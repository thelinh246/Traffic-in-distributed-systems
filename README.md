# Distributed Network Traffic Alert & Recommendation System

Đây là dự án demo cho môn học về **hệ phân tán / mạng máy tính**:

- Giám sát **traffic trong mạng** ở mức **link giữa các switch/router**.
- Phát hiện **congestion / link down** và sinh **cảnh báo**.
- Đề xuất **đường đi tối ưu** giữa hai node mạng dựa trên tải và chất lượng link.

Kiến trúc chính:

- `producer`: giả lập metric traffic trên các link (throughput, utilization, latency, loss, link_down).
- `processor` (alert engine): đọc metric từ Kafka, suy luận mức độ (LOW / MEDIUM / HIGH / CRITICAL), sinh cảnh báo & trạng thái link.
- `api`: service FastAPI:
  - Xem trạng thái toàn mạng.
  - Xem cảnh báo mới nhất trên từng link.
  - Gợi ý route tối ưu giữa hai node (Dijkstra, trọng số theo congestion).

Hệ thống giao tiếp qua **Apache Kafka**, thể hiện tính chất **hệ phân tán, loosely coupled, mở rộng được**.

## 1. Cấu trúc thư mục

```text
.
├── README.md
├── docker-compose.yml        # Kafka + KRaft (Bitnami)
├── requirements.txt
├── common
│   ├── __init__.py
│   ├── config.py
│   ├── kafka_utils.py
│   └── topology.py
├── producer
│   ├── __init__.py
│   └── net_traffic_producer.py
├── processor
│   ├── __init__.py
│   └── net_alert_engine.py
└── api
    ├── __init__.py
    ├── models.py
    └── net_api_server.py
```

## 2. Chuẩn bị môi trường

Python 3.10+ (khuyến nghị) và `pip`.

Cài thư viện:

```bash
pip install -r requirements.txt
```

## 3. Khởi chạy Kafka (Docker Compose)

Trong thư mục dự án:

```bash
docker-compose up -d
```

Mặc định Kafka sẽ lắng nghe ở `localhost:9092`.

> Nếu bạn đã có Kafka riêng, cập nhật `KAFKA_BOOTSTRAP_SERVERS` trong `common/config.py`.

## 4. Chạy các service

Mở 3 terminal:

```bash
# Terminal 1 – Producer: giả lập metric link
python -m producer.net_traffic_producer

# Terminal 2 – Alert Engine: phân tích & sinh cảnh báo
python -m processor.net_alert_engine

# Terminal 3 – API Server
uvicorn api.net_api_server:app --reload --port 8000
```

Khi mọi thứ chạy, API có tại: `http://localhost:8000/docs`

## 5. Các endpoint chính

- `GET /links`  
  → Trạng thái mới nhất của tất cả link.

- `GET /alerts/{link_id}`  
  → Cảnh báo mới nhất cho link (L1, L2, ...).

- `GET /route?src=S1&dst=S4`  
  → Gợi ý route tối ưu giữa hai node mạng (S1 → S4).

## 6. Gợi ý nội dung báo cáo

- Bài toán: Giám sát và tối ưu traffic mạng, hỗ trợ Traffic Engineering.
- Kiến trúc: mô hình microservice + message broker (Kafka).
- Luồng dữ liệu:
  1. Producer gửi metric link → Kafka topic `net_traffic_raw`.
  2. Alert Engine đọc metric → phân loại severity → gửi:
     - Alert → topic `net_traffic_alerts`.
     - State link → topic `net_link_state`.
  3. API service subscribe `net_traffic_alerts` & `net_link_state` → expose REST API.
- Thuật toán chọn đường: Dijkstra, trọng số cạnh = f(severity, latency).

Bạn có thể copy hình vẽ kiến trúc và nội dung này vào báo cáo, chỉnh sửa theo style của mình.
