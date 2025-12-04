"""Tiện ích kết nối Kafka: tạo Producer/Consumer với JSON."""

import json
from typing import Any
from kafka import KafkaProducer, KafkaConsumer

from .config import KAFKA_BOOTSTRAP_SERVERS


def create_producer() -> KafkaProducer:
    """Tạo KafkaProducer với value là JSON."""
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )


def create_consumer(topic: str, group_id: str) -> KafkaConsumer:
    """Tạo KafkaConsumer đọc JSON từ một topic nhất định."""
    return KafkaConsumer(
        topic,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=group_id,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="latest",
        enable_auto_commit=True,
    )
