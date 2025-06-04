# services/amazon/order_parser.py

def parse_order_data(order_data: dict) -> dict:
    payload = order_data.get("payload", {})
    return payload

def parse_order_items(order_data: dict) -> dict:
    payload = order_data.get("payload", {})
    order_items = payload.get("OrderItems", [])
    return order_items
