import json
from bs4 import BeautifulSoup


def extract_comments(html_content):
    if not html_content or not html_content.strip():
        return []
    soup = BeautifulSoup(html_content, "lxml")
    comments_list = []

    reviews = soup.find_all("div", attrs={"data-review-id": True})

    for review in reviews:
        comment_body = review.find(
            "div",
            attrs={"style": lambda v: v and "line-height: 1.25rem" in v},
        )
        if comment_body:
            comments_list.append(comment_body.get_text(strip=True))
    return comments_list


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


def transform(html_listing, reviews_html):
    rating, review_count = extract_metrics(html_listing)
    reviews = extract_comments(reviews_html) if reviews_html else []
    return {
        "rating": rating,
        "review_count": review_count,
        "reviews": reviews,
    }