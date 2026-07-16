

from fastapi import APIRouter, Header, HTTPException, Query, UploadFile, File

from PIL import Image
from io import BytesIO
import numpy as np

from core.auth import get_user_from_token
from core.schemas import CreateAttendanceSessionRequest
from core.schemas import UpdateAttendanceSessionRequest
from database.config import admin_supabase, supabase
from datetime import datetime, timedelta, timezone

from pipelines.face_pipeline import get_face_embeddings

router = APIRouter()

ATTENDANCE_PRESENT_WINDOW = timedelta(minutes=10)
ATTENDANCE_SESSION_DURATION = timedelta(hours=1)


def _attach_students(entries: list[dict]):
    student_ids = {
        entry["student_id"]
        for entry in entries
        if entry.get("student_id") is not None
    }

    students_by_id = {}

    if student_ids:
        students_response = (
            supabase
            .table("student")
            .select("student_id, name, enrollment_number")
            .in_("student_id", list(student_ids))
            .execute()
        )

        students_by_id = {
            student["student_id"]: student
            for student in students_response.data
        }

    return [
        {
            **entry,
            "student": students_by_id.get(entry["student_id"]),
        }
        for entry in entries
    ]


def _parse_iso_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _auto_close_expired_session(session_row: dict):
    if session_row.get("status") != "open" or not session_row.get("opened_at"):
        return session_row

    opened_at = _parse_iso_datetime(session_row["opened_at"])
    now = datetime.now(timezone.utc)

    if now <= opened_at + ATTENDANCE_SESSION_DURATION:
        return session_row

    updated_session = (
        admin_supabase
        .table("attendance_sessions")
        .update({
            "status": "closed",
            "closed_at": now.isoformat()
        })
        .eq("session_id", session_row["session_id"])
        .eq("status", "open")
        .execute()
    )

    if updated_session.data:
        return updated_session.data[0]

    return {
        **session_row,
        "status": "closed",
        "closed_at": now.isoformat()
    }


@router.post("/attendance/sessions")
async def create_attendance_session(
    payload: CreateAttendanceSessionRequest,
    authorization: str = Header(...)
):

    # -------------------------
    # VERIFY TOKEN
    # -------------------------

    token = authorization.replace(
        "Bearer ",
        ""
    )

    teacher = get_user_from_token(token)

    if not teacher:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    if teacher["role"] != "teacher":
        raise HTTPException(
            status_code=403,
            detail="Teachers only"
        )

    # -------------------------
    # VERIFY SUBJECT
    # -------------------------

    subject = (
        supabase
        .table("subjects")
        .select("*")
        .eq("subject_id", payload.subjectId)
        .eq("teacher_id", teacher["id"])
        .execute()
    )

    if not subject.data:
        raise HTTPException(
            status_code=404,
            detail="Subject not found"
        )

    subject_data = subject.data[0]

    # -------------------------
    # CHECK OPEN SESSION
    # -------------------------

    existing = (
        supabase
        .table("attendance_sessions")
        .select("*")
        .eq("subject_id", payload.subjectId)
        .eq("status", "open")
        .execute()
    )

    if existing.data:
        raise HTTPException(
            status_code=400,
            detail="Attendance session already open"
        )

    # -------------------------
    # CREATE SESSION
    # -------------------------

    session = (
        supabase
        .table("attendance_sessions")
        .insert({
            "subject_id": payload.subjectId,
            "teacher_id": teacher["id"],
            "status": "open"
        })
        .execute()
    )

    session_data = session.data[0]

    # -------------------------
    # GET ENROLLED STUDENTS
    # -------------------------

    students = (
        supabase
        .table("subjects_student")
        .select("student_id")
        .eq("subject_id", payload.subjectId)
        .execute()
    )

    # -------------------------
    # CREATE PENDING ENTRIES
    # -------------------------

    logs = []

    for student in students.data:

        logs.append({
            "session_id": session_data["session_id"],
            "student_id": student["student_id"],
            "subject_id": payload.subjectId,
            "status": "pending"
        })

    if logs:

        supabase.table(
            "attendance_logs"
        ).insert(
            logs
        ).execute()

    return {
        "success": True,
        "message": "Attendance session created",
        "session": session_data
    }






@router.get("/attendance/sessions")
async def get_attendance_sessions(
    subjectId: int | None = Query(default=None),
    authorization: str = Header(...)
):
    # -------------------------
    # VERIFY TOKEN
    # -------------------------

    token = authorization.replace(
        "Bearer ",
        ""
    )

    teacher = get_user_from_token(token)

    if not teacher:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    if teacher["role"] != "teacher":
        raise HTTPException(
            status_code=403,
            detail="Teachers only"
        )

    # -------------------------
    # GET SESSIONS
    # -------------------------

    query = (
        supabase
        .table("attendance_sessions")
        .select("session_id, subject_id, teacher_id, status, opened_at, closed_at")
        .eq("teacher_id", teacher["id"])
        .eq("status", "closed")
    )

    if subjectId:
        query = query.eq("subject_id", subjectId)

    response = (
        query
        .order("opened_at", desc=True)
        .execute()
    )

    subject_ids = {
        session["subject_id"]
        for session in response.data
        if session.get("subject_id") is not None
    }

    subjects_by_id = {}

    if subject_ids:
        subjects_response = (
            supabase
            .table("subjects")
            .select("subject_id, name")
            .in_("subject_id", list(subject_ids))
            .execute()
        )

        subjects_by_id = {
            subject["subject_id"]: subject["name"]
            for subject in subjects_response.data
        }

    sessions = [
        {
            **session,
            "subject_name": subjects_by_id.get(session["subject_id"]),
        }
        for session in response.data
    ]

    return {
        "success": True,
        "sessions": sessions
    }


@router.get("/attendance/sessions/active")
async def get_teacher_active_attendance_sessions(
    authorization: str = Header(...)
):
    token = authorization.replace(
        "Bearer ",
        ""
    )

    teacher = get_user_from_token(token)

    if not teacher:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    if teacher["role"] != "teacher":
        raise HTTPException(
            status_code=403,
            detail="Teachers only"
        )

    sessions_response = (
        admin_supabase
        .table("attendance_sessions")
        .select("session_id, subject_id, teacher_id, status, opened_at, closed_at")
        .eq("teacher_id", teacher["id"])
        .eq("status", "open")
        .order("opened_at", desc=True)
        .execute()
    )

    open_sessions = []

    for session_row in sessions_response.data:
        refreshed_session = _auto_close_expired_session(session_row)
        if refreshed_session.get("status") == "open":
            open_sessions.append(refreshed_session)

    if not open_sessions:
        return {
            "success": True,
            "sessions": []
        }

    subject_ids = {
        session["subject_id"]
        for session in open_sessions
        if session.get("subject_id") is not None
    }

    subjects_by_id = {}

    if subject_ids:
        subjects_response = (
            admin_supabase
            .table("subjects")
            .select("subject_id, subject_code, name, section")
            .in_("subject_id", list(subject_ids))
            .execute()
        )

        subjects_by_id = {
            subject["subject_id"]: subject
            for subject in subjects_response.data
        }

    session_ids = [session["session_id"] for session in open_sessions]

    logs_response = (
        admin_supabase
        .table("attendance_logs")
        .select("session_id, status")
        .in_("session_id", session_ids)
        .execute()
    )

    stats_by_session = {
        session_id: {
            "total_students": 0,
            "checked_in_count": 0,
        }
        for session_id in session_ids
    }

    for log in logs_response.data:
        session_id = log["session_id"]
        stats = stats_by_session.setdefault(
            session_id,
            {"total_students": 0, "checked_in_count": 0},
        )
        stats["total_students"] += 1
        if log.get("status") in {"present", "late", "excused"}:
            stats["checked_in_count"] += 1

    sessions = []

    for session_row in open_sessions:
        subject_row = subjects_by_id.get(session_row["subject_id"])
        stats = stats_by_session.get(
            session_row["session_id"],
            {"total_students": 0, "checked_in_count": 0},
        )

        sessions.append({
            **session_row,
            "subject_name": subject_row["name"] if subject_row else None,
            "subject_code": subject_row["subject_code"] if subject_row else None,
            "section": subject_row["section"] if subject_row else None,
            "checked_in_count": stats["checked_in_count"],
            "total_students": stats["total_students"],
        })

    return {
        "success": True,
        "sessions": sessions
    }




@router.get("/attendance/sessions/{session_id}")
async def get_attendance_session(
    session_id: int,
    authorization: str = Header(...)
):

    # -------------------------
    # VERIFY TOKEN
    # -------------------------

    token = authorization.replace(
        "Bearer ",
        ""
    )

    teacher = get_user_from_token(token)

    if not teacher:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    if teacher["role"] != "teacher":
        raise HTTPException(
            status_code=403,
            detail="Teachers only"
        )

    # -------------------------
    # VERIFY SESSION
    # -------------------------

    session = (
    admin_supabase
    .table("attendance_sessions")
    .select("""
        *,
        subjects(
            subject_id,
            subject_code,
            name,
            section
        )
    """)
    .eq("session_id", session_id)
    .eq("teacher_id", teacher["id"])
    .execute()
)

    if not session.data:
        raise HTTPException(
            status_code=404,
            detail="Attendance session not found"
        )

    session_data = session.data[0]

    session_data = _auto_close_expired_session(session_data)

    # -------------------------
    # GET ATTENDANCE ENTRIES
    # -------------------------

    logs = (
    admin_supabase
    .table("attendance_logs")
    .select("""
        student_id,
        status,
        method,
        confidence,
        marked_at
    """)
    .eq("session_id", session_id)
    .order("student_id")
    .execute()
)

    logs_data = _attach_students(logs.data)

    return {
        "success": True,
        "session": session_data,
        "entries": logs_data
    }





@router.patch("/attendance/sessions/{session_id}")
async def update_attendance_session(
    session_id: int,
    payload: UpdateAttendanceSessionRequest,
    authorization: str = Header(...)
):

    # --------------------------------
    # VERIFY TOKEN
    # --------------------------------

    token = authorization.replace(
        "Bearer ",
        ""
    )

    teacher = get_user_from_token(token)

    if not teacher:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    if teacher["role"] != "teacher":
        raise HTTPException(
            status_code=403,
            detail="Teachers only"
        )

    # --------------------------------
    # VERIFY SESSION
    # --------------------------------

    session = (
        supabase
        .table("attendance_sessions")
        .select("*")
        .eq("session_id", session_id)
        .eq("teacher_id", teacher["id"])
        .execute()
    )

    if not session.data:
        raise HTTPException(
            status_code=404,
            detail="Attendance session not found"
        )

    session_data = session.data[0]

    if session_data["status"] == "closed":
        raise HTTPException(
            status_code=400,
            detail="Attendance session already closed"
        )

    # --------------------------------
    # UPDATE ATTENDANCE LOGS
    # --------------------------------

    for entry in payload.entries:

        (
            supabase
            .table("attendance_logs")
            .update({
                "status": entry.status
            })
            .eq("session_id", session_id)
            .eq("student_id", entry.studentId)
            .execute()
        )

    # --------------------------------
    # CLOSE SESSION
    # --------------------------------

    updated_session = (
        supabase
        .table("attendance_sessions")
        .update({
            "status": "closed",
            "closed_at": datetime.now(timezone.utc).isoformat()
        })
        .eq("session_id", session_id)
        .execute()
    )

    return {
        "success": True,
        "message": "Attendance session closed successfully",
        "session": updated_session.data[0]
    }





@router.get("/attendance/sessions/{session_id}/entries")
async def get_attendance_entries(
    session_id: int,
    authorization: str = Header(...)
):

    # -------------------------
    # VERIFY TOKEN
    # -------------------------

    token = authorization.replace("Bearer ", "")

    user = get_user_from_token(token)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    # -------------------------
    # VERIFY SESSION EXISTS
    # -------------------------

    session = (
        supabase
        .table("attendance_sessions")
        .select("*")
        .eq("session_id", session_id)
        .execute()
    )

    if not session.data:
        raise HTTPException(
            status_code=404,
            detail="Attendance session not found"
        )

    session_data = session.data[0]

    # -------------------------
    # TEACHER
    # -------------------------

    if user["role"] == "teacher":

        if session_data["teacher_id"] != user["id"]:
            raise HTTPException(
                status_code=403,
                detail="Unauthorized"
            )

        entries = (
            supabase
            .table("attendance_logs")
            .select("""
                *,
            """)
            .eq("session_id", session_id)
            .order("student_id")
            .execute()
        )

        entries_data = _attach_students(entries.data)

        return {
            "success": True,
            "entries": entries_data
        }

    # -------------------------
    # STUDENT
    # -------------------------

    if user["role"] == "student":

        entry = (
            supabase
            .table("attendance_logs")
            .select("""
                *,
            """)
            .eq("session_id", session_id)
            .eq("student_id", user["id"])
            .execute()
        )

        entries_data = _attach_students(entry.data)

        return {
            "success": True,
            "entries": entries_data
        }

    raise HTTPException(
        status_code=403,
        detail="Invalid role"
    )

@router.get("/student/attendance")
async def get_student_attendance(
    authorization: str = Header(...)
):

    token = authorization.replace(
        "Bearer ",
        ""
    )

    student = get_user_from_token(token)

    if not student:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    if student["role"] != "student":
        raise HTTPException(
            status_code=403,
            detail="Students only"
        )

    response = (
        supabase
        .table("attendance_logs")
        .select("""
            subject_id,
            status,
            subjects(
                subject_code,
                name
            )
        """)
        .eq("student_id", student["id"])
        .execute()
    )

    summary = {}

    for row in response.data:

        subject_id = row["subject_id"]

        if subject_id not in summary:

            summary[subject_id] = {
                "subject_id": subject_id,
                "subject_name": row["subjects"]["name"],
                "subject_code": row["subjects"]["subject_code"],
                "total": 0,
                "present": 0,
                "late": 0,
                "absent": 0
            }

        summary[subject_id]["total"] += 1

        if row["status"] == "present":
            summary[subject_id]["present"] += 1

        elif row["status"] == "late":
            summary[subject_id]["late"] += 1

        elif row["status"] == "absent":
            summary[subject_id]["absent"] += 1

    attendance = []

    for item in summary.values():

        item["percentage"] = round(
            (
                item["present"] +
                item["late"]
            )
            /
            item["total"]
            *
            100,
            2
        )

        attendance.append(item)

    return {
        "success": True,
        "attendance": attendance
    }


@router.get("/student/attendance/active")
async def get_student_active_attendance(
    authorization: str = Header(...)
):

    token = authorization.replace(
        "Bearer ",
        ""
    )

    student = get_user_from_token(token)

    if not student:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    if student["role"] != "student":
        raise HTTPException(
            status_code=403,
            detail="Students only"
        )

    enrolled_subjects = (
        admin_supabase
        .table("subjects_student")
        .select("subject_id")
        .eq("student_id", student["id"])
        .execute()
    )

    subject_ids = [row["subject_id"] for row in enrolled_subjects.data]

    if not subject_ids:
        return {
            "success": True,
            "sessions": []
        }

    sessions_response = (
        admin_supabase
        .table("attendance_sessions")
        .select("session_id, subject_id, opened_at, closed_at, status")
        .eq("status", "open")
        .in_("subject_id", subject_ids)
        .order("opened_at", desc=True)
        .execute()
    )

    sessions = []

    for session_row in sessions_response.data:
        refreshed_session = _auto_close_expired_session(session_row)
        if refreshed_session.get("status") == "open":
            sessions.append(refreshed_session)

    if not sessions:
        return {
            "success": True,
            "sessions": []
        }

    subject_lookup_response = (
        admin_supabase
        .table("subjects")
        .select("subject_id, subject_code, name, section")
        .in_("subject_id", [row["subject_id"] for row in sessions])
        .execute()
    )

    subject_by_id = {
        row["subject_id"]: row
        for row in subject_lookup_response.data
    }

    mark_response = (
        admin_supabase
        .table("attendance_logs")
        .select("session_id, status, marked_at")
        .eq("student_id", student["id"])
        .in_("session_id", [row["session_id"] for row in sessions])
        .execute()
    )

    mark_by_session = {
        row["session_id"]: row
        for row in mark_response.data
    }

    active_sessions = []

    for session_row in sessions:
        subject_row = subject_by_id.get(session_row["subject_id"])
        mark_row = mark_by_session.get(session_row["session_id"])

        active_sessions.append({
            **session_row,
            "subject_name": subject_row["name"] if subject_row else None,
            "subject_code": subject_row["subject_code"] if subject_row else None,
            "section": subject_row["section"] if subject_row else None,
            "marked": bool(mark_row and mark_row.get("status") in {"present", "late", "excused"}),
            "mark_status": mark_row["status"] if mark_row else None,
            "marked_at": mark_row["marked_at"] if mark_row else None,
        })

    return {
        "success": True,
        "sessions": active_sessions
    }


@router.get("/student/subjects/{subject_id}/attendance-sessions")
async def get_student_subject_attendance_sessions(
    subject_id: int,
    authorization: str = Header(...)
):

    token = authorization.replace(
        "Bearer ",
        ""
    )

    student = get_user_from_token(token)

    if not student:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    if student["role"] != "student":
        raise HTTPException(
            status_code=403,
            detail="Students only"
        )

    enrolled = (
        admin_supabase
        .table("subjects_student")
        .select("student_id")
        .eq("subject_id", subject_id)
        .eq("student_id", student["id"])
        .execute()
    )

    if not enrolled.data:
        raise HTTPException(
            status_code=403,
            detail="You are not enrolled in this subject"
        )

    subject_response = (
        admin_supabase
        .table("subjects")
        .select("subject_id, subject_code, name, section")
        .eq("subject_id", subject_id)
        .execute()
    )

    if not subject_response.data:
        raise HTTPException(
            status_code=404,
            detail="Subject not found"
        )

    subject_data = subject_response.data[0]

    sessions_response = (
        admin_supabase
        .table("attendance_sessions")
        .select("session_id, subject_id, opened_at, closed_at, status")
        .eq("subject_id", subject_id)
        .eq("status", "closed")
        .order("opened_at", desc=True)
        .execute()
    )

    sessions = sessions_response.data

    if not sessions:
        return {
            "success": True,
            "subject": subject_data,
            "sessions": []
        }

    logs_response = (
        admin_supabase
        .table("attendance_logs")
        .select("session_id, status, marked_at")
        .eq("student_id", student["id"])
        .in_("session_id", [row["session_id"] for row in sessions])
        .execute()
    )

    log_by_session = {
        row["session_id"]: row
        for row in logs_response.data
    }

    result_sessions = []

    for session_row in sessions:
        log_row = log_by_session.get(session_row["session_id"])

        result_sessions.append({
            **session_row,
            "subject_code": subject_data["subject_code"],
            "subject_name": subject_data["name"],
            "section": subject_data["section"],
            "marked": bool(log_row and log_row.get("status") in {"present", "late", "excused"}),
            "mark_status": log_row["status"] if log_row else None,
            "marked_at": log_row["marked_at"] if log_row else None,
        })

    return {
        "success": True,
        "subject": subject_data,
        "sessions": result_sessions
    }


@router.get("/student/attendance-sessions")
async def get_student_attendance_sessions(
    authorization: str = Header(...)
):

    # -------------------------
    # VERIFY TOKEN
    # -------------------------

    token = authorization.replace("Bearer ", "")

    student = get_user_from_token(token)

    if not student:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    if student["role"] != "student":
        raise HTTPException(
            status_code=403,
            detail="Students only"
        )

    # -------------------------
    # GET ENROLLED SUBJECTS
    # -------------------------

    enrolled = (
        admin_supabase
        .table("subjects_student")
        .select("subject_id")
        .eq("student_id", student["id"])
        .execute()
    )

    if not enrolled.data:
        return {
            "success": True,
            "sessions": []
        }

    subject_ids = [
        row["subject_id"]
        for row in enrolled.data
    ]

    # -------------------------
    # GET SUBJECT DETAILS
    # -------------------------

    subjects = (
        admin_supabase
        .table("subjects")
        .select("subject_id, subject_code, name, section")
        .in_("subject_id", subject_ids)
        .execute()
    )

    subject_map = {
        row["subject_id"]: row
        for row in subjects.data
    }

    # -------------------------
    # GET CLOSED SESSIONS
    # -------------------------

    sessions = (
        admin_supabase
        .table("attendance_sessions")
        .select(
            "session_id, subject_id, opened_at, closed_at, status"
        )
        .in_("subject_id", subject_ids)
        .eq("status", "closed")
        .order("opened_at", desc=True)
        .execute()
    )

    if not sessions.data:
        return {
            "success": True,
            "sessions": []
        }

    session_ids = [
        row["session_id"]
        for row in sessions.data
    ]

    # -------------------------
    # GET STUDENT LOGS
    # -------------------------

    logs = (
        admin_supabase
        .table("attendance_logs")
        .select(
            "session_id, status, marked_at"
        )
        .eq("student_id", student["id"])
        .in_("session_id", session_ids)
        .execute()
    )

    log_map = {
        row["session_id"]: row
        for row in logs.data
    }

    # -------------------------
    # BUILD RESPONSE
    # -------------------------

    result = []

    for session in sessions.data:

        subject = subject_map.get(
            session["subject_id"],
            {}
        )

        log = log_map.get(
            session["session_id"]
        )

        result.append({

            "session_id": session["session_id"],

            "subject_id": session["subject_id"],

            "subject_code": subject.get("subject_code"),

            "subject_name": subject.get("name"),

            "section": subject.get("section"),

            "opened_at": session["opened_at"],

            "closed_at": session["closed_at"],

            "status": session["status"],

            "marked": bool(
                log and log["status"] in {
                    "present",
                    "late",
                    "excused"
                }
            ),

            "mark_status": (
                log["status"]
                if log
                else "absent"
            ),

            "marked_at": (
                log["marked_at"]
                if log
                else None
            )

        })

    return {
        "success": True,
        "sessions": result
    }


@router.post("/student/attendance/{session_id}/check-in")
async def check_in_student_attendance(
    session_id: int,
    faceImage: UploadFile = File(...),
    authorization: str = Header(...)
):

    token = authorization.replace(
        "Bearer ",
        ""
    )

    student = get_user_from_token(token)

    if not student:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    if student["role"] != "student":
        raise HTTPException(
            status_code=403,
            detail="Students only"
        )

    session_response = (
        admin_supabase
        .table("attendance_sessions")
        .select("session_id, subject_id, opened_at, closed_at, status")
        .eq("session_id", session_id)
        .execute()
    )

    if not session_response.data:
        raise HTTPException(
            status_code=404,
            detail="Attendance session not found"
        )

    session_data = session_response.data[0]

    session_data = _auto_close_expired_session(session_data)

    if session_data["status"] != "open":
        raise HTTPException(
            status_code=400,
            detail="Attendance session has ended"
        )

    subject_response = (
        admin_supabase
        .table("subjects")
        .select("subject_id, subject_code, name, section")
        .eq("subject_id", session_data["subject_id"])
        .execute()
    )

    subject_data = subject_response.data[0] if subject_response.data else None

    opened_at = _parse_iso_datetime(session_data["opened_at"])
    now = datetime.now(timezone.utc)

    if now > opened_at + ATTENDANCE_SESSION_DURATION:
        _auto_close_expired_session(session_data)
        raise HTTPException(
            status_code=400,
            detail="Attendance session has ended"
        )

    enrolled = (
        admin_supabase
        .table("subjects_student")
        .select("student_id")
        .eq("subject_id", session_data["subject_id"])
        .eq("student_id", student["id"])
        .execute()
    )

    if not enrolled.data:
        raise HTTPException(
            status_code=403,
            detail="You are not enrolled in this subject"
        )

    student_response = (
        admin_supabase
        .table("student")
        .select("student_id, name, face_embedding")
        .eq("student_id", student["id"])
        .execute()
    )

    if not student_response.data:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    student_row = student_response.data[0]

    if not student_row.get("face_embedding"):
        raise HTTPException(
            status_code=400,
            detail="Face not registered for this student"
        )

    image_bytes = await faceImage.read()
    image_np = np.array(
        Image.open(
            BytesIO(image_bytes)
        ).convert("RGB")
    )

    encodings = get_face_embeddings(image_np)

    if len(encodings) == 0:
        raise HTTPException(
            status_code=400,
            detail="No face detected"
        )

    if len(encodings) > 1:
        raise HTTPException(
            status_code=400,
            detail="Multiple faces detected"
        )

    current_face_embedding = encodings[0]
    stored_face_embedding = np.array(student_row["face_embedding"])
    distance = np.linalg.norm(stored_face_embedding - current_face_embedding)

    if distance > 0.6:
        raise HTTPException(
            status_code=401,
            detail="Face not recognized"
        )

    marked_at = now.isoformat()
    mark_status = "present" if now <= opened_at + ATTENDANCE_PRESENT_WINDOW else "late"

    update_response = (
        admin_supabase
        .table("attendance_logs")
        .update({
            "status": mark_status,
            "method": "face",
            "confidence": round(max(0.0, 1.0 - float(distance)), 4),
            "marked_at": marked_at
        })
        .eq("session_id", session_id)
        .eq("student_id", student["id"])
        .execute()
    )

    if not update_response.data:
        raise HTTPException(
            status_code=404,
            detail="Attendance entry not found"
        )

    return {
        "success": True,
        "message": "Attendance marked successfully",
        "entry": update_response.data[0],
        "session": {
            **session_data,
            "subject_name": subject_data["name"] if subject_data else None,
            "subject_code": subject_data["subject_code"] if subject_data else None,
            "section": subject_data["section"] if subject_data else None
        }
    }

from fastapi import APIRouter, Header, HTTPException
from collections import defaultdict

@router.get("/student/overall-attendance")
async def get_student_overall_attendance(
    authorization: str = Header(...)
):
    token = authorization.replace("Bearer ", "")

    student = get_user_from_token(token)

    if not student:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    if student["role"] != "student":
        raise HTTPException(
            status_code=403,
            detail="Students only"
        )

    # Get all attendance logs for this student
    attendance_response = (
        admin_supabase
        .table("attendance_logs")
        .select("subject_id, status")
        .eq("student_id", student["id"])
        .execute()
    )

    logs = attendance_response.data

    # Get all subjects
    subjects_response = (
        admin_supabase
        .table("subjects")
        .select("subject_id, name")
        .execute()
    )

    subject_names = {
        subject["subject_id"]: subject["name"]
        for subject in subjects_response.data
    }

    # Calculate subject-wise stats
    subject_stats = defaultdict(lambda: {
        "total_sessions": 0,
        "present": 0,
        "late": 0,
        "absent": 0
    })

    for log in logs:
        subject_id = log["subject_id"]

        subject_stats[subject_id]["total_sessions"] += 1

        if log["status"] == "present":
            subject_stats[subject_id]["present"] += 1

        elif log["status"] == "late":
            subject_stats[subject_id]["late"] += 1

        else:
            subject_stats[subject_id]["absent"] += 1

    overall_total_sessions = 0
    overall_attended_sessions = 0
    overall_present = 0
    overall_late = 0
    overall_absent = 0

    subjects = []
    needs_attention = []

    for subject_id, stats in subject_stats.items():

        attended_sessions = (
            stats["present"] +
            stats["late"]
        )

        percentage = (
            attended_sessions / stats["total_sessions"] * 100
            if stats["total_sessions"] > 0
            else 0
        )

        overall_total_sessions += stats["total_sessions"]
        overall_attended_sessions += attended_sessions
        overall_present += stats["present"]
        overall_late += stats["late"]
        overall_absent += stats["absent"]

        subject_data = {
            "subject_id": subject_id,
            "subject_name": subject_names.get(subject_id, "Unknown Subject"),
            "attendance_percentage": round(percentage, 2),
            "total_sessions": stats["total_sessions"],
            "attended_sessions": attended_sessions,
            "present": stats["present"],
            "late": stats["late"],
            "absent": stats["absent"]
        }

        subjects.append(subject_data)

        if percentage < 40:
            needs_attention.append(subject_data)

    overall_percentage = (
        overall_attended_sessions / overall_total_sessions * 100
        if overall_total_sessions > 0
        else 0
    )

    return {
        "success": True,
        "overall": {
            "attendance_percentage": round(overall_percentage, 2),
            "total_sessions": overall_total_sessions,
            "attended_sessions": overall_attended_sessions,
            "present": overall_present,
            "late": overall_late,
            "absent": overall_absent
        },
        "subjects": subjects,
        "needs_attention": needs_attention
    }