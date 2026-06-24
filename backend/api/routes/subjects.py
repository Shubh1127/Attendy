from fastapi import APIRouter,HTTPException, Header
from database.config import supabase
from core.schemas import CreateSubjectRequest, JoinSubjectRequest
from auth import get_user_from_token
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