"""Alert Engine: phân tích metric link và sinh cảnh báo + trạng thái.

- Nhận dữ liệu metric từ topic RAW_TOPIC.
- Đánh giá mức độ: LOW / MEDIUM / HIGH / CRITICAL.
- Gửi:
  + Alert chi tiết lên ALERT_TOPIC.
  + Trạng thái link (state) lên STATE_TOPIC (sử dụng bản mới nhất mỗi link).
"""

import logging

from common.kafka_utils import create_consumer, create_producer
from common.config import RAW_TOPIC, ALERT_TOPIC, STATE_TOPIC

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Các ngưỡng demo (có thể đưa vào báo cáo và giải thích):
UTIL_HIGH = 90.0   # %
UTIL_MED = 70.0

LAT_HIGH = 50.0    # ms
LAT_MED = 30.0

LOSS_HIGH = 5.0    # %
LOSS_MED = 1.0


def classify_severity(util: float, latency: float, loss: float, down: bool) -> str:
    """Phân loại mức độ nghiêm trọng của trạng thái link."""
    if down:
        return "CRITICAL"

    if util >= UTIL_HIGH or latency >= LAT_HIGH or loss >= LOSS_HIGH:
        return "HIGH"

    if util >= UTIL_MED or latency >= LAT_MED or loss >= LOSS_MED:
        return "MEDIUM"

    return "LOW"


def build_alert_message(link_id: str, severity: str, down: bool) -> str:
    if down:
        return f"Link {link_id} DOWN – cần chuyển hướng traffic ngay!"

    if severity == "HIGH":
        return f"Congestion nặng trên link {link_id}, nên tránh route qua link này."
    if severity == "MEDIUM":
        return f"Link {link_id} đang tải cao, latency tăng."
    return f"Link {link_id} hoạt động bình thường."


def main() -> None:
    consumer = create_consumer(RAW_TOPIC, group_id="net-alert-engine")
    producer = create_producer()

    logger.info("⚙️ Net alert engine started. Listening for link metrics...")

    try:
        for msg in consumer:
            data = msg.value
            link_id = data["link_id"]
            util = data["utilization_pct"]
            latency = data["latency_ms"]
            loss = data["packet_loss_pct"]
            down = data["link_down"]
            ts = data["timestamp"]

            severity = classify_severity(util, latency, loss, down)

            alert = {
                "link_id": link_id,
                "src": data["src"],
                "dst": data["dst"],
                "timestamp": ts,
                "severity": severity,
                "link_down": down,
                "utilization_pct": util,
                "latency_ms": latency,
                "packet_loss_pct": loss,
                "message": build_alert_message(link_id, severity, down),
            }

            # Gửi alert
            producer.send(ALERT_TOPIC, alert)

            # Gửi state – bản mới nhất mỗi link
            state = {
                "link_id": link_id,
                "src": data["src"],
                "dst": data["dst"],
                "capacity_mbps": data["capacity_mbps"],
                "last_update": ts,
                "severity": severity,
                "link_down": down,
                "utilization_pct": util,
                "throughput_mbps": data["throughput_mbps"],
                "latency_ms": latency,
                "packet_loss_pct": loss,
            }
            producer.send(STATE_TOPIC, state)

            producer.flush()
            logger.info("Alert: %s", alert)

    except KeyboardInterrupt:
        logger.info("Net alert engine stopped.")


if __name__ == "__main__":
    main()
