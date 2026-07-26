"""
FLIGHT PRICE COMPARISON SYSTEM
================================
Compare flight prices across multiple sources.

HOW TO USE:
  1. Open a terminal / command prompt
  2. Navigate to the flight_scraper folder
  3. Run: python main.py
  4. Follow the prompts to search flights

WHAT HAPPENS:
  - You enter your origin, destination, date, and cabin class
  - The system searches ALL configured sources
  - Results are saved to output/flights.csv
  - The cheapest ticket is shown on screen
  - You can open the CSV in Excel or Google Sheets

EXAMPLES:
  python main.py                          # Uses defaults (MAN -> FRA)
  python main.py --origin LHR --destination JFK  # Custom route

HOW TO CUSTOMIZE:
  Edit config.py to change defaults, add API keys, or change settings
"""

import sys
import os

# Add the flight_scraper folder to Python's path
# This ensures all imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from sources import SourceManager
from currency import ExchangeRateFetcher
from csvwriter import FlightCSVWriter
from timeutils import get_current_timestamp


def validate_date(date_str):
    """Check the entered date is not in the past. Returns the date or None."""
    from datetime import datetime
    try:
        entered = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.now().astimezone().date()
        if entered < today:
            print(f"  [ERROR] '{date_str}' is in the past. Today is {today}.")
            print(f"  [ERROR] Flight APIs reject past dates. Please enter a future date.")
            return None
        return date_str
    except ValueError:
        print(f"  [ERROR] '{date_str}' is not a valid YYYY-MM-DD date.")
        return None


def get_user_input():
    """
    Get search parameters.

    Tries to ask the user interactively. If input is not available
    (piped mode, non-TTY), uses defaults from config.py.

    RETURNS:
    - (origin, destination, date, cabin_class)
    """
    # Try interactive mode first
    try:
        print(f"\n{'='*60}")
        print(f"  FLIGHT PRICE COMPARISON SYSTEM")
        print(f"{'='*60}")
        print(f"  Press Enter at any prompt to use the default value.")
        print(f"  Defaults are shown in [brackets].")
        print(f"{'='*60}\n")

        origin_input = input(f"  Origin airport [default: {config.DEFAULT_ORIGIN}]: ").strip().upper()
        origin = origin_input if origin_input else config.DEFAULT_ORIGIN

        dest_input = input(f"  Destination airport [default: {config.DEFAULT_DESTINATION}]: ").strip().upper()
        destination = dest_input if dest_input else config.DEFAULT_DESTINATION

        while True:
            date_input = input(f"  Travel date [default: {config.DEFAULT_DATE}] (YYYY-MM-DD): ").strip()
            date = date_input if date_input else config.DEFAULT_DATE
            if validate_date(date):
                break
            if not date_input:
                print(f"  Using default: {config.DEFAULT_DATE}")
                break

        cabin_input = input(f"  Cabin class [default: {config.DEFAULT_CABIN}] "
                            f"(economy/premium_economy/business/first): ").strip().lower()
        cabin_class = cabin_input if cabin_input else config.DEFAULT_CABIN

        valid_cabins = ["economy", "premium_economy", "business", "first"]
        if cabin_class not in valid_cabins:
            print(f"  [WARNING] '{cabin_class}' is not a standard cabin class.")
            print(f"  Valid options: {', '.join(valid_cabins)}")
            print(f"  Using: {config.DEFAULT_CABIN}")
            cabin_class = config.DEFAULT_CABIN

        return origin, destination, date, cabin_class

    except (EOFError, OSError):
        # Non-interactive mode — use defaults
        pass

    return (
        config.DEFAULT_ORIGIN,
        config.DEFAULT_DESTINATION,
        config.DEFAULT_DATE,
        config.DEFAULT_CABIN,
    )


def main():
    """
    Main program flow:
    
    1. Get user input (origin, destination, date, cabin class)
    2. Set up currency converter
    3. Create all sources
    4. Search all sources
    5. Convert currencies
    6. Write results to CSV
    7. Show summary
    """
    # STEP 1: Get what the user wants to search
    origin, destination, date, cabin_class = get_user_input()

    # STEP 2: Set up the currency converter
    # This will try to get live exchange rates, or use fallback
    print(f"\n  [CURRENCY] Initializing exchange rates...")
    currency_converter = ExchangeRateFetcher(base_currency=config.BASE_CURRENCY)
    currency_converter.load_rates()

    # STEP 3: Create the source manager
    # This creates all the sources (mock and optionally real APIs)
    print(f"\n  [SOURCES] Setting up flight data sources...")
    manager = SourceManager(currency_converter)

    # STEP 4: Search all sources
    search_time = get_current_timestamp()
    all_flights = manager.search_all(origin, destination, date, cabin_class)

    # STEP 5: Attach search timestamps
    for flight in all_flights:
        flight.search_time = search_time
        flight.search_date = date

    # STEP 6: Write results to CSV
    print(f"  [CSV] Saving results...")
    writer = FlightCSVWriter(
        output_dir=config.OUTPUT_DIR,
        filename=config.OUTPUT_FILE,
    )
    writer.write(all_flights, search_time, date)

    # STEP 7: Done!
    print(f"  Done! Open {config.OUTPUT_DIR}/{config.OUTPUT_FILE} to see all results.")
    print(f"  Run again to search a different route/date/cabin.\n")


# ============================================================
# ENTRY POINT
# ============================================================
# This is what runs when you type: python main.py
if __name__ == "__main__":
    main()
