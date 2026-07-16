from pydantic import BaseModel


class TokenUser(BaseModel):
    id: str
    role: str
    name: str
    email: str | None = None
    avatarUrl: str | None = None
    rollNumber: str | None = None
    department: str | None = None


class AuthSession(BaseModel):
    token: str
    expiresAt: str
    user: TokenUser

class Student(BaseModel):
    id: str
    name: str
    enrollmentNumber: str | None = None
    faceEmbedding: list[float] | None = None
    voiceEmbedding: list[float] | None = None

class StudentRegisterRequest(BaseModel):
    enrollmentNumber: str
    faceEmbedding: list[float]
    voiceEmbedding: list[float]


class BiometricLoginResult(BaseModel):
    matched: bool
    confidence: float
    session: AuthSession | None = None
    reason: str | None = None


class Subject(BaseModel):
    id: str
    name: str
    code: str
    term: str
    teacherId: str
    teacherName: str
    studentCount: int
    schedule: str | None = None
    attendanceRate: float | None = None
    color: str

class CreateSubjectRequest(BaseModel):
    subject_code: str
    name: str
    section: str

class JoinSubjectRequest(BaseModel):
    code: str



class CreateAttendanceSessionRequest(BaseModel):
    subjectId: int


class AttendanceEntryUpdate(BaseModel):
    studentId: int
    status: str


class UpdateAttendanceSessionRequest(BaseModel):
    entries: list[AttendanceEntryUpdate]

class TeacherLoginRequest(BaseModel):
    name: str
    email: str
    password: str


class TeacherLoginResponse(BaseModel):
    email: str
    password: str