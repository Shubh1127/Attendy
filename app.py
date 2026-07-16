import logging
import time
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes.student import router as student_router
from api.routes.subjects import router as subjects_router
from api.routes.attendance import router as attendance_router
from api.routes.teacher import router as teacher_router
from core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Attendy")

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()

    logger.info("=" * 80)
    logger.info("REQUEST")
    logger.info("Method : %s", request.method)
    logger.info("Path   : %s", request.url.path)
    logger.info("URL    : %s", request.url)
    logger.info("Client : %s", request.client.host if request.client else "Unknown")

    try:
        body = await request.body()
        if body:
            logger.info("Body   : %s", body.decode(errors="ignore"))
    except Exception:
        logger.info("Body   : <Unable to read>")

    try:
        response = await call_next(request)

        elapsed = (time.time() - start) * 1000

        logger.info("RESPONSE")
        logger.info("Status : %s", response.status_code)
        logger.info("Time   : %.2f ms", elapsed)
        logger.info("=" * 80)

        return response

    except Exception as e:
        elapsed = (time.time() - start) * 1000

        logger.error("=" * 80)
        logger.error("UNHANDLED EXCEPTION")
        logger.error("Method : %s", request.method)
        logger.error("Path   : %s", request.url.path)
        logger.error("Error  : %s", str(e))
        logger.error("Time   : %.2f ms", elapsed)
        logger.error(traceback.format_exc())
        logger.error("=" * 80)

        return JSONResponse(
            status_code=500,
            content={"detail": str(e)},
        )


app.include_router(student_router)
app.include_router(subjects_router)
app.include_router(attendance_router)
app.include_router(teacher_router)


@app.get("/health")
def health():
    logger.info("Health endpoint called")
    return {"ok": True}