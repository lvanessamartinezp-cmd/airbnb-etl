import json
from bs4 import BeautifulSoup


def extract_metrics(html):
    soup = BeautifulSoup(html, "lxml")

    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string:
            continue
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and "aggregateRating" in data:
                rating = data["aggregateRating"].get("ratingValue")
                review_count = (
                    data["aggregateRating"].get("reviewCount")
                    or data["aggregateRating"].get("ratingCount")
                )
                return (
                    float(rating) if rating else None,
                    int(review_count) if review_count else None,
                )
        except Exception:
            continue

    return None, None


def transform(html_listing):
    rating, review_count = extract_metrics(html_listing)
    return {
        "rating": rating,
        "review_count": review_count,
    }