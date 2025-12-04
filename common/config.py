"""Cấu hình dùng chung cho toàn hệ thống."""

from typing import Final

# Địa chỉ Kafka broker (có thể chỉnh sửa nếu cần)
KAFKA_BOOTSTRAP_SERVERS: Final[str] = "localhost:9092"

# Tên các topic Kafka
RAW_TOPIC: Final[str] = "net_traffic_raw"        # Topic chứa metric link
ALERT_TOPIC: Final[str] = "net_traffic_alerts"   # Topic chứa cảnh báo
STATE_TOPIC: Final[str] = "net_link_state"       # Topic chứa trạng thái mới nhất của link
