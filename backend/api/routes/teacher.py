from fastapi import APIRouter, HTTPException

from core.auth import create_access_token
from core.schemas import TeacherLoginRequest
from database.db import teacher_login,create_teacher

router = APIRouter()



@router.post("/teacher/register")
async def register_teacher(
    payload: TeacherLoginRequest
):

    teacher = create_teacher(
        payload.username,
        payload.password,
        payload.name
    )

    if not teacher:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    token = create_access_token(
        user_id=teacher["teacher_id"],
        role="teacher",
        name=teacher["name"]
    )

    return {
        "success": True,
        "token": token,
        "teacher": {
            "id": teacher["teacher_id"],
            "name": teacher["name"],
            "username": teacher["username"]
        }
    }


@router.post("/teacher/login")
async def login_teacher(
    payload: TeacherLoginRequest
):

    teacher = teacher_login(
        payload.username,
        payload.password
    )

    if not teacher:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    token = create_access_token(
        user_id=teacher["teacher_id"],
        role="teacher",
        name=teacher["name"]
    )

    return {
        "success": True,
        "token": token,
        "teacher": {
            "id": teacher["teacher_id"],
            "name": teacher["name"],
            "username": teacher["username"]
        }
    }