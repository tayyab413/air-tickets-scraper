"""
CSV writing utilities.
Saves all flight data into one CSV file.

HOW THE CSV WORKS:
- One file: output/flights.csv
- Overwritten every time you run the program
- Sorted by price (cheapest first)
- The cheapest ticket is marked with is_cheapest = TRUE
- All columns are consistent (same headers every time)

WHY CSV?
- CSV = Comma Separated Values
- Opens in Excel, Google Sheets, or any text editor
- Easy to read programmatically for a future dashboard
- Standard format that everyone understands
"""

import csv
import os
import tempfile
import shutil

from schema import CSV_COLUMNS


class FlightCSVWriter:
    """
    Handles all CSV file operations.
    
    RESPONSIBILITIES:
    1. Sort flights by converted price (cheapest first)
    2. Mark the absolute cheapest ticket
    3. Write all flights to flights.csv
    4. Overwrite the file (never append)
    """

    def __init__(self, output_dir="output", filename="flights.csv"):
        self.output_dir = output_dir
        self.filename = filename
        self.filepath = os.path.join(output_dir, filename)

        # Create the output folder if it doesn't exist yet
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"  [CSV] Created output folder: {output_dir}/")

    def write(self, flights, search_time, search_date):
        """
        Write all flights to the CSV file.
        
        STEPS:
        1. Sort flights by converted price (cheapest first)
        2. Mark the cheapest flight with is_cheapest = True
        3. Open the CSV file for writing (this overwrites!)
        4. Write header row (column names)
        5. Write one row per flight
        6. Print summary
        
        PARAMETERS:
        - flights: list of FlightData objects
        - search_time: when the search was performed
        - search_date: the date that was searched
        """
        if not flights:
            print("  [CSV] WARNING: No flights to save. CSV file will be empty.")
            return

        # Step 1: Sort by converted price (cheapest FIRST)
        sorted_flights = sorted(flights, key=lambda f: f.converted_price_base)

        # Step 2: Mark the cheapest ticket
        cheapest = sorted_flights[0]
        cheapest.is_cheapest = True

        # Write to CSV (try direct, fallback to new filename if locked)
        from datetime import datetime as _dt

        def write_csv(filepath):
            with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=CSV_COLUMNS)
                writer.writeheader()
                for flight in sorted_flights:
                    row = {
                        "source_name": flight.source_name,
                        "airline": flight.airline,
                        "flight_number": flight.flight_number,
                        "origin": flight.origin,
                        "destination": flight.destination,
                        "departure_time": flight.departure_time,
                        "arrival_time": flight.arrival_time,
                        "departure_timezone": flight.departure_timezone,
                        "arrival_timezone": flight.arrival_timezone,
                        "stops": flight.stops,
                        "stop_airports": flight.stop_airports,
                        "cabin_class": flight.cabin_class,
                        "cabin_class_original": flight.cabin_class_original,
                        "original_price": flight.original_price,
                        "original_currency": flight.original_currency,
                        "base_currency": flight.base_currency,
                        "exchange_rate_used": flight.exchange_rate_used,
                        "converted_price_base": flight.converted_price_base,
                        "ticket_link": flight.ticket_link,
                        "baggage_info": flight.baggage_info or "",
                        "fare_rules": flight.fare_rules or "",
                        "search_time": flight.search_time or search_time,
                        "search_date": flight.search_date or search_date,
                        "is_cheapest": "TRUE" if flight.is_cheapest else "FALSE",
                    }
                    writer.writerow(row)

        try:
            write_csv(self.filepath)
        except PermissionError:
            fallback = os.path.join(self.output_dir, f"flights_latest_{_dt.now().strftime('%Y%m%d_%H%M%S')}.csv")
            write_csv(fallback)
            print(f"  [CSV] Output file is locked by another program.")
            print(f"  [CSV] Saved to: {fallback}")
            self.filepath = fallback

        # Print summary
        cheapest_airline = cheapest.airline
        cheapest_flight = cheapest.flight_number
        cheapest_price_orig = f"{cheapest.original_currency} {cheapest.original_price:.2f}"
        cheapest_price_base = f"{cheapest.base_currency} {cheapest.converted_price_base:.2f}"

        print(f"\n{'='*60}")
        print(f"  SUMMARY")
        print(f"{'='*60}")
        print(f"  Total flights found: {len(sorted_flights)}")
        print(f"  From sources: {len(set(f.source_name for f in sorted_flights))}")
        print(f"  Saved to:      {self.filepath}")
        print(f"")
        print(f"  *** CHEAPEST TICKET ***")
        print(f"     Airline:     {cheapest_airline} ({cheapest_flight})")
        print(f"     From:        {cheapest.origin} -> {cheapest.destination}")
        print(f"     Departure:   {cheapest.departure_time}")
        print(f"     Arrival:     {cheapest.arrival_time}")
        print(f"     Stops:       {cheapest.stops}")
        print(f"     Cabin:       {cheapest.cabin_class}")
        print(f"     Price:       {cheapest_price_orig}")
        print(f"     Converted:   {cheapest_price_base}")
        print(f"     Source:      {cheapest.source_name}")
        print(f"{'='*60}\n")

    def read_all(self):
        """
        Read all flights back from the CSV file.
        Useful for a future dashboard to load the data.
        
        RETURNS:
        - List of dictionaries (each dict = one flight row)
        - Empty list if file doesn't exist
        """
        if not os.path.exists(self.filepath):
            print(f"  [CSV] No file found at {self.filepath}")
            return []

        flights = []
        with open(self.filepath, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                flights.append(row)

        print(f"  [CSV] Read {len(flights)} flights from {self.filepath}")
        return flights
