import logging
import time
from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from prometheus_client import CONTENT_TYPE_LATEST

from app.metrics import (
    PREDICT_ERRORS_TOTAL,
    PREDICT_LATENCY_SECONDS,
    PREDICT_REQUESTS_TOTAL,
    metrics_exposition,
)
from app.model import ModelManager
from app.schemas import (
    PatientInput,
    PredictionOutput,
    PredictionRequest,
    PredictionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def get_model_manager(request: Request) -> ModelManager:
    return request.app.state.model_manager


@router.get('/health')
async def health(request: Request) -> dict[str, Any]:
    return get_model_manager(request).health()


@router.get('/ready')
async def ready(request: Request) -> dict[str, Any]:
    try:
        get_model_manager(request).load_model()
        return {'status': 'ready'}
    except Exception as exc:
        logger.exception('Модель не готова')
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f'Модель не загружена: {exc}',
        )


@router.get('/metrics')
async def metrics() -> Response:
    return Response(
        content=metrics_exposition(),
        media_type=CONTENT_TYPE_LATEST,
    )


@router.post('/predict', response_model=PredictionResponse)
async def predict(
    predict_data: PredictionRequest, request: Request
) -> PredictionResponse:
    if not predict_data.patients:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Список пациентов пуст',
        )

    PREDICT_REQUESTS_TOTAL.inc()
    start = time.perf_counter()
    try:
        rows = [patient.model_dump() for patient in predict_data.patients]
        probabilities = get_model_manager(request).predict_patients(rows)
        return PredictionResponse(
            predictions=[
                PredictionOutput(
                    id=index + 1,
                    prediction=int(probability >= 0.5),
                    probability=round(probability, 6),
                )
                for index, probability in enumerate(probabilities)
            ]
        )
    except Exception as exc:
        PREDICT_ERRORS_TOTAL.inc()
        logger.exception('Ошибка инференса')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Ошибка инференса: {exc}',
        )
    finally:
        PREDICT_LATENCY_SECONDS.observe(time.perf_counter() - start)


@router.post('/api/get_prediction/')
async def get_prediction(
    data: PatientInput, request: Request
) -> dict[str, float]:
    PREDICT_REQUESTS_TOTAL.inc()
    start = time.perf_counter()
    try:
        probabilities = get_model_manager(request).predict_patients([data.model_dump()])
        return {'predict': round(probabilities[0] * 100, 2)}
    except Exception as exc:
        PREDICT_ERRORS_TOTAL.inc()
        logger.exception('Ошибка инференса')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Ошибка инференса: {exc}',
        )
    finally:
        PREDICT_LATENCY_SECONDS.observe(time.perf_counter() - start)


@router.post('/api/get_predictions/')
async def get_predictions(file: UploadFile, request: Request) -> list[dict[str, Any]]:
    if file.content_type not in ('text/csv', 'application/vnd.ms-excel'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Ожидается CSV-файл',
        )

    PREDICT_REQUESTS_TOTAL.inc()
    start = time.perf_counter()
    try:
        content = await file.read()
        return get_model_manager(request).predict_csv(content)
    except Exception as exc:
        PREDICT_ERRORS_TOTAL.inc()
        logger.exception('Ошибка инференса')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Ошибка инференса: {exc}',
        )
    finally:
        PREDICT_LATENCY_SECONDS.observe(time.perf_counter() - start)
