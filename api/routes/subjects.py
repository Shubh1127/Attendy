
from fastapi import APIRouter, UploadFile, File, HTTPException, Header, Path
from database.config import supabase
from core.schemas import CreateSubjectRequest, JoinSubjectRequest
from core.auth import get_user_from_token
router = APIRouter()
import pdfplumber


from io import BytesIO


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
        "teacher_id": teacher["id"],
        "student_count": 0,
        "attendance_rate": 0
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

    

        # -------------------------
    # ATTENDANCE STATISTICS
    # -------------------------

    total_sessions = len({
        log["session_id"]
        for log in attendance_logs
    })

    present = 0
    absent = 0
    late = 0
    excused = 0

    for log in attendance_logs:

        if log["status"] == "present":
            present += 1

        elif log["status"] == "absent":
            absent += 1

        elif log["status"] == "late":
            late += 1

        elif log["status"] == "excused":
            excused += 1

    attendance_rate = 0

    total_records = (
        present +
        absent +
        late +
        excused
    )

    if total_records > 0:

        attendance_rate = round(
            (
                (present + late + excused)
                /
                total_records
            ) * 100,
            2
        )

    result = {
            "subject_id": subject["subject_id"],
            "subject_code": subject["subject_code"],
            "name": subject["name"],
            "section": subject["section"],
            "teacher_id": subject["teacher_id"],
            "studentCount": student_count,
            "totalSessions": total_sessions,
            "present": present,
            "absent": absent,
            "late": late,
            "excused": excused,
            "attendanceRate": attendance_rate
}

    print(result)

    return result




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



@router.post("/subjects/{subject_id}/students/upload")
async def upload_students_pdf(
    subject_id: int = Path(...),
    file: UploadFile = File(...),
    authorization: str = Header(...)
):

    # ------------------------------------
    # VERIFY TOKEN
    # ------------------------------------

    token = authorization.replace(
        "Bearer ",
        ""
    )

    teacher = get_user_from_token(
        token
    )

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

    # ------------------------------------
    # VERIFY SUBJECT
    # ------------------------------------

    subject = (
        supabase
        .table("subjects")
        .select("*")
        .eq("subject_id", subject_id)
        .eq("teacher_id", teacher["id"])
        .execute()
    )

    if not subject.data:

        raise HTTPException(
            status_code=404,
            detail="Subject not found"
        )

    # ------------------------------------
    # VERIFY FILE
    # ------------------------------------

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )
    pdf_bytes = await file.read()

    students = []

    try:

        with pdfplumber.open(
            BytesIO(pdf_bytes)
        ) as pdf:

            for page in pdf.pages:

                tables = page.extract_tables()

                for table in tables:

                    if not table:
                        continue

                    headers = [
                        str(column).strip() if column is not None else ""
                        for column in table[0]
                    ]

                    try:
                        enrollment_index = headers.index("Enrollment Number")
                        name_index = headers.index("Name")
                    except ValueError:
                        continue

                    for row in table[1:]:

                        if not row:
                            continue

                        if len(row) <= max(enrollment_index, name_index):
                            continue

                        enrollment_number = row[enrollment_index]
                        name = row[name_index]

                        if enrollment_number is None or name is None:
                            continue

                        enrollment_number = str(enrollment_number).strip()
                        try:
                             enrollment_number = int(enrollment_number)
                        except ValueError:
                         raise HTTPException(
                            status_code=400,
                            detail=f"Invalid enrollment number: {enrollment_number}"
                        )
                        name = str(name).strip()

                        if not enrollment_number or not name:
                            continue

                        students.append({
                            "enrollment_number": enrollment_number,
                            "name": name,
                        })

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Unable to read PDF"
        )

    if not students:
        raise HTTPException(
            status_code=400,
            detail="No student data found in PDF"
        )

    unique_students = []
    seen_enrollment_numbers = set()

    for student in students:

        if student["enrollment_number"] in seen_enrollment_numbers:
            continue

        seen_enrollment_numbers.add(student["enrollment_number"])
        unique_students.append(student)

    students = unique_students

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
        int(student["enrollment_number"])
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
    # GET ALL STUDENTS FROM DATABASE
    # ---------------------------------

    enrollment_numbers = [
        student["enrollment_number"]
        for student in students
    ]

    all_students = (
        supabase
        .table("student")
        .select("student_id,enrollment_number")
        .in_("enrollment_number", enrollment_numbers)
        .execute()
    )

 #0 ---------------------------------
# FIND EXISTING ENROLLMENTS
# ---------------------------------

    existing_enrollments = (
        supabase
        .table("subjects_student")
        .select("student_id")
        .eq("subject_id", subject_id)
        .execute()
    )

    enrolled_student_ids = {
        row["student_id"]
        for row in existing_enrollments.data
    }

    # ---------------------------------
    # PREPARE SUBJECT ENROLLMENTS
    # ---------------------------------

    enrollments = []

    for student in all_students.data:

        if student["student_id"] not in enrolled_student_ids:

            enrollments.append({

                "subject_id": subject_id,

                "student_id": student["student_id"]

            })

    # ---------------------------------
    # INSERT SUBJECT ENROLLMENTS
    # ---------------------------------

    if enrollments:

        (
            supabase
            .table("subjects_student")
            .insert(enrollments)
            .execute()
        )

    # ---------------------------------
    # UPDATE SUBJECT STUDENT COUNT
    # ---------------------------------

    student_count = (
        supabase
        .table("subjects_student")
        .select("student_id", count="exact")
        .eq("subject_id", subject_id)
        .execute()
    )

    (
        supabase
        .table("subjects")
        .update({
            "student_count": student_count.count
        })
        .eq("subject_id", subject_id)
        .execute()
    )
    # ---------------------------------
    # RETURN RESPONSE
    # ---------------------------------

    return {

        "success": True,

        "message": "Students uploaded successfully",

        "students_added": len(inserted_students),

        "students_enrolled": len(enrollments)

    }

   