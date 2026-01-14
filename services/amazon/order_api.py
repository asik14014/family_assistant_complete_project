# services/amazon/order_api.py
import os
import requests

SP_API_BASE = "https://sellingpartnerapi-na.amazon.com"

def get_order_details(order_id: str, access_token: str, marketplace_id: str):
    url = f"{SP_API_BASE}/orders/v0/orders/{order_id}"
    headers = {
        "x-amz-access-token": access_token,
        "Content-Type": "application/json"
    }
    params = {
        "MarketplaceIds": marketplace_id
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    return response.json()


def get_order_items_details(order_id: str, access_token: str, marketplace_id: str):
    url = f"{SP_API_BASE}/orders/v0/orders/{order_id}/orderItems"
    headers = {
        "x-amz-access-token": access_token,
        "Content-Type": "application/json"
    }
    params = {
        "MarketplaceIds": marketplace_id
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    return response.json()