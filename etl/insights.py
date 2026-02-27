import logging
import requests
import config


def parse_highlight_opportunity(text):
    highlight = None
    opportunity = None
    for line in text.split("\n"):
        line = line.strip()
        if line.lower().startswith("highlight"):
            highlight = line.split(":", 1)[1].strip()
        if line.lower().startswith("opportunity"):
            opportunity = line.split(":", 1)[1].strip()
    return highlight, opportunity


def build_prompt(reviews):
    reviews_text = "\n".join(reviews)
    return f"""Based on these 5 most recent Airbnb guest reviews:

                {reviews_text}
                
                Provide:
                Highlight: one concise sentence summarizing what guests love most.
                Opportunity: one concise sentence summarizing the most common improvement area.
                
                Respond exactly in this format:
                Highlight: ...
                Opportunity: ...
                """


def call_groq(reviews_text):
    if not config.GROQ_API_KEY:
        return None
    payload = {
        "model": config.GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a concise analyst. Reply only with Highlight: and Opportunity: lines.",
            },
            {"role": "user", "content": reviews_text},
        ],
        "max_tokens": 120,
        "temperature": 0.3,
    }
    try:
        r = requests.post(
            config.GROQ_URL,
            headers={
                "Authorization": f"Bearer {config.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )
        data = r.json()
        if not r.ok:
            logging.error("Groq API error: %s", data)
            return None
        return (data.get("choices") or [{}])[0].get("message", {}).get("content")
    except Exception as e:
        logging.error("Groq API error: %s", e)
        return None


def generate_ai_insights(reviews):
    if not config.ENABLE_AI_INSIGHTS or not reviews or not config.GROQ_API_KEY:
        return None, None
    text = call_groq(build_prompt(reviews))
    if text:
        return parse_highlight_opportunity(text)
    return None, None
