from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.student import router as student_router
from api.routes.subjects import router as subjects_router
from api.routes.attendance import router as attendance_router
from api.routes.teacher import router as teacher_router
from core.config import settings

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(student_router)
app.include_router(subjects_router)
app.include_router(attendance_router)
app.include_router(teacher_router)

@app.get("/health")
def health():
    return {"ok": True}
