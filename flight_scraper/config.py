"""
Configuration settings for the flight price comparison system.
Change these to customize how the system works.

HOW TO USE:
1. Open this file in any text editor
2. Change DEFAULT_ORIGIN and DEFAULT_DESTINATION to search different routes
3. Change DEFAULT_DATE to search a different date
4. Change DEFAULT_CABIN to search different cabin types
5. To add real API sources, set ENABLE_* to True and add your API keys
"""

import os
from datetime import datetime

# ============================================================
# ROUTE SETTINGS - Change these to search different routes
# ============================================================
DEFAULT_ORIGIN = "MAN"           # Departure airport (IATA code, e.g., "MAN" for Manchester)
DEFAULT_DESTINATION = "FRA"      # Arrival airport (IATA code, e.g., "FRA" for Frankfurt)
DEFAULT_DATE = datetime.now().strftime("%Y-%m-%d")  # Defaults to today's date (computed at import time)
DEFAULT_CABIN = "economy"        # Options: economy, premium_economy, business, first

# ============================================================
# CURRENCY SETTINGS
# ============================================================
BASE_CURRENCY = "EUR"            # All prices are converted to this for fair comparison

# ============================================================
# MOCK SOURCE SETTINGS
# ============================================================
# Mock sources work WITHOUT any API keys.
# They generate realistic-looking flight data to test the system.
MOCK_SOURCE_COUNT = 0            # Set to 0 to disable mock data. Use 1-10 for testing.

# ============================================================
# REAL API SOURCE SETTINGS (OPTIONAL)
# ============================================================
# These are OPTIONAL. You can run the system with just mock sources.
# To use real sources, you need to register for free API keys.
# All registrations below are free and do NOT require a credit card.

ENABLE_IGNV = True               # Enabled - your API key is set below
ENABLE_AVIATIONSTACK = True      # Enabled - your API key is set below (limited: real-time only, no prices)
ENABLE_KIWI = False              # Kiwi.com Tequila - invitation only since May 2024

# ============================================================
# NEW REAL API SOURCES (no API keys required!)
# ============================================================
# These sources use reverse-engineered or public APIs.
# They work out of the box — no registration needed.

ENABLE_GOOGLE_FLIGHTS = True     # Google Flights via reverse-engineered Protobuf API (fast-flights)
ENABLE_RYANAIR = True            # Ryanair public API (may return 0 for routes Ryanair doesn't fly)
ENABLE_WHENTOFLY = True          # WhentoFly.io - free flight API, no signup required
ENABLE_OCTOTRIP = True           # OctoTrip.app - free MCP flight search API, no login required

# ============================================================
# PLAYWRIGHT SCRAPERS (best-effort, anti-bot dependent)
# ============================================================
# These attempt to scrape flight websites using Playwright/requests.
# Major travel sites use anti-bot protection, so these may return
# empty results. They fail gracefully if blocked.

ENABLE_KAYAK = True              # Kayak (anti-bot: high)
ENABLE_SKYSCANNER = True         # Skyscanner (anti-bot: high)
ENABLE_EXPEDIA = True            # Expedia (anti-bot: high)
ENABLE_MOMONDO = True            # Momondo (anti-bot: high, same as Kayak)

# API Keys - Get these for free (no credit card needed):
# Ignav:      https://ignav.com              (1,000 free requests, then $2/1,000)
# AviationStack: https://aviationstack.com   (Free plan, 500 requests/month)
# Kiwi.com:   https://tequila.kiwi.com       (Sign up for free)
IGNV_API_KEY = "ignav_z5l3BhaVG4BaLrgRpMWEymZZJp1RSjBX"
AVIATIONSTACK_API_KEY = "54124322f9467f701205356900827818"
KIWI_API_KEY = os.environ.get("KIWI_API_KEY", "")

# ============================================================
# OUTPUT SETTINGS
# ============================================================
OUTPUT_DIR = "output"            # Folder where the CSV file is saved
OUTPUT_FILE = "flights_latest.csv"  # Overwritten each run (renamed to avoid lock conflicts)
