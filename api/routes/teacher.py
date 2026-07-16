import token

from fastapi import APIRouter, HTTPException

from core.auth import create_access_token
from core.schemas import TeacherLoginRequest, TeacherLoginResponse
from database.db import teacher_login,create_teacher

router = APIRouter()



@router.post("/teacher/register")
async def register_teacher(
    payload: TeacherLoginRequest
):

    teacher = create_teacher(
        payload.email,
        payload.password,
        payload.name
    )

    if not teacher:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    token, expires_at = create_access_token(
    user_id=teacher["teacher_id"],
    role="teacher",
    name=teacher["name"]
)

    return {
        "success": True,
        "token":token,
        "expiresAt": expires_at,
        "teacher": {
            "id": teacher["teacher_id"],
            "name": teacher["name"],
            "email": teacher["email"],
            "role": "teacher"
    }
    }


@router.post("/teacher/login")
async def login_teacher(
    payload: TeacherLoginResponse
):

    teacher = teacher_login(
        payload.email,
        payload.password
    )

    if not teacher:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token, expires_at = create_access_token(
    user_id=teacher["teacher_id"],
    role="teacher",
    name=teacher["name"]
)

    return {
        "success": True,
        "token":token,
        "expiresAt": expires_at,
        "teacher": {
            "id": teacher["teacher_id"],
            "name": teacher["name"],
            "email": teacher["email"],
            "role": "teacher"
    }
}

