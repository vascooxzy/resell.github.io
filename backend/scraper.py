import time
import random
import logging
import re
from typing import Optional
from dataclasses import dataclass, field

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS_POOL = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "pt-PT,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://pt.dhgate.com/",
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Accept-Language": "pt-PT,pt;q=0.8,en-GB;q=0.5,en;q=0.3",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://pt.dhgate.com/",
    },
]

BASE_URL = "https://pt.dhgate.com"


@dataclass
class Product:
    name: str
    price: str
    rating: str
    seller: str
    link: str
    image: str
    orders: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "price": self.price,
            "rating": self.rating,
            "seller": self.seller,
            "link": self.link,
            "image": self.image,
            "orders": self.orders,
        }


def _get_headers() -> dict:
    return random.choice(HEADERS_POOL)


def _random_delay(min_s: float = 1.5, max_s: float = 3.5) -> None:
    delay = random.uniform(min_s, max_s)
    logger.debug(f"Waiting {delay:.2f}s before next request")
    time.sleep(delay)


def _clean_text(text: Optional[str]) -> str:
    if not text:
        return "N/A"
    return re.sub(r"\s+", " ", text).strip()


def _extract_price(element) -> str:
    """Try multiple selectors to find the price."""
    selectors = [
        ".price-current",
        ".product-price",
        ".prd-price",
        "[class*='price']",
        ".item-price",
    ]
    for sel in selectors:
        node = element.select_one(sel)
        if node:
            txt = _clean_text(node.get_text())
            if txt and txt != "N/A":
                return txt
    return "N/A"


def _extract_rating(element) -> str:
    selectors = [
        ".feedback-stars",
        "[class*='star']",
        "[class*='rating']",
        ".item-rating",
    ]
    for sel in selectors:
        node = element.select_one(sel)
        if node:
            # Check aria-label or data attributes first
            for attr in ("aria-label", "data-score", "data-rating", "title"):
                val = node.get(attr, "")
                if val:
                    return _clean_text(val)
            txt = _clean_text(node.get_text())
            if txt and txt != "N/A":
                return txt
    return "N/A"


def _extract_seller(element) -> str:
    selectors = [
        ".seller-name",
        ".store-name",
        "[class*='seller']",
        "[class*='store']",
        ".shopname",
    ]
    for sel in selectors:
        node = element.select_one(sel)
        if node:
            txt = _clean_text(node.get_text())
            if txt and txt != "N/A":
                return txt
    return "N/A"


def _extract_link(element) -> str:
    link_node = element.select_one("a[href]")
    if link_node:
        href = link_node.get("href", "")
        if href.startswith("http"):
            return href
        return BASE_URL + href
    return "N/A"


def _extract_image(element) -> str:
    img = element.select_one("img[src], img[data-src], img[data-lazy-src]")
    if img:
        for attr in ("src", "data-src", "data-lazy-src", "data-original"):
            val = img.get(attr, "")
            if val and val.startswith("http"):
                return val
    return ""


def _extract_orders(element) -> str:
    selectors = [
        "[class*='order']",
        "[class*='sold']",
        ".trade-count",
    ]
    for sel in selectors:
        node = element.select_one(sel)
        if node:
            txt = _clean_text(node.get_text())
            if txt and txt != "N/A":
                return txt
    return "N/A"


def _parse_product_cards(soup: BeautifulSoup) -> list[Product]:
    """
    Attempt multiple container selectors to find product cards.
    Returns a list of Product objects.
    """
    container_selectors = [
        ".gallery-item",
        ".item-info-wrap",
        ".product-item",
        "li.item",
        "[class*='product-card']",
        "[class*='item-card']",
        ".search-result-item",
        "ul.gallery-bd > li",
    ]

    cards = []
    for sel in container_selectors:
        cards = soup.select(sel)
        if cards:
            logger.info(f"Found {len(cards)} cards with selector '{sel}'")
            break

    if not cards:
        logger.warning("No product cards found with any known selector")
        return []

    products = []
    for card in cards:
        name_node = card.select_one(
            ".item-title, .product-name, [class*='title'], h2, h3"
        )
        name = _clean_text(name_node.get_text()) if name_node else "N/A"

        if name == "N/A":
            continue

        products.append(
            Product(
                name=name,
                price=_extract_price(card),
                rating=_extract_rating(card),
                seller=_extract_seller(card),
                link=_extract_link(card),
                image=_extract_image(card),
                orders=_extract_orders(card),
            )
        )

    return products


def scrape_dhgate(query: str, max_pages: int = 1) -> list[dict]:
    """
    Scrape DHgate search results for the given query.

    Args:
        query: Search term.
        max_pages: Number of pages to scrape (default 1).

    Returns:
        List of product dicts.
    """
    all_products: list[Product] = []

    session = requests.Session()

    for page in range(1, max_pages + 1):
        url = f"{BASE_URL}/wholesale/search.do?act=search&searchkey={requests.utils.quote(query)}&page={page}"
        logger.info(f"Scraping page {page}: {url}")

        try:
            response = session.get(url, headers=_get_headers(), timeout=20)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error on page {page}: {e}")
            break
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed on page {page}: {e}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        products = _parse_product_cards(soup)

        if not products:
            logger.warning(f"No products found on page {page}. Stopping.")
            break

        all_products.extend(products)
        logger.info(f"Page {page}: collected {len(products)} products (total {len(all_products)})")

        if page < max_pages:
            _random_delay()

    return [p.to_dict() for p in all_products]
