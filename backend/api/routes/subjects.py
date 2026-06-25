from fastapi import APIRouter,HTTPException, Header
from database.config import supabase
from core.schemas import CreateSubjectRequest, JoinSubjectRequest
from core.auth import get_user_from_token
router = APIRouter()



@router.post("/subjects/create")
async def create_subject(
    payload: CreateSubjectRequest,
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

    subject = (
        supabase
        .table("subjects")
        .select("*")
        .eq("subject_code", payload.subject_code)
        .execute()
    )

    if subject.data:
        raise HTTPException(
            status_code=400,
            detail="Subject code already exists"
        )

    response = (
        supabase
        .table("subjects")
        .insert({
            "subject_code": payload.subject_code,
            "name": payload.name,
            "section": payload.section,
            "teacher_id": teacher["id"]
        })
        .execute()
    )

    return {
        "success": True,
        "message": "Subject created successfully",
        "subject": response.data[0]
    }



@router.post("/subjects/join")
async def join_subject(
    payload: JoinSubjectRequest,
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

    student_id = student["id"]

    # Find subject
    subject = (
        supabase
        .table("subjects")
        .select("*")
        .eq("subject_code", payload.code)
        .execute()
    )

    if not subject.data:
        raise HTTPException(
            status_code=404,
            detail="Subject not found"
        )

    subject_data = subject.data[0]

    # Check already enrolled
    enrollment = (
        supabase
        .table("subjects_student")
        .select("*")
        .eq("student_id", student_id)
        .eq("subject_id", subject_data["subject_id"])
        .execute()
    )

    if enrollment.data:
        raise HTTPException(
            status_code=400,
            detail="Already enrolled"
        )

    # Create enrollment
    enrollment_response = (
        supabase
        .table("subjects_student")
        .insert({
            "student_id": student_id,
            "subject_id": subject_data["subject_id"]
        })
        .execute()
    )

    return {
        "success": True,
        "message": "Joined subject successfully",
        "subject": subject_data,
        "enrollment": enrollment_response.data[0]
    }

@router.get("/subjects/{subject_id}")
async def get_subject(
    subject_id: int,
    authorization: str = Header(...)
):

    token = authorization.replace(
        "Bearer ",
        ""
    )

    user = get_user_from_token(token)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    # Get Subject
    subject_response = (
        supabase
        .table("subjects")
        .select("*")
        .eq("subject_id", subject_id)
        .execute()
    )

    if not subject_response.data:
        raise HTTPException(
            status_code=404,
            detail="Subject not found"
        )

    subject = subject_response.data[0]

    # Get enrolled students
    students_response = (
        supabase
        .table("subjects_student")
        .select("*")
        .eq("subject_id", subject_id)
        .execute()
    )

    students = students_response.data
    student_count = len(students)

    # Get attendance logs
    attendance_response = (
        supabase
        .table("attendance_logs")
        .select("*")
        .eq("subject_id", subject_id)
        .execute()
    )

    attendance_logs = attendance_response.data

    # Attendance Rate
    attendance_rate = 0

    if student_count > 0:

        total_classes = len(
            set(
                log["created_at"]
                for log in attendance_logs
            )
        )

        if total_classes > 0:

            total_present = len(attendance_logs)

            max_possible = (
                student_count *
                total_classes
            )

            attendance_rate = round(
                (total_present / max_possible) * 100,
                2
            )

    return {
        "subject_id": subject["subject_id"],
        "subject_code": subject["subject_code"],
        "name": subject["name"],
        "section": subject["section"],
        "teacher_id": subject["teacher_id"],
        "studentCount": student_count,
        "attendanceRate": attendance_rate
    }




@router.get("/subjects")
async def get_subjects(
    authorization: str = Header(...)
):

    token = authorization.replace(
        "Bearer ",
        ""
    )

    user = get_user_from_token(token)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    # =========================
    # TEACHER SUBJECTS
    # =========================

    if user["role"] == "teacher":

        response = (
            supabase
            .table("subjects")
            .select("*")
            .eq("teacher_id", user["id"])
            .execute()
        )

        return {
            "success": True,
            "subjects": response.data
        }

    # =========================
    # STUDENT SUBJECTS
    # =========================

    if user["role"] == "student":

        response = (
            supabase
            .table("subjects_student")
            .select("subjects(*)")
            .eq("student_id", user["id"])
            .execute()
        )

        subjects = [
            row["subjects"]
            for row in response.data
            if row.get("subjects")
        ]

        return {
            "success": True,
            "subjects": subjects
        }

    raise HTTPException(
        status_code=403,
        detail="Invalid role"
    )