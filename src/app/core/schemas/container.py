from typing import Dict, Optional

from src.app.core.schemas.base import CommonBaseModel


class ContainerBase(CommonBaseModel):
    image: str
    command: Optional[str] = None


class ContainerCreate(ContainerBase):
    env: Optional[Dict[str, str]] = {}


class Container(ContainerBase):
    id: str
    image: str
    status: str
    url: str


class ServiceScale(CommonBaseModel):
    service_name: str
    replicas: int


class LogEntry(CommonBaseModel):
    timestamp: str
    message: str


class ContainerLog(CommonBaseModel):
    logs: list[LogEntry]


class ScaleRequest(CommonBaseModel):
    container_id: str
    scale_target: int
