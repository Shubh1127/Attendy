

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Header

from PIL import Image
from io import BytesIO
import numpy as np

from core.auth import create_access_token
from database.config import supabase
from pipelines.face_pipeline import get_face_embeddings
from pipelines.voice_pipeline import get_voice_embedding

from core.auth import get_user_from_token

router = APIRouter()






    

    
   

    

    

@router.post("/student/verify")
async def verify_student(
    enrollmentNumber: str = Form(...),
    faceImage: UploadFile = File(...),
    voiceAudio: UploadFile | None = File(default=None)
):

    # -------------------------------
    # CHECK STUDENT EXISTS
    # -------------------------------

    response = (
        supabase
        .table("student")
        .select("*")
        .eq("enrollment_number", enrollmentNumber)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="Enrollment number not found"
        )

    student = response.data[0]

    # -------------------------------
    # GENERATE FACE EMBEDDING
    # -------------------------------

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

    # =====================================================
    # LOGIN FLOW
    # =====================================================

    if student["is_registered"]:

        stored_face_embedding = np.array(
            student["face_embedding"]
        )

        distance = np.linalg.norm(
            stored_face_embedding -
            current_face_embedding
        )

        FACE_THRESHOLD = 0.6

        if distance > FACE_THRESHOLD:
            raise HTTPException(
                status_code=401,
                detail="Face not recognized"
            )
        
        token, expires_at = create_access_token(
            user_id=student["student_id"],
            role="student",
            name=student["name"]
        )

        return {
            "action": "login",
            "matched": True,
            "token": token,
            "expiresAt": expires_at,
            "student_id": student["student_id"],
            "student_name": student["name"]
        }

    # =====================================================
# REGISTRATION FLOW
# =====================================================

    if voiceAudio is None:
         return {
            "action": "voice_required",
            "matched": False,
            "message": "Voice enrollment required."
        }

    audio_bytes = await voiceAudio.read()

    voice_embedding = get_voice_embedding(
        audio_bytes
    )

    if voice_embedding is None:
        raise HTTPException(
            status_code=400,
            detail="Voice embedding generation failed"
        )

    face_embedding = current_face_embedding.tolist()

    (
        supabase
        .table("student")
        .update({
            "face_embedding": face_embedding,
            "voice_embedding": voice_embedding,
            "is_registered": True
        })
        .eq(
            "enrollment_number",
            enrollmentNumber
        )
        .execute()
    )

    token, expires_at = create_access_token(
        user_id=student["student_id"],
        role="student",
        name=student["name"]
    )

    return {
        "action": "register",
        "registered": True,
        "token": token,
        "expiresAt": expires_at,
        "student_id": student["student_id"],
        "student_name": student["name"]
    }


@router.get("/me")
async def get_me(
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

    return {
        "id": user["id"],
        "role": user["role"],
        "name": user["name"],
        # "rollNumber": user.get("rollNumber"),
        # "department": user.get("department")
    }