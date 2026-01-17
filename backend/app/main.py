from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import tags, questions, exams, media, ghost
from app.core.config import settings


app = FastAPI(
    title='UG Backend',
    description='API endpoints and database for the Ultrasound Guidance app',
    version='0.1.0',
    docs_url='/docs',
    redoc_url='/redoc',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

api_router = APIRouter(prefix=settings.API_V1_PREFIX)
api_router.include_router(tags.router)
api_router.include_router(questions.router)
api_router.include_router(exams.router)
api_router.include_router(media.router)
api_router.include_router(ghost.router)

app.include_router(api_router)


@app.get("/")
def root():
   return {
       "message": "Hello world! 🚀"
   }
