"""
Time zone handling utilities.

HOW TIME WORKS IN FLIGHTS:
- Airports show times in their LOCAL time zone
- A flight departing Manchester at 07:30 is in UK time (GMT/BST)
- The same flight arriving Frankfurt at 10:15 is in German time (CET/CEST)
- That's a flight time of ~1h 45min, not 2h 45min, because the time difference
  between UK and Germany is usually 1 hour

INDUSTRY STANDARD:
- Departure time = local time at departure airport
- Arrival time = local time at arrival airport
- This is what you see on your ticket and boarding pass

WHAT WE DO:
- Store departure_time as local time at origin airport
- Store arrival_time as local time at destination airport
- Store timezone info for both airports
- This makes it easy to display in a consistent way
- A future dashboard can convert to any timezone if needed

TIMEZONE DATABASE:
- We use IANA timezone names (e.g., "Europe/London", "Europe/Berlin")
- These are standard names recognized by most software
- They automatically handle daylight saving time changes
"""

from datetime import datetime, timezone


# ============================================================
# AIRPORT TIMEZONE DATABASE
# ============================================================
# Format: IATA airport code -> (IANA timezone name, description)
#
# This tells us what timezone each airport is in.
# We list major European airports + common connecting hubs.
#
# NOTE: For a route like MAN -> FRA, both are European airports
# with well-defined timezones. This gets more complex for routes
# across continents, but the same principles apply.

AIRPORT_TIMEZONES = {
    # === UK Airports ===
    "MAN": ("Europe/London", "UK time"),
    "LHR": ("Europe/London", "UK time"),
    "LGW": ("Europe/London", "UK time"),
    "STN": ("Europe/London", "UK time"),
    "LTN": ("Europe/London", "UK time"),
    "BHX": ("Europe/London", "UK time"),
    "GLA": ("Europe/London", "UK time"),
    "EDI": ("Europe/London", "UK time"),
    "BFS": ("Europe/London", "UK time"),
    "DUB": ("Europe/Dublin", "Irish time"),

    # === German Airports ===
    "FRA": ("Europe/Berlin", "German time"),
    "MUC": ("Europe/Berlin", "German time"),
    "BER": ("Europe/Berlin", "German time"),
    "HAM": ("Europe/Berlin", "German time"),
    "STR": ("Europe/Berlin", "German time"),
    "CGN": ("Europe/Berlin", "German time"),
    "DUS": ("Europe/Berlin", "German time"),
    "TXL": ("Europe/Berlin", "German time"),  # Closed, kept for compatibility

    # === French Airports ===
    "CDG": ("Europe/Paris", "French time"),
    "ORY": ("Europe/Paris", "French time"),
    "NCE": ("Europe/Paris", "French time"),
    "LYS": ("Europe/Paris", "French time"),
    "MRS": ("Europe/Paris", "French time"),

    # === Benelux ===
    "AMS": ("Europe/Amsterdam", "Dutch time"),
    "EIN": ("Europe/Amsterdam", "Dutch time"),
    "BRU": ("Europe/Brussels", "Belgian time"),
    "CRL": ("Europe/Brussels", "Belgian time"),
    "LUX": ("Europe/Luxembourg", "Luxembourg time"),

    # === Swiss ===
    "ZRH": ("Europe/Zurich", "Swiss time"),
    "GVA": ("Europe/Geneva", "Swiss time"),
    "BSL": ("Europe/Zurich", "Swiss time"),

    # === Austrian ===
    "VIE": ("Europe/Vienna", "Austrian time"),
    "INN": ("Europe/Vienna", "Austrian time"),

    # === Nordic ===
    "CPH": ("Europe/Copenhagen", "Danish time"),
    "ARN": ("Europe/Stockholm", "Swedish time"),
    "OSL": ("Europe/Oslo", "Norwegian time"),
    "HEL": ("Europe/Helsinki", "Finnish time"),
    "BGO": ("Europe/Oslo", "Norwegian time"),
    "AAL": ("Europe/Copenhagen", "Danish time"),
    "GOT": ("Europe/Stockholm", "Swedish time"),

    # === Southern Europe ===
    "MAD": ("Europe/Madrid", "Spanish time"),
    "BCN": ("Europe/Barcelona", "Spanish time"),
    "AGP": ("Europe/Madrid", "Spanish time"),
    "PMI": ("Europe/Madrid", "Spanish time"),
    "FCO": ("Europe/Rome", "Italian time"),
    "MXP": ("Europe/Milan", "Italian time"),
    "LIN": ("Europe/Milan", "Italian time"),
    "VCE": ("Europe/Rome", "Italian time"),
    "LIS": ("Europe/Lisbon", "Portuguese time"),
    "OPO": ("Europe/Lisbon", "Portuguese time"),

    # === Central/Eastern Europe ===
    "WAW": ("Europe/Warsaw", "Polish time"),
    "KRK": ("Europe/Warsaw", "Polish time"),
    "PRG": ("Europe/Prague", "Czech time"),
    "BUD": ("Europe/Budapest", "Hungarian time"),
    "VIE": ("Europe/Vienna", "Austrian time"),
    "ZAG": ("Europe/Zagreb", "Croatian time"),
    "SOF": ("Europe/Sofia", "Bulgarian time"),
    "OTP": ("Europe/Bucharest", "Romanian time"),
    "ATH": ("Europe/Athens", "Greek time"),
    "SKG": ("Europe/Athens", "Greek time"),

    # === Turkey ===
    "IST": ("Europe/Istanbul", "Turkish time"),
    "SAW": ("Europe/Istanbul", "Turkish time"),
    "AYT": ("Europe/Istanbul", "Turkish time"),

    # === US & Canada ===
    "JFK": ("America/New_York", "US Eastern time"),
    "EWR": ("America/New_York", "US Eastern time"),
    "LGA": ("America/New_York", "US Eastern time"),
    "ORD": ("America/Chicago", "US Central time"),
    "MDW": ("America/Chicago", "US Central time"),
    "LAX": ("America/Los_Angeles", "US Pacific time"),
    "SFO": ("America/Los_Angeles", "US Pacific time"),
    "SEA": ("America/Los_Angeles", "US Pacific time"),
    "MIA": ("America/New_York", "US Eastern time"),
    "ATL": ("America/New_York", "US Eastern time"),
    "DFW": ("America/Chicago", "US Central time"),
    "IAH": ("America/Chicago", "US Central time"),
    "DEN": ("America/Denver", "US Mountain time"),
    "BOS": ("America/New_York", "US Eastern time"),
    "IAD": ("America/New_York", "US Eastern time"),
    "PHL": ("America/New_York", "US Eastern time"),
    "YYZ": ("America/Toronto", "Canadian Eastern time"),
    "YUL": ("America/Toronto", "Canadian Eastern time"),
    "YVR": ("America/Vancouver", "Canadian Pacific time"),

    # === Middle East ===
    "DXB": ("Asia/Dubai", "Gulf time"),
    "AUH": ("Asia/Dubai", "Gulf time"),
    "DOH": ("Asia/Qatar", "Gulf time"),
    "BAH": ("Asia/Qatar", "Gulf time"),
    "RUH": ("Asia/Riyadh", "Saudi time"),
    "JED": ("Asia/Riyadh", "Saudi time"),

    # === Asia ===
    "SIN": ("Asia/Singapore", "Singapore time"),
    "HKG": ("Asia/Hong_Kong", "Hong Kong time"),
    "NRT": ("Asia/Tokyo", "Japan time"),
    "HND": ("Asia/Tokyo", "Japan time"),
    "KIX": ("Asia/Tokyo", "Japan time"),
    "ICN": ("Asia/Seoul", "Korea time"),
    "BKK": ("Asia/Bangkok", "Thailand time"),
    "KUL": ("Asia/Kuala_Lumpur", "Malaysia time"),
    "DEL": ("Asia/Kolkata", "India time"),
    "BOM": ("Asia/Kolkata", "India time"),
    "PVG": ("Asia/Shanghai", "China time"),
    "PEK": ("Asia/Shanghai", "China time"),
    "HGH": ("Asia/Shanghai", "China time"),
    "CAN": ("Asia/Shanghai", "China time"),

    # === Oceania ===
    "SYD": ("Australia/Sydney", "Australian Eastern time"),
    "MEL": ("Australia/Sydney", "Australian Eastern time"),
    "BNE": ("Australia/Brisbane", "Australian Eastern time"),
    "PER": ("Australia/Perth", "Australian Western time"),
    "AKL": ("Pacific/Auckland", "New Zealand time"),
    "CHC": ("Pacific/Auckland", "New Zealand time"),
}


def get_airport_timezone(airport_code):
    """
    Look up the timezone for an airport.
    
    PARAMETERS:
    - airport_code: 3-letter IATA code (e.g., "MAN", "FRA")
    
    RETURNS:
    - (timezone_name, description)
    - Example: ("Europe/London", "UK time")
    - If airport not found, returns ("UTC", "UTC")
    """
    code = airport_code.upper()
    if code in AIRPORT_TIMEZONES:
        return AIRPORT_TIMEZONES[code]
    
    # If we don't know this airport, warn and return UTC
    print(f"  [TIME] Warning: Unknown timezone for airport '{airport_code}'")
    print(f"  [TIME] Defaulting to UTC. Add it to timeutils.py if needed.")
    return ("UTC", "UTC time")


def get_current_timestamp():
    """
    Get the current local time as a formatted string.
    Used to record when the search was performed.
    
    RETURNS:
    - String like "2025-06-15 14:30:00"
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_current_utc_timestamp():
    """
    Get the current UTC time as a formatted string.
    
    RETURNS:
    - String like "2025-06-15 13:30:00 UTC"
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
