"""API Server (FastAPI) cho hệ thống traffic mạng.

Chức năng:
- Lắng nghe Kafka topic ALERT_TOPIC và STATE_TOPIC để cập nhật:
  + latest_alerts: cảnh báo mới nhất cho mỗi link.
  + link_state: trạng thái mới nhất mỗi link.
- Cung cấp REST API cho client / giao diện người dùng:
  + GET /links: trạng thái toàn mạng.
  + GET /alerts/{link_id}: cảnh báo mới nhất của link.
  + GET /route?src=..&dst=..: gợi ý route tối ưu giữa hai node.
"""

import logging
import threading
from typing import Dict, List, Tuple

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from common.kafka_utils import create_consumer
from common.config import ALERT_TOPIC, STATE_TOPIC
from common.topology import build_adjacency, get_links
from .models import LinkState, LinkAlert, RouteSegment, RouteResult

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Distributed Network Traffic Recommendation System",
    description="""Demo hệ thống cảnh báo & khuyến nghị traffic trong mạng.
    - Producer sinh metric link
    - Alert Engine phân tích & sinh cảnh báo
    - API server gợi ý route tối ưu""",
    version="1.0.0",
)

# Cho phép frontend (file:// hoặc domain khác) gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # cho phép mọi origin (demo)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Cache trong bộ nhớ – cho demo.
link_state: Dict[str, dict] = {}
latest_alerts: Dict[str, dict] = {}

# Trọng số cho từng mức độ – dùng cho Dijkstra
SEVERITY_WEIGHT = {
    "LOW": 1.0,
    "MEDIUM": 3.0,
    "HIGH": 6.0,
    "CRITICAL": 10.0,
}


def severity_to_weight(sev: str) -> float:
    return SEVERITY_WEIGHT.get(sev, 1.0)


# ===============================
# 1. Kafka consumer chạy nền
# ===============================

def consume_state() -> None:
    consumer = create_consumer(STATE_TOPIC, group_id="api-net-state")
    logger.info("API state consumer started.")
    for msg in consumer:
        data = msg.value
        link_id = data["link_id"]
        link_state[link_id] = data


def consume_alerts() -> None:
    consumer = create_consumer(ALERT_TOPIC, group_id="api-net-alerts")
    logger.info("API alerts consumer started.")
    for msg in consumer:
        data = msg.value
        link_id = data["link_id"]
        latest_alerts[link_id] = data


def start_background_consumers() -> None:
    t1 = threading.Thread(target=consume_state, daemon=True)
    t2 = threading.Thread(target=consume_alerts, daemon=True)
    t1.start()
    t2.start()


@app.on_event("startup")
def on_startup() -> None:
    start_background_consumers()


# ===============================
# 2. REST API
# ===============================

@app.get("/links", response_model=Dict[str, LinkState])
def get_all_links():
    """Trả về trạng thái mới nhất của tất cả link trong mạng."""
    # Chỉ trả về các link thực sự có state (đã nhận từ Kafka)
    return {lid: LinkState(**st) for lid, st in link_state.items()}


@app.get("/alerts/{link_id}", response_model=LinkAlert)
def get_alert(link_id: str):
    """Trả về cảnh báo mới nhất của một link."""
    if link_id not in latest_alerts:
        raise HTTPException(status_code=404, detail="Không có cảnh báo cho link này.")
    return LinkAlert(**latest_alerts[link_id])


@app.get("/route", response_model=RouteResult)
def recommend_route(
    src: str = Query(..., description="Node bắt đầu, ví dụ S1"),
    dst: str = Query(..., description="Node đích, ví dụ S4"),
):
    """Gợi ý route tối ưu giữa src và dst, dựa trên congestion của các link.

    - Thuật toán: Dijkstra.
    - Trọng số cạnh = f(severity, latency_ms):
        weight = severity_weight + latency_ms / 10
    """
    path_links, cost = find_best_path(src, dst)
    if not path_links:
        raise HTTPException(status_code=404, detail="Không tìm được đường đi.")

    segments: List[RouteSegment] = []
    for link_id in path_links:
        st = link_state.get(link_id)
        if st is None:
            # Nếu chưa có state, vẫn trả về link nhưng thông tin rỗng / mặc định
            segments.append(RouteSegment(link_id=link_id))
        else:
            segments.append(
                RouteSegment(
                    link_id=link_id,
                    src=st["src"],
                    dst=st["dst"],
                    severity=st["severity"],
                    link_down=st["link_down"],
                    utilization_pct=st["utilization_pct"],
                    latency_ms=st["latency_ms"],
                    packet_loss_pct=st["packet_loss_pct"],
                )
            )

    return RouteResult(
        src=src,
        dst=dst,
        path_links=path_links,
        total_cost=cost,
        segments=segments,
    )


# ===============================
# 3. Dijkstra tìm đường đi tốt nhất
# ===============================

def find_best_path(src: str, dst: str):
    import heapq

    adj = build_adjacency()
    INF = 10**9

    if src not in adj or dst not in adj:
        return None, None

    dist: Dict[str, float] = {node: float(INF) for node in adj.keys()}
    prev: Dict[str, Tuple[str, str]] = {}  # node -> (prev_node, link_id)

    dist[src] = 0.0
    heap: List[Tuple[float, str]] = [(0.0, src)]

    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        if u == dst:
            break

        for v, link_id in adj.get(u, []):
            st = link_state.get(link_id, {})
            sev = st.get("severity", "LOW")
            latency = float(st.get("latency_ms", 5.0))

            w = severity_to_weight(sev) + latency / 10.0
            nd = d + w

            if nd < dist.get(v, float(INF)):
                dist[v] = nd
                prev[v] = (u, link_id)
                heapq.heappush(heap, (nd, v))

    if dist.get(dst, float(INF)) == float(INF):
        return None, None

    # reconstruct path (list link_id)
    path_links: List[str] = []
    cur = dst
    while cur != src:
        p, link_id = prev[cur]
        path_links.append(link_id)
        cur = p
    path_links.reverse()
    return path_links, dist[dst]
