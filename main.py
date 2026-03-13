"""
Challenge 3: Nacenění aut - speciální vozidla (Vehicle Pricing >3.5t)

Input:  Vehicle identification details
Output: Estimated market value with sources

Priority indicators (most to least important):
  1. Tovární značka + Model (Make + Model)
  2. Typ nástavby (Body type / superstructure)
  3. Rok výroby (Year of manufacture)
  4. Najeté km (Mileage)
"""

import os
import threading
import time

import google.generativeai as genai
import psycopg2
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Challenge 3: Vehicle Pricing")

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://hackathon:hackathon@localhost:5432/hackathon"
)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")


class GeminiTracker:
    """Wrapper around Gemini that tracks token usage."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        self.enabled = bool(api_key)
        if self.enabled:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0
        self.request_count = 0
        self._lock = threading.Lock()

    def generate(self, prompt, **kwargs):
        if not self.enabled:
            raise RuntimeError("Gemini API key not configured")
        response = self.model.generate_content(prompt, **kwargs)
        with self._lock:
            self.request_count += 1
            meta = getattr(response, "usage_metadata", None)
            if meta:
                self.prompt_tokens += getattr(meta, "prompt_token_count", 0)
                self.completion_tokens += getattr(meta, "candidates_token_count", 0)
                self.total_tokens += getattr(meta, "total_token_count", 0)
        return response

    def get_metrics(self):
        with self._lock:
            return {
                "gemini_request_count": self.request_count,
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.total_tokens,
            }

    def reset(self):
        with self._lock:
            self.prompt_tokens = 0
            self.completion_tokens = 0
            self.total_tokens = 0
            self.request_count = 0


gemini = GeminiTracker(GEMINI_API_KEY)


def get_db():
    return psycopg2.connect(DATABASE_URL)


@app.on_event("startup")
def init_db():
    for _ in range(15):
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                """CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )"""
            )
            conn.commit()
            cur.close()
            conn.close()
            return
        except Exception:
            time.sleep(1)


@app.get("/")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return gemini.get_metrics()


@app.post("/metrics/reset")
def reset_metrics():
    gemini.reset()
    return {"status": "reset"}


@app.post("/solve")
def solve(payload: dict):
    """
    Estimate market value of a heavy/special vehicle (>3.5t).

    Input example:
    {
        "make": "MAN",
        "model": "TGX 18.510 4x2",
        "year": 2020,
        "mileage_km": 320000,
        "body_type": "chladírenská nástavba",
        "additional_info": "Euro 6, BLS, retarder"
    }

    Expected output:
    {
        "estimated_value_czk": 1450000,
        "currency": "CZK",
        "price_range_czk": {
            "min": 1200000,
            "max": 1700000
        },
        "sources": [
            {
                "url": "https://www.truck1.eu/...",
                "title": "MAN TGX 18.510, 2020, chladírenská",
                "price": 52000,
                "currency": "EUR",
                "price_czk": 1300000
            },
            {
                "url": "https://www.autoline.info/...",
                "title": "MAN TGX 18.510 4x2 BLS",
                "price": 55000,
                "currency": "EUR",
                "price_czk": 1375000
            },
            {
                "url": "https://www.tipcars.com/...",
                "title": "MAN TGX 18.510",
                "price": 1500000,
                "currency": "CZK",
                "price_czk": 1500000
            }
        ],
        "methodology": "Averaged 3 listings from truck1.eu, autoline.info, tipcars.com"
    }

    Minimum 3 sources with URLs required for full score.
    """
    # TODO: Implement your solution here
    #
    # Suggested approaches:
    # 1. Use Gemini with Google Search grounding to find listings
    # 2. Scrape truck marketplaces (truck1.eu, autoline.info, mobile.de, tipcars.com)
    # 3. Use the sidecar DB to cache pricing data
    #
    # Priority for matching: make+model > body_type > year > mileage

    make = payload.get("make", "")
    model = payload.get("model", "")
    year = payload.get("year")
    mileage_km = payload.get("mileage_km")
    body_type = payload.get("body_type", "")

    result = {
        "estimated_value_czk": None,
        "currency": "CZK",
        "price_range_czk": {
            "min": None,
            "max": None,
        },
        "sources": [],
        "methodology": None,
    }

    return result


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
