"""Service Producer: giả lập metric traffic trên các link mạng.

- Mỗi vài giây, chọn ngẫu nhiên một link.
- Sinh ra throughput, utilization, latency, packet loss, trạng thái up/down.
- Gửi dữ liệu lên Kafka topic RAW_TOPIC.
"""

import random
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

from common.kafka_utils import create_producer
from common.config import RAW_TOPIC
from common.topology import get_links

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def build_link_list() -> List[Dict[str, Any]]:
    """Chuyển topology sang danh sách dict cho dễ xử lý."""
    link_dicts = []
    for link_id, (src, dst, cap) in get_links().items():
        link_dicts.append(
            {
                "link_id": link_id,
                "src": src,
                "dst": dst,
                "capacity_mbps": cap,
            }
        )
    return link_dicts


LINKS = build_link_list()


def generate_link_metric() -> Dict[str, Any]:
    """Sinh ngẫu nhiên metric cho một link."""
    link = random.choice(LINKS)
    cap = link["capacity_mbps"]

    # throughput ~ N(cap*0.5, cap*0.25)
    throughput = max(10.0, min(cap, random.gauss(cap * 0.5, cap * 0.25)))
    utilization = throughput / cap * 100.0

    latency = max(1.0, random.gauss(5.0, 3.0))  # ms
    packet_loss = max(0.0, random.gauss(0.2, 0.3))  # %
    # 3% khả năng link down
    link_down = random.random() < 0.03

    if link_down:
        # Khi down thì gần như không truyền được
        throughput = 0.0
        utilization = 0.0
        latency = random.uniform(100, 500)
        packet_loss = random.uniform(10, 50)

    return {
        "link_id": link["link_id"],
        "src": link["src"],
        "dst": link["dst"],
        "capacity_mbps": cap,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "throughput_mbps": round(throughput, 2),
        "utilization_pct": round(utilization, 2),
        "latency_ms": round(latency, 2),
        "packet_loss_pct": round(packet_loss, 2),
        "link_down": link_down,
    }


def main() -> None:
    producer = create_producer()
    logger.info("🌐 Net traffic producer started. Sending metrics to Kafka...")

    try:
        while True:
            metric = generate_link_metric()
            producer.send(RAW_TOPIC, metric)
            producer.flush()
            logger.info("Sent: %s", metric)
            time.sleep(1.5)
    except KeyboardInterrupt:
        logger.info("Producer stopped.")


if __name__ == "__main__":
    main()
