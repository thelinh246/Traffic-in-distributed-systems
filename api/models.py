"""Pydantic models cho API trả về."""

from typing import Optional, List
from pydantic import BaseModel


class LinkState(BaseModel):
    link_id: str
    src: str
    dst: str
    capacity_mbps: int
    last_update: str
    severity: str
    link_down: bool
    utilization_pct: float
    throughput_mbps: float
    latency_ms: float
    packet_loss_pct: float


class LinkAlert(BaseModel):
    link_id: str
    src: str
    dst: str
    timestamp: str
    severity: str
    link_down: bool
    utilization_pct: float
    latency_ms: float
    packet_loss_pct: float
    message: str


class RouteSegment(BaseModel):
    link_id: str
    src: Optional[str] = None
    dst: Optional[str] = None
    severity: Optional[str] = None
    link_down: Optional[bool] = None
    utilization_pct: Optional[float] = None
    latency_ms: Optional[float] = None
    packet_loss_pct: Optional[float] = None


class RouteResult(BaseModel):
    src: str
    dst: str
    path_links: List[str]
    total_cost: float
    segments: List[RouteSegment]
