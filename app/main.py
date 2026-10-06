import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import router
from app.config import settings
from app.model import ModelManager

BASE_DIR = Path(__file__).resolve().parent.parent

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('Сервис %s запущен', settings.app_name)
    app.state.model_manager = ModelManager()
    yield
    logger.info('Сервис %s остановлен', settings.app_name)


app = FastAPI(
    title='Heart Attack Risk API',
    description='REST API для инференса модели предсказания риска сердечного приступа',
    lifespan=lifespan,
)

app.mount('/static', StaticFiles(directory=BASE_DIR / 'app' / 'static'), 'static')
templates = Jinja2Templates(directory=str(BASE_DIR / 'app' / 'templates'))

app.include_router(router)


@app.get('/')
async def main_page(request: Request):
    return templates.TemplateResponse(
        name='index.html',
        context={'request': request},
    )
