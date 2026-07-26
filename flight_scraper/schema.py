"""
Defines the common data format for all flight results.
Every source must return data in this format so we can compare them fairly.

WHY A COMMON SCHEMA?
- Different websites show different information
- Some show prices in GBP, some in USD, some in EUR
- Some call it "Economy", some call it "Coach"
- Some show direct flights, some show connecting flights
- This schema puts everything into ONE standard format
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class FlightData:
    """
    One flight result. Every source returns this same format.
    
    Think of this as a standard form that every website's data
    gets translated into, so we can compare apples to apples.
    """
    # --- Where this flight came from ---
    source_name: str                    # Which website provided this (e.g., "Kayak")
    
    # --- Route ---
    origin: str                         # Departure airport code (e.g., "MAN")
    destination: str                    # Arrival airport code (e.g., "FRA")
    departure_time: str                 # Local time at departure airport (e.g., "07:30")
    arrival_time: str                   # Local time at arrival airport (e.g., "10:15")
    departure_timezone: str             # Timezone of departure airport (e.g., "Europe/London")
    arrival_timezone: str               # Timezone of arrival airport (e.g., "Europe/Berlin")
    
    # --- Flight details ---
    airline: str                        # Airline name (e.g., "Lufthansa")
    flight_number: str                  # Flight number (e.g., "LH1234")
    stops: int                          # Number of stops (0 = direct, 1 = one stop, etc.)
    stop_airports: str                  # Airport codes where it stops (comma-separated, empty for direct)
    
    # --- Cabin class ---
    cabin_class: str                    # Normalized: "economy", "premium_economy", "business", "first"
    cabin_class_original: str           # Original name from source (e.g., "Coach", "Y Class", "Club")
    
    # --- Price ---
    original_price: float               # Price in the source's own currency
    original_currency: str              # Source's currency code (e.g., "GBP", "USD", "EUR")
    base_currency: str                  # Our standard comparison currency (e.g., "EUR")
    exchange_rate_used: float           # The exchange rate used to convert
    converted_price_base: float         # Price converted to base currency for fair comparison
    
    # --- Booking ---
    ticket_link: str                    # URL to book this flight (may be empty for some sources)
    
    # --- Optional extras ---
    baggage_info: Optional[str] = None  # Baggage allowance info (e.g., "1 x 23kg checked")
    fare_rules: Optional[str] = None    # Fare rules (e.g., "Non-refundable")
    
    # --- Search metadata ---
    search_time: str = ""               # When the search was performed
    search_date: str = ""               # The date that was searched
    is_cheapest: bool = False           # True if this is THE cheapest ticket across all sources


# CSV column headers in the order they appear in the CSV file
# This keeps the CSV organized and easy to read
CSV_COLUMNS = [
    "source_name",              # Which website
    "airline",                  # Airline name
    "flight_number",            # Flight number
    "origin",                   # From airport
    "destination",              # To airport
    "departure_time",           # Departure local time
    "arrival_time",             # Arrival local time
    "departure_timezone",       # Departure timezone
    "arrival_timezone",         # Arrival timezone
    "stops",                    # Number of stops
    "stop_airports",            # Stop airport codes
    "cabin_class",              # Normalized cabin class
    "cabin_class_original",     # Original cabin name
    "original_price",           # Price in original currency
    "original_currency",        # Original currency code
    "base_currency",            # Base currency for comparison
    "exchange_rate_used",       # Exchange rate applied
    "converted_price_base",     # Converted price
    "ticket_link",              # Booking URL
    "baggage_info",             # Baggage allowance
    "fare_rules",               # Fare rules
    "search_time",              # When searched
    "search_date",              # Date searched for
    "is_cheapest",              # Cheapest flag (TRUE/FALSE)
]
