from database.config import supabase
import bcrypt



def hash_pass(pwd):
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

def check_pass(pwd, hashed):
    return bcrypt.checkpw(pwd.encode(), hashed.encode())


def check_teacher_exists(username):
    # Check for unique username, returns false when username is already taken
    response = supabase.table("teacher").select("username").eq("username", username).execute()
    return len(response.data) > 0 


from postgrest.exceptions import APIError


def create_teacher(
    name: str,
    password: str,
    email: str
):

    # -------------------------
    # CHECK EMAIL EXISTS
    # -------------------------

    existing = (
        supabase
        .table("teacher")
        .select("teacher_id")
        .eq("email", email)
        .execute()
    )

    if existing.data:
        return None

    # -------------------------
    # INSERT TEACHER
    # -------------------------

    try:

        response = (
            supabase
            .table("teacher")
            .insert({
                "name": name,
                "email": email,
                "password": hash_pass(password)
            })
            .execute()
        )

        return response.data[0]

    except APIError:

        return None

def teacher_login(email, password):
    response = supabase.table("teacher").select("*").eq("email", email).execute()
    if response.data:
        teacher = response.data[0]
        if check_pass(password, teacher['password']):
            return teacher
    return None


def get_all_students():
    response = supabase.table('student').select("*").execute()
    return response.data

def create_student(new_name, face_embedding=None, voice_embedding=None):
    data = {'name': new_name, 'face_embedding':face_embedding, "voice_embedding": voice_embedding}
    response = supabase.table('student').insert(data).execute()
    return response.data


def create_subject(subject_code, name, section, teacher_id):
    data = {"subject_code": subject_code, "name": name, "section": section, "teacher_id": teacher_id}
    response = supabase.table("subjects").insert(data).execute()
    return response.data

def get_teacher_subjects(teacher_id):
    response = supabase.table('subjects').select("*, subjects_student(count), attendance_logs(created_at)").eq("teacher_id", teacher_id).execute()
    subjects = response.data


    for sub in subjects:
        sub['total_students'] = sub.get("subjects_student", [{}])[0].get('count', 0) if sub.get('subjects_student') else 0
        attendance = sub.get('attendance_logs', [])
        unique_sessions = len(set(log['created_at'] for log in attendance))
        sub['total_classes'] = unique_sessions


        sub.pop('subjects_student', None)
        sub.pop('attendance_logs', None)

    return subjects


def  enroll_student_to_subject(student_id, subject_id):
    data = {'student_id': student_id, "subject_id": subject_id}
    response= supabase.table('subjects_student').insert(data).execute()
    return response.data


def  unenroll_student_to_subject(student_id, subject_id):
    response= supabase.table('subjects_student').delete().eq('student_id', student_id).eq('subject_id', subject_id).execute()
    return response.data



def get_student_subjects(student_id):
    response = supabase.table('subjects_student').select('*, subjects(*)').eq('student_id', student_id).execute()
    return response.data


def get_student_attendance(student_id):
    response = supabase.table('attendance_logs').select('*, subjects(*)').eq('student_id', student_id).execute()
    return response.data


def create_attendance(logs):
    normalized_logs = []
    for log in logs:
        entry = dict(log)
        if 'timestamp' in entry and 'created_at' not in entry:
            entry['created_at'] = entry.pop('timestamp')
        normalized_logs.append(entry)

    response = supabase.table('attendance_logs').insert(normalized_logs).execute()
    return response.data

def get_attendance_for_teacher(teacher_id):
    response = supabase.table('attendance_logs').select("*, subjects!inner(*)").eq('subjects.teacher_id', teacher_id).execute()
    return response.data

def get_all_students():
    response=supabase.table('student').select("*").execute()
    return response.data


def get_student_by_enrollment(enrollment_number):

    response = (
        supabase
        .table("student")
        .select("*")
        .eq("enrollment_number", enrollment_number)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None

def get_student_face_embedding(enrollment_number):

    response = (
        supabase
        .table("student")
        .select("face_embedding")
        .eq("enrollment_number", enrollment_number)
        .execute()
    )

    if response.data:
        return response.data[0]["face_embedding"]

    return None