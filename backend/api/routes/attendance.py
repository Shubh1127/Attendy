from fastapi import APIRouter, Header, HTTPException,Query

from core.auth import get_user_from_token
from core.schemas import CreateAttendanceSessionRequest
from core.schemas import UpdateAttendanceSessionRequest
from database.config import supabase
from datetime import datetime, timezone

router = APIRouter()


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
    authorization: str = Header(...),
    subjectId: int | None = Query(default=None)
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
        .select("""
            session_id,
            status,
            opened_at,
            closed_at,
            subjects(
                subject_id,
                name,
                subject_code
            )
        """)
        .eq("teacher_id", teacher["id"])
    )

    if subjectId:
        query = query.eq("subject_id", subjectId)

    response = (
        query
        .order("opened_at", desc=True)
        .execute()
    )

    return {
        "success": True,
        "sessions": response.data
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
        supabase
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

    # -------------------------
    # GET ATTENDANCE ENTRIES
    # -------------------------

    logs = (
        supabase
        .table("attendance_logs")
        .select("""
            student_id,
            status,
            method,
            confidence,
            marked_at,
            student(
                id,
                name,
                enrollment_number
            )
        """)
        .eq("session_id", session_id)
        .order("student_id")
        .execute()
    )

    return {
        "success": True,
        "session": session_data,
        "entries": logs.data
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
                student(
                    id,
                    name,
                    enrollment_number
                )
            """)
            .eq("session_id", session_id)
            .order("student_id")
            .execute()
        )

        return {
            "success": True,
            "entries": entries.data
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
                student(
                    id,
                    name,
                    enrollment_number
                )
            """)
            .eq("session_id", session_id)
            .eq("student_id", user["id"])
            .execute()
        )

        return {
            "success": True,
            "entries": entry.data
        }

    raise HTTPException(
        status_code=403,
        detail="Invalid role"
    )