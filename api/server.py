"""
FastAPI server for the Flight Price Comparison System.
Serves flight data as JSON API for the frontend dashboard.

Endpoints:
  GET  /api/flights       - Returns all flights from the last CSV export
  GET  /api/flights?source=XXX - Filter by source name
  POST /api/search        - Triggers a new search (async)
  GET  /api/sources       - Lists available sources and their status
  GET  /api/stats         - Summary statistics
"""

import os
import csv
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Paths ─────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
SCRAPER_DIR = BASE_DIR / "flight_scraper"
CSV_DIR = SCRAPER_DIR / "output"
CSV_FILE = CSV_DIR / "flights_latest.csv"

# Load scraper config for defaults
sys.path.insert(0, str(SCRAPER_DIR))
import config

# ── Models ────────────────────────────────────────────────
class SearchRequest(BaseModel):
    origin: str = "MAN"
    destination: str = "FRA"
    date: str = ""
    cabin_class: str = "economy"


class FlightOut(BaseModel):
    source_name: str
    airline: str
    flight_number: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    stops: int
    stop_airports: str
    cabin_class: str
    original_price: float
    original_currency: str
    converted_price_base: float
    base_currency: str
    ticket_link: str
    baggage_info: str
    is_cheapest: bool


# ── Timezone helpers ──────────────────────────────────────
_TZ_CACHE = {}

def _tz_abbr(iana_name: str, ref_date: str = None) -> str:
    if not iana_name:
        return ""
    key = (iana_name, ref_date or "today")
    if key in _TZ_CACHE:
        return _TZ_CACHE[key]
    try:
        tz = ZoneInfo(iana_name)
        if ref_date:
            dt = datetime.strptime(ref_date, "%Y-%m-%d").replace(tzinfo=tz)
        else:
            dt = datetime.now(tz=tz)
        abbr = dt.tzname() or ""
    except Exception:
        abbr = ""
    _TZ_CACHE[key] = abbr
    return abbr


# ── CSV Reader ────────────────────────────────────────────
def load_flights_from_csv(filepath=None) -> list[dict]:
    """Load flight data from the CSV file and return as list of dicts."""
    path = filepath or CSV_FILE
    # Try to find the latest CSV
    if not path.exists():
        backups = sorted(CSV_DIR.glob("flights_latest_*.csv"), reverse=True)
        if backups:
            path = backups[0]
        else:
            return []

    rows = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row["is_cheapest"] = row.get("is_cheapest", "FALSE").upper() == "TRUE"
                try:
                    row["original_price"] = float(row.get("original_price", 0))
                except ValueError:
                    row["original_price"] = 0
                try:
                    row["converted_price_base"] = float(row.get("converted_price_base", 0))
                except ValueError:
                    row["converted_price_base"] = 0
                try:
                    row["stops"] = int(row.get("stops", 0))
                except ValueError:
                    row["stops"] = 0
                ref = row.get("search_date") or row.get("date", "")
                row["departure_tz_abbr"] = _tz_abbr(row.get("departure_timezone", ""), ref)
                row["arrival_tz_abbr"] = _tz_abbr(row.get("arrival_timezone", ""), ref)
                rows.append(row)
    except Exception:
        return []

    return rows


# ── App Lifecycle ─────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    os.makedirs(CSV_DIR, exist_ok=True)
    yield
    # Shutdown


app = FastAPI(
    title="Flight Price Comparison API",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow frontend on any domain to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Endpoints ─────────────────────────────────────────────
@app.get("/api/flights")
def get_flights(source: Optional[str] = Query(None)):
    """Return all flights, optionally filtered by source name."""
    all_flights = load_flights_from_csv()
    if source:
        all_flights = [f for f in all_flights if f["source_name"].lower() == source.lower()]
    return {"count": len(all_flights), "flights": all_flights}


@app.get("/api/sources")
def get_sources():
    """List all sources and how many flights each returned."""
    flights = load_flights_from_csv()
    source_counts = {}
    for f in flights:
        name = f["source_name"]
        source_counts[name] = source_counts.get(name, 0) + 1
    sources_list = [
        {"name": name, "flight_count": count, "active": count > 0}
        for name, count in sorted(source_counts.items(), key=lambda x: -x[1])
    ]
    return {"sources": sources_list, "total_sources": len(sources_list)}


@app.get("/api/stats")
def get_stats():
    """Return summary statistics."""
    flights = load_flights_from_csv()
    if not flights:
        return {"total_flights": 0, "cheapest": None, "sources": 0}

    cheapest = min(flights, key=lambda f: f["converted_price_base"])
    prices = [f["converted_price_base"] for f in flights if f["converted_price_base"] > 0]
    avg_price = sum(prices) / len(prices) if prices else 0
    sources = len(set(f["source_name"] for f in flights))

    return {
        "total_flights": len(flights),
        "active_sources": sources,
        "average_price": round(avg_price, 2),
        "currency": flights[0].get("base_currency", "EUR"),
        "cheapest": {
            "airline": cheapest["airline"],
            "price": cheapest["converted_price_base"],
            "currency": cheapest["base_currency"],
            "source": cheapest["source_name"],
        },
        "last_updated": flights[0].get("search_time", ""),
    }


@app.post("/api/search")
def run_search(req: SearchRequest):
    """Trigger a new search and return the results."""
    cmd = [sys.executable, str(SCRAPER_DIR / "main.py")]
    cmd += ["--origin", req.origin or config.DEFAULT_ORIGIN]
    cmd += ["--dest", req.destination or config.DEFAULT_DESTINATION]
    cmd += ["--date", req.date or config.DEFAULT_DATE]
    cmd += ["--cabin", req.cabin_class or config.DEFAULT_CABIN]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
            cwd=str(SCRAPER_DIR),
            env={**os.environ, "PYTHONPATH": str(SCRAPER_DIR)},
        )
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "message": "Search took too long (>3 min)"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

    flights = load_flights_from_csv()
    return {
        "status": "success",
        "flights_count": len(flights),
        "log": output[-2000:],
        "flights": flights[:50],
    }


@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.now().isoformat()}


# ── Run directly ──────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
