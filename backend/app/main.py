from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.audit import extract_actor_email, extract_request_id
from app.routers import tags, questions, exams, media, ghost, audit
from app.core.config import settings


app = FastAPI(
    title="UG Backend",
    description="API endpoints and database for the Ultrasound Guidance app",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix=settings.API_V1_PREFIX)
api_router.include_router(tags.router)
api_router.include_router(questions.router)
api_router.include_router(exams.router)
api_router.include_router(media.router)
api_router.include_router(ghost.router)
api_router.include_router(audit.router)

app.include_router(api_router)


@app.middleware("http")
async def add_request_context(request: Request, call_next):
    request.state.request_id = extract_request_id(request)
    request.state.actor_email = extract_actor_email(request)

    response = await call_next(request)
    response.headers["x-request-id"] = request.state.request_id
    return response


@app.get("/")
def root():
    return {"message": "Hello world! 🚀"}
