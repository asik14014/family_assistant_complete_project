import os
import requests
from services.amazon.amazon_client import get_access_token

SP_API_BASE = "https://sellingpartnerapi-na.amazon.com"
MARKETPLACE_ID = os.getenv("SP_MARKETPLACE_ID", "ATVPDKIKX0DER")


def get_review_eligibility(order_id: str) -> bool:
    """Return True if review solicitation is available."""
    url = f"{SP_API_BASE}/solicitations/v1/orders/{order_id}"
    params = {"marketplaceIds": MARKETPLACE_ID}
    headers = {
        "x-amz-access-token": get_access_token(),
        "Content-Type": "application/json",
    }
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code != 200:
        return False
    data = resp.json()
    actions = data.get("actions", [])
    for action in actions:
        if action.get("name") == "productReviewAndSellerFeedback":
            return True
    return False


def send_review_request(order_id: str) -> bool:
    """Send the product review and seller feedback request."""
    url = f"{SP_API_BASE}/solicitations/v1/orders/{order_id}/solicitations/productReviewAndSellerFeedback"
    params = {"marketplaceIds": MARKETPLACE_ID}
    headers = {
        "x-amz-access-token": get_access_token(),
        "Content-Type": "application/json",
    }
    resp = requests.post(url, headers=headers, params=params)
    return resp.status_code in (200, 201, 202)
