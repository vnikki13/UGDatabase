from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import tags, questions
from .core.config import settings


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

app.include_router(api_router)


@app.get("/")
def root():
   return {
       "message": "Hello world! 🚀"
   }
