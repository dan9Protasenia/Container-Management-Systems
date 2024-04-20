from fastapi import Path

from src.app.api.metrics.service import MetricsService


async def get_container_metrics(container_id: str = Path(...)):
    metrics = MetricsService.get_container_stats(container_id)
    return MetricsService.analyze_stats(metrics)
