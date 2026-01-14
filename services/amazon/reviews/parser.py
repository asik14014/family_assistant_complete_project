import json
from dotenv import load_dotenv
import requests
from requests_html import AsyncHTMLSession
import hashlib
import random
import os

load_dotenv()

SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
]

def build_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection": "keep-alive"
    }

def parse_reviews_from_html(html: str) -> list:
    print(f"response received: {html}")
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    review_blocks = soup.select(".review")

    reviews = []
    for block in review_blocks:
        title = block.select_one(".review-title span")
        text = block.select_one(".review-text span")
        rating = block.select_one(".review-rating span")
        date = block.select_one(".review-date")

        body = text.text.strip() if text else ''
        date_str = date.text.strip() if date else ''
        review_id = hashlib.sha256(f"{body}_{date_str}".encode()).hexdigest()

        reviews.append({
            'id': review_id,
            'title': title.text.strip() if title else '',
            'text': body,
            'rating': rating.text.strip() if rating else '',
            'date': date_str
        })

    print(f"reviews: {reviews}")

    return reviews

def fetch_reviews(asin: str) -> list:

    base_url = f"https://www.amazon.com/product-reviews/{asin}"
    api_url = f"http://api.scraperapi.com/?api_key={SCRAPERAPI_KEY}&url={base_url}"
    print(f"api url: {api_url}")
    resp = requests.get(api_url)

    print(f"Status code: {resp.status_code}")
    
    if resp.status_code == 404:
        return []
    if resp.status_code != 200:
        raise Exception(f"Failed to fetch reviews for {asin}, status {resp.status_code}")

    return parse_reviews_from_html(resp.text)