

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

import pdfplumber
import pandas as pd


@router.post("/students/upload")
async def upload_students(
    file: UploadFile = File(...),
    authorization: str = Header(...)
):

    # ---------------------------------
    # VERIFY TOKEN
    # ---------------------------------

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

    # ---------------------------------
    # VERIFY FILE
    # ---------------------------------

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    # ---------------------------------
    # READ PDF
    # ---------------------------------

    pdf_bytes = await file.read()

    rows = []

    try:

        with pdfplumber.open(
            BytesIO(pdf_bytes)
        ) as pdf:

            for page in pdf.pages:

                tables = page.extract_tables()

                for table in tables:

                    if not table:
                        continue

                    headers = table[0]

                    for row in table[1:]:

                        if row:
                            rows.append(row)

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Unable to read PDF"
        )

    if not rows:
        raise HTTPException(
            status_code=400,
            detail="No student data found in PDF"
        )

    # ---------------------------------
    # CONVERT TO DATAFRAME
    # ---------------------------------

    df = pd.DataFrame(
        rows,
        columns=headers
    )

    # ---------------------------------
    # VALIDATE COLUMNS
    # ---------------------------------

    required_columns = [
        "Enrollment Number",
        "Name"
    ]

    for column in required_columns:

        if column not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing column: {column}"
            )

    # ---------------------------------
    # CLEAN DATA
    # ---------------------------------

    df = df[required_columns]

    df.columns = [
        "enrollment_number",
        "name"
    ]

    df = df.dropna()

    df["enrollment_number"] = (
        df["enrollment_number"]
        .astype(str)
        .str.strip()
    )

    df["name"] = (
        df["name"]
        .astype(str)
        .str.strip()
    )

    df = df.drop_duplicates(
        subset=["enrollment_number"]
    )

    students = df.to_dict(
        orient="records"
    )

    # ---------------------------------
    # REMOVE ALREADY EXISTING STUDENTS
    # ---------------------------------

    existing = (
        supabase
        .table("student")
        .select("enrollment_number")
        .execute()
    )

    existing_numbers = {
        student["enrollment_number"]
        for student in existing.data
    }

    students_to_insert = []

    for student in students:

        if student["enrollment_number"] not in existing_numbers:

            students_to_insert.append({

                "name": student["name"],

                "enrollment_number": student["enrollment_number"],

                "is_registered": False

            })

    # ---------------------------------
    # INSERT INTO DATABASE
    # ---------------------------------

    if students_to_insert:

        inserted = (
            supabase
            .table("student")
            .insert(
                students_to_insert
            )
            .execute()
        )

        inserted_students = inserted.data

    else:

        inserted_students = []

    # ---------------------------------
    # RETURN RESPONSE
    # ---------------------------------

    return {

        "success": True,

        "message": f"{len(inserted_students)} students uploaded successfully",

        "students": inserted_students

    }

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
        
        token = create_access_token(
        user_id=student["id"],
        role="student",
        name=student["name"]
    )

        return {
            "action": "login",
            "matched": True,
            "token": token,
            "student_id": student["id"],
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

    token = create_access_token(
        user_id=student["id"],
        role="student",
        name=student["name"]
    )

    return {
        "action": "register",
        "registered": True,
        "token": token,
        "student_id": student["id"],
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