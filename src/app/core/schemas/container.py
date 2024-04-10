from typing import Dict, Optional
from pydantic import Field
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
    labels: Optional[Dict[str, str]] = Field(default_factory=dict)


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


class ScaleContainerRequest(CommonBaseModel):
    image: str
