"""
Mô tả topology mạng demo:

- Host:
    H1: Host ở phía "trái"
    H2: Host ở phía "phải"

- Switch (access):
    SW1: Access switch kết nối H1 với core
    SW2: Access switch kết nối H2 với core

- Router (core):
    R1, R2, R3, R4: các router trong mạng lõi
    → Hệ thống traffic engineering sẽ giám sát & tối ưu các link giữa R1..R4.

- Core links (lớp L3, TE giám sát):
    L1: R1 <-> R2 (1000 Mbps)
    L2: R2 <-> R3 (1000 Mbps)
    L3: R1 <-> R3 (500 Mbps)
    L4: R3 <-> R4 (1000 Mbps)
    L5: R2 <-> R4 (500 Mbps)

- Access links (lớp L2, chỉ để minh họa sơ đồ, không đưa vào TE):
    A1: H1 <-> SW1
    A2: SW1 <-> R1
    A3: H2 <-> SW2
    A4: SW2 <-> R4

ASCII sơ đồ (ngắn gọn):

    H1 ----- SW1 === R1 ---L1--- R2 ---L2--- R3 ---L4--- R4 === SW2 ----- H2
                      \\          /             \\ 
                       \\--L3----/               \\--L5--/

Trong code:
- Các metric, severity, routing chỉ áp dụng trên L1..L5 (link giữa router).
- H1, H2, SW1, SW2 tồn tại để giải thích topology trong báo cáo & demo.
"""

from typing import Dict, Tuple, List

# Thông tin node: host / switch / router
NODES = {
    "H1": {"type": "host", "label": "Host 1"},
    "H2": {"type": "host", "label": "Host 2"},
    "SW1": {"type": "switch", "label": "Access Switch 1"},
    "SW2": {"type": "switch", "label": "Access Switch 2"},
    "R1": {"type": "router", "label": "Core Router 1"},
    "R2": {"type": "router", "label": "Core Router 2"},
    "R3": {"type": "router", "label": "Core Router 3"},
    "R4": {"type": "router", "label": "Core Router 4"},
}

# Access links (L2) – chỉ để vẽ sơ đồ, không dùng cho TE
ACCESS_LINKS = [
    ("H1", "SW1"),
    ("SW1", "R1"),
    ("H2", "SW2"),
    ("SW2", "R4"),
]

# Core links (L3) – đây là phần TE sẽ monitor và tối ưu
CORE_LINKS = {
    "L1": ("R1", "R2", 1000),
    "L2": ("R2", "R3", 1000),
    "L3": ("R1", "R3", 500),
    "L4": ("R3", "R4", 1000),
    "L5": ("R2", "R4", 500),
}


def get_links() -> Dict[str, Tuple[str, str, int]]:
    """
    Trả về các core links (giữa router) với format:
    link_id -> (src_node, dst_node, capacity_mbps)

    Hàm này được Producer dùng để sinh metric cho từng link.
    """
    return CORE_LINKS


def build_adjacency() -> Dict[str, List[tuple]]:
    """
    Xây dựng adjacency list chỉ cho lớp core (router):

    Trả về: node -> List[(neighbor_node, link_id)]

    API /route sẽ dùng adjacency này cho thuật toán Dijkstra.
    """
    adj: Dict[str, List[tuple]] = {}
    for link_id, (u, v, _cap) in CORE_LINKS.items():
        adj.setdefault(u, []).append((v, link_id))
        adj.setdefault(v, []).append((u, link_id))
    return adj


def pretty_print_topology() -> None:
    """
    In ra mô tả topology cho mục đích demo / báo cáo.
    """
    print("=== TOPOLOGY MẠNG DEMO ===")
    print("\nNodes:")
    for node, info in NODES.items():
        print(f"  - {node:3s}: {info['type'].upper():7s} | {info['label']}")

    print("\nAccess links (L2, minh họa):")
    for a, b in ACCESS_LINKS:
        print(f"  - {a} <--> {b}")

    print("\nCore links (L3, TE giám sát):")
    for link_id, (u, v, cap) in CORE_LINKS.items():
        print(f"  - {link_id}: {u} <--> {v}  (capacity = {cap} Mbps)")

    print("\nASCII sơ đồ (tóm tắt):")
    print(r"")
    print(r"   H1 ----- SW1 === R1 ---L1--- R2 ---L2--- R3 ---L4--- R4 === SW2 ----- H2")
    print(r"                     \\          /             \\")
    print(r"                      \\--L3----/               \\--L5--/")
    print("")


if __name__ == "__main__":
    # Cho phép chạy: python -m common.topology để in sơ đồ ra màn hình
    pretty_print_topology()
