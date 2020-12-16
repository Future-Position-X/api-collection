from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends

from app import models, schemas, services
from app.api import deps

router = APIRouter()


@router.post(
    "/series/{series_uuid}/metrics",
    # response_model=schemas.Series,
    # response_model_exclude_none=True,
    status_code=201,
)
def create_series_metric(
    series_uuid: UUID,
    metric_create: schemas.MetricCreate,
    current_user: models.User = Depends(deps.get_current_user),
) -> schemas.Metric:
    series = services.metric.create_series_metric(
        current_user, series_uuid, metric_create.to_dto()
    )
    return schemas.Metric.from_dto(series)


@router.get("/series/{series_uuid}/metrics", status_code=200)
def get_series_metrics(
    series_uuid: UUID,
    current_user: models.User = Depends(deps.get_current_user_or_guest),
) -> List[schemas.Metric]:
    metrics = services.metric.get_series_metrics(current_user, series_uuid)
    return [schemas.Metric.from_dto(m) for m in metrics]


@router.get("/series/{series_uuid}/metrics/{ts}", status_code=200)
def get_metric(
    series_uuid: UUID,
    ts: datetime,
    current_user: models.User = Depends(deps.get_current_user_or_guest),
) -> schemas.Metric:
    metric = services.metric.get_metric(current_user, series_uuid, ts)
    return schemas.Metric.from_dto(metric)


@router.put("/series/{series_uuid}/metrics/{ts}", status_code=204)
def update_metric(
    series_uuid: UUID,
    ts: datetime,
    metric_in: schemas.MetricUpdate,
    current_user: models.User = Depends(deps.get_current_user),
) -> None:
    services.metric.update_metric(current_user, series_uuid, ts, metric_in.to_dto())
    return None


@router.delete("/series/{series_uuid}/metrics/{ts}", status_code=204)
def delete_metric(
    series_uuid: UUID,
    ts: datetime,
    current_user: models.User = Depends(deps.get_current_user),
) -> None:
    services.metric.delete_metric(current_user, series_uuid, ts)
    return None
