"""
Flight data sources - both mock and real.

ARCHITECTURE:
Every source is a class that has one job: "get me flights for this route/date/cabin".
Each source returns a list of FlightData objects in our standard format.

MOCK SOURCES (10 total):
These generate realistic flight data WITHOUT any API keys.
They simulate what real flight websites would return.
Each one uses different currencies, cabin names, and price patterns.

REAL SOURCES (optional):
- Amadeus API: Real flight search API (needs free API key)
- AviationStack API: Flight schedules (needs free API key)
- Kiwi.com API: Flight search (needs free API key)

HOW TO ADD A NEW SOURCE:
1. Create a new class that extends BaseSource
2. Implement the search() method
3. Add it to the SOURCES list at the bottom
4. Return FlightData objects in our standard format

ERROR HANDLING:
Each source is wrapped in a try/except block.
If one source fails, it doesn't stop the others.
Failed sources are reported but don't crash the program.
"""

import random
from datetime import datetime
from schema import FlightData
from timeutils import get_airport_timezone
import config as cfg


# ============================================================
# SECTION 1: BASE SOURCE CLASS
# ============================================================

class BaseSource:
    """
    Every source inherits from this class.
    This ensures all sources have the same structure.
    
    To create a new source, you just need to:
    1. Write a class that extends BaseSource
    2. Set the source_name
    3. Implement the search() method
    """

    def __init__(self):
        self.source_name = "base_source"
        self._flights = []

    def search(self, origin, destination, date, cabin_class, currency_converter):
        """
        Search for flights.

        PARAMETERS:
        - origin: IATA code (e.g., "MAN")
        - destination: IATA code (e.g., "FRA")
        - date: date string (e.g., "2025-06-15")
        - cabin_class: one of "economy", "premium_economy", "business", "first"
        - currency_converter: ExchangeRateFetcher instance

        RETURNS:
        - List of FlightData objects
        - Empty list if no flights found or if an error occurs
        """
        raise NotImplementedError("Each source must implement its own search method")

    def name(self):
        """Return the human-readable name of this source."""
        return self.source_name


# ============================================================
# SECTION 2: MOCK SOURCES (10 sources, no API keys needed)
# ============================================================
#
# Each mock source generates realistic flights for MAN->FRA.
# They simulate different types of travel websites:
#
# Source 1: AirlineDirect   - Booking direct with British Airways (GBP)
# Source 2: AggregatorOne   - Like Skyscanner (USD)
# Source 3: AirlineGerman   - Lufthansa direct booking (EUR)
# Source 4: BudgetAir       - Budget airline like Ryanair (EUR)
# Source 5: OTAPremium      - Premium OTA like Expedia (USD)
# Source 6: MetaSearch      - Like Kayak (USD)
# Source 7: AirlinePartner  - Partner/Alliance flights (EUR)
# Source 8: CorporateTravel - Business travel agency (GBP)
# Source 9: LastMinuteDeals - Last minute deals (GBP)
# Source 10: MultiStop      - Multi-stop specialists (EUR)
#

class MockSource_01_AirlineDirect(BaseSource):
    """
    Simulates booking directly with a full-service airline (British Airways).
    Prices in GBP. Uses British cabin naming conventions.
    """
    def __init__(self):
        super().__init__()
        self.source_name = "AirlineDirect (British Airways)"

    def search(self, origin, destination, date, cabin_class, currency_converter):
        results = []

        # Define mock flights
        mock_flights = [
            {
                "airline": "British Airways",
                "flight_number": "BA1390",
                "stops": 0,
                "stop_airports": "",
                "departure_time": "07:15",
                "arrival_time": "10:00",
                "base_price_eur": 145,
            },
            {
                "airline": "British Airways",
                "flight_number": "BA1392",
                "stops": 0,
                "stop_airports": "",
                "departure_time": "11:30",
                "arrival_time": "14:15",
                "base_price_eur": 165,
            },
            {
                "airline": "British Airways",
                "flight_number": "BA1386",
                "stops": 0,
                "stop_airports": "",
                "departure_time": "16:45",
                "arrival_time": "19:30",
                "base_price_eur": 155,
            },
            {
                "airline": "British Airways",
                "flight_number": "BA1388",
                "stops": 0,
                "stop_airports": "",
                "departure_time": "20:00",
                "arrival_time": "22:45",
                "base_price_eur": 135,
            },
        ]

        # Cabin class mapping
        cabin_map = {
            "economy": ("Economy", 1.0),
            "premium_economy": ("World Traveller Plus", 1.7),
            "business": ("Club Europe", 3.5),
            "first": ("First", 5.0),
        }

        original_currency = "GBP"
        orig_cabin_label, price_multiplier = cabin_map.get(cabin_class, ("Economy", 1.0))

        for f in mock_flights:
            # Price variation based on time of day
            hour = int(f["departure_time"].split(":")[0])
            if hour < 8 or hour > 19:
                time_factor = 0.9  # Early morning / late night - cheaper
            elif 10 <= hour <= 14:
                time_factor = 1.15  # Midday - more expensive
            else:
                time_factor = 1.0

            # Calculate price in EUR, then convert to source currency
            price_eur = f["base_price_eur"] * price_multiplier * time_factor
            # Add slight randomness
            price_eur += random.uniform(-5, 10)

            # Convert EUR to GBP using the inverse logic
            # If 1 EUR = 0.86 GBP, then price_eur EUR = price_eur * 0.86 GBP
            rate = currency_converter.rates.get("GBP", 0.86)
            price_gbp = round(price_eur * rate, 2)

            # Convert GBP back to EUR for comparison
            converted_price, used_rate = currency_converter.convert(price_gbp, original_currency)

            dep_tz = get_airport_timezone(origin)
            arr_tz = get_airport_timezone(destination)

            ticket_link = f"https://www.britishairways.com/book/{f['flight_number']}/{date}"

            flight = FlightData(
                source_name=self.source_name,
                origin=origin,
                destination=destination,
                departure_time=f["departure_time"],
                arrival_time=f["arrival_time"],
                departure_timezone=dep_tz[0],
                arrival_timezone=arr_tz[0],
                airline=f["airline"],
                flight_number=f["flight_number"],
                stops=f["stops"],
                stop_airports=f["stop_airports"],
                cabin_class=cabin_class,
                cabin_class_original=orig_cabin_label,
                original_price=price_gbp,
                original_currency=original_currency,
                base_currency=cfg.BASE_CURRENCY,
                exchange_rate_used=used_rate,
                converted_price_base=converted_price,
                ticket_link=ticket_link,
                baggage_info="1 x 23kg checked bag included",
                fare_rules="Free changes up to 24h before departure",
                search_time="",
                search_date=date,
                is_cheapest=False,
            )
            results.append(flight)

        return results


class MockSource_02_AggregatorOne(BaseSource):
    """
    Simulates an aggregator like Skyscanner.
    Returns results in USD. Shows multiple airlines.
    """
    def __init__(self):
        super().__init__()
        self.source_name = "Aggregator (SkySearch)"

    def search(self, origin, destination, date, cabin_class, currency_converter):
        results = []

        mock_flights = [
            {
                "airline": "Lufthansa", "flight_number": "LH941",
                "stops": 0, "stop_airports": "",
                "departure_time": "06:30", "arrival_time": "09:15",
                "base_price_eur": 120
            },
            {
                "airline": "Eurowings", "flight_number": "EW9882",
                "stops": 0, "stop_airports": "",
                "departure_time": "08:00", "arrival_time": "10:40",
                "base_price_eur": 95
            },
            {
                "airline": "Brussels Airlines", "flight_number": "SN2572",
                "stops": 1, "stop_airports": "BRU",
                "departure_time": "07:00", "arrival_time": "10:30",
                "base_price_eur": 110
            },
            {
                "airline": "KLM", "flight_number": "KL1080",
                "stops": 1, "stop_airports": "AMS",
                "departure_time": "09:15", "arrival_time": "12:45",
                "base_price_eur": 130
            },
            {
                "airline": "Air France", "flight_number": "AF1069",
                "stops": 1, "stop_airports": "CDG",
                "departure_time": "14:00", "arrival_time": "17:45",
                "base_price_eur": 145
            },
        ]

        cabin_map = {
            "economy": ("Economy", 1.0),
            "premium_economy": ("Premium Economy", 1.8),
            "business": ("Business", 3.0),
            "first": ("First", 5.5),
        }

        original_currency = "USD"
        orig_cabin_label, price_multiplier = cabin_map.get(cabin_class, ("Economy", 1.0))

        for f in mock_flights:
            # Multi-stop discount/premium
            stop_factor = 1.0 + (f["stops"] * 0.05)  # 5% more per stop

            price_eur = f["base_price_eur"] * price_multiplier * stop_factor
            price_eur += random.uniform(-8, 12)

            # EUR -> USD
            rate = currency_converter.rates.get("USD", 1.08)
            price_usd = round(price_eur * rate, 2)

            converted_price, used_rate = currency_converter.convert(price_usd, original_currency)

            dep_tz = get_airport_timezone(origin)
            arr_tz = get_airport_timezone(destination)

            # Build stop airports string
            stop_str = ", ".join([f["stop_airports"]]) if f["stop_airports"] else ""

            flight = FlightData(
                source_name=self.source_name,
                origin=origin,
                destination=destination,
                departure_time=f["departure_time"],
                arrival_time=f["arrival_time"],
                departure_timezone=dep_tz[0],
                arrival_timezone=arr_tz[0],
                airline=f["airline"],
                flight_number=f["flight_number"],
                stops=f["stops"],
                stop_airports=stop_str,
                cabin_class=cabin_class,
                cabin_class_original=orig_cabin_label,
                original_price=price_usd,
                original_currency=original_currency,
                base_currency=cfg.BASE_CURRENCY,
                exchange_rate_used=used_rate,
                converted_price_base=converted_price,
                ticket_link=f"https://www.skysearch.net/flights/{origin}-{destination}/{date}/{f['flight_number']}",
                baggage_info="Check with airline",
                fare_rules="Varies by airline",
                search_time="",
                search_date=date,
                is_cheapest=False,
            )
            results.append(flight)

        return results


class MockSource_03_AirlineGerman(BaseSource):
    """
    Simulates Lufthansa direct booking. Prices in EUR.
    German cabin naming conventions.
    """
    def __init__(self):
        super().__init__()
        self.source_name = "Airline German (Lufthansa)"

    def search(self, origin, destination, date, cabin_class, currency_converter):
        results = []

        mock_flights = [
            {"airline": "Lufthansa", "flight_number": "LH941",
             "stops": 0, "stop_airports": "",
             "departure_time": "06:30", "arrival_time": "09:15", "base_price_eur": 130},
            {"airline": "Lufthansa", "flight_number": "LH943",
             "stops": 0, "stop_airports": "",
             "departure_time": "10:00", "arrival_time": "12:45", "base_price_eur": 150},
            {"airline": "Lufthansa", "flight_number": "LH945",
             "stops": 0, "stop_airports": "",
             "departure_time": "14:30", "arrival_time": "17:15", "base_price_eur": 140},
            {"airline": "Lufthansa", "flight_number": "LH947",
             "stops": 0, "stop_airports": "",
             "departure_time": "18:00", "arrival_time": "20:45", "base_price_eur": 125},
            {"airline": "Lufthansa", "flight_number": "LH949",
             "stops": 0, "stop_airports": "",
             "departure_time": "21:15", "arrival_time": "23:55", "base_price_eur": 110},
        ]

        cabin_map = {
            "economy": ("Economy Class", 1.0),
            "premium_economy": ("Premium Economy Class", 1.6),
            "business": ("Business Class", 3.2),
            "first": ("First Class", 5.0),
        }

        original_currency = "EUR"
        orig_cabin_label, price_multiplier = cabin_map.get(cabin_class, ("Economy Class", 1.0))

        for f in mock_flights:
            price_eur = f["base_price_eur"] * price_multiplier
            price_eur += random.uniform(-3, 8)

            # No conversion needed since already in EUR
            converted_price, used_rate = currency_converter.convert(price_eur, "EUR")

            dep_tz = get_airport_timezone(origin)
            arr_tz = get_airport_timezone(destination)

            flight = FlightData(
                source_name=self.source_name,
                origin=origin,
                destination=destination,
                departure_time=f["departure_time"],
                arrival_time=f["arrival_time"],
                departure_timezone=dep_tz[0],
                arrival_timezone=arr_tz[0],
                airline=f["airline"],
                flight_number=f["flight_number"],
                stops=f["stops"],
                stop_airports=f["stop_airports"],
                cabin_class=cabin_class,
                cabin_class_original=orig_cabin_label,
                original_price=price_eur,
                original_currency=original_currency,
                base_currency=cfg.BASE_CURRENCY,
                exchange_rate_used=used_rate,
                converted_price_base=converted_price,
                ticket_link=f"https://www.lufthansa.com/book/{f['flight_number']}/{date}",
                baggage_info="1 x 23kg checked bag",
                fare_rules="Flexible fares available",
                search_time="",
                search_date=date,
                is_cheapest=False,
            )
            results.append(flight)

        return results


class MockSource_04_BudgetAir(BaseSource):
    """
    Simulates a budget airline (Ryanair-style). EUR prices.
    Only offers Economy. Extra fees for everything.
    Uses different cabin naming.
    """
    def __init__(self):
        super().__init__()
        self.source_name = "Budget Air (EconomyFly)"

    def search(self, origin, destination, date, cabin_class, currency_converter):
        results = []

        mock_flights = [
            {"airline": "EconomyFly", "flight_number": "EF001",
             "stops": 0, "stop_airports": "",
             "departure_time": "06:00", "arrival_time": "08:50", "base_price_eur": 45},
            {"airline": "EconomyFly", "flight_number": "EF002",
             "stops": 0, "stop_airports": "",
             "departure_time": "12:30", "arrival_time": "15:20", "base_price_eur": 55},
            {"airline": "EconomyFly", "flight_number": "EF003",
             "stops": 0, "stop_airports": "",
             "departure_time": "18:45", "arrival_time": "21:35", "base_price_eur": 40},
            {"airline": "EconomyFly", "flight_number": "EF004",
             "stops": 0, "stop_airports": "",
             "departure_time": "22:00", "arrival_time": "00:50", "base_price_eur": 35},
        ]

        # Budget airlines only sell Economy (with optional extras)
        if cabin_class == "economy":
            orig_cabin_label = "Standard"
            price_multiplier = 1.0
        elif cabin_class == "premium_economy":
            orig_cabin_label = "Plus"
            price_multiplier = 1.0  # Same seats, just different extras
        else:
            # No business/first on budget airlines
            return results  # Return empty

        original_currency = "EUR"

        for f in mock_flights:
            # Late night flights are cheaper
            hour = int(f["departure_time"].split(":")[0])
            if hour >= 22 or hour < 7:
                night_factor = 0.85
            else:
                night_factor = 1.0

            price_eur = f["base_price_eur"] * price_multiplier * night_factor
            price_eur += random.uniform(-2, 5)

            converted_price, used_rate = currency_converter.convert(price_eur, "EUR")

            dep_tz = get_airport_timezone(origin)
            arr_tz = get_airport_timezone(destination)

            flight = FlightData(
                source_name=self.source_name,
                origin=origin,
                destination=destination,
                departure_time=f["departure_time"],
                arrival_time=f["arrival_time"],
                departure_timezone=dep_tz[0],
                arrival_timezone=arr_tz[0],
                airline=f["airline"],
                flight_number=f["flight_number"],
                stops=f["stops"],
                stop_airports=f["stop_airports"],
                cabin_class=cabin_class,
                cabin_class_original=orig_cabin_label,
                original_price=price_eur,
                original_currency=original_currency,
                base_currency=cfg.BASE_CURRENCY,
                exchange_rate_used=used_rate,
                converted_price_base=converted_price,
                ticket_link=f"https://www.economyfly.com/book/{f['flight_number']}/{date}",
                baggage_info="No checked bag included (from EUR 15 extra)",
                fare_rules="Non-refundable. Change fee: EUR 50",
                search_time="",
                search_date=date,
                is_cheapest=False,
            )
            results.append(flight)

        return results


class MockSource_05_OTAPremium(BaseSource):
    """
    Simulates a premium OTA like Expedia. USD prices.
    Offers all cabin classes with typical OTA naming.
    """
    def __init__(self):
        super().__init__()
        self.source_name = "OTA Premium (TravelPlus)"

    def search(self, origin, destination, date, cabin_class, currency_converter):
        results = []

        mock_flights = [
            {"airline": "Lufthansa", "flight_number": "LH943",
             "stops": 0, "stop_airports": "",
             "departure_time": "10:00", "arrival_time": "12:45", "base_price_eur": 155},
            {"airline": "British Airways", "flight_number": "BA1392",
             "stops": 0, "stop_airports": "",
             "departure_time": "11:30", "arrival_time": "14:15", "base_price_eur": 160},
            {"airline": "Swiss", "flight_number": "LX8111",
             "stops": 1, "stop_airports": "ZRH",
             "departure_time": "08:15", "arrival_time": "10:30", "base_price_eur": 140},
            {"airline": "Austrian Airlines", "flight_number": "OS5811",
             "stops": 1, "stop_airports": "VIE",
             "departure_time": "15:00", "arrival_time": "17:30", "base_price_eur": 148},
        ]

        cabin_map = {
            "economy": ("Economy", 1.0),
            "premium_economy": ("Premium", 1.75),
            "business": ("Business", 3.3),
            "first": ("First", 5.2),
        }

        original_currency = "USD"
        orig_cabin_label, price_multiplier = cabin_map.get(cabin_class, ("Economy", 1.0))

        for f in mock_flights:
            # OTA adds a booking fee
            ota_fee = random.uniform(5, 15)
            price_eur = f["base_price_eur"] * price_multiplier + ota_fee
            price_eur += random.uniform(-5, 10)

            rate = currency_converter.rates.get("USD", 1.08)
            price_usd = round(price_eur * rate, 2)

            converted_price, used_rate = currency_converter.convert(price_usd, "USD")

            dep_tz = get_airport_timezone(origin)
            arr_tz = get_airport_timezone(destination)

            flight = FlightData(
                source_name=self.source_name,
                origin=origin,
                destination=destination,
                departure_time=f["departure_time"],
                arrival_time=f["arrival_time"],
                departure_timezone=dep_tz[0],
                arrival_timezone=arr_tz[0],
                airline=f["airline"],
                flight_number=f["flight_number"],
                stops=f["stops"],
                stop_airports=f["stop_airports"] if f["stop_airports"] else "",
                cabin_class=cabin_class,
                cabin_class_original=orig_cabin_label,
                original_price=price_usd,
                original_currency=original_currency,
                base_currency=cfg.BASE_CURRENCY,
                exchange_rate_used=used_rate,
                converted_price_base=converted_price,
                ticket_link=f"https://www.travelplus.com/deals/{origin}-{destination}/{date}/{f['flight_number']}",
                baggage_info="Varies by fare. Check at booking.",
                fare_rules="24-hour cancellation policy",
                search_time="",
                search_date=date,
                is_cheapest=False,
            )
            results.append(flight)

        return results


class MockSource_06_MetaSearch(BaseSource):
    """
    Simulates a meta-search engine like Kayak. USD prices.
    Shows results from multiple airlines with "compare" links.
    """
    def __init__(self):
        super().__init__()
        self.source_name = "Meta Search (Kayak-style)"

    def search(self, origin, destination, date, cabin_class, currency_converter):
        results = []

        mock_flights = [
            {"airline": "Lufthansa", "flight_number": "LH941",
             "stops": 0, "stop_airports": "",
             "departure_time": "06:30", "arrival_time": "09:15", "base_price_eur": 125},
            {"airline": "British Airways", "flight_number": "BA1390",
             "stops": 0, "stop_airports": "",
             "departure_time": "07:15", "arrival_time": "10:00", "base_price_eur": 140},
            {"airline": "Air France", "flight_number": "AF1569",
             "stops": 1, "stop_airports": "CDG",
             "departure_time": "11:00", "arrival_time": "14:30", "base_price_eur": 115},
            {"airline": "KLM", "flight_number": "KL1078",
             "stops": 1, "stop_airports": "AMS",
             "departure_time": "06:00", "arrival_time": "09:30", "base_price_eur": 108},
            {"airline": "Eurowings", "flight_number": "EW9880",
             "stops": 0, "stop_airports": "",
             "departure_time": "15:00", "arrival_time": "17:40", "base_price_eur": 85},
        ]

        cabin_map = {
            "economy": ("Economy / Coach", 1.0),
            "premium_economy": ("Premium Economy", 1.65),
            "business": ("Business / Club", 3.1),
            "first": ("First / Suite", 5.3),
        }

        original_currency = "USD"
        orig_cabin_label, price_multiplier = cabin_map.get(cabin_class, ("Economy", 1.0))

        for f in mock_flights:
            price_eur = f["base_price_eur"] * price_multiplier
            price_eur += random.uniform(-10, 15)

            rate = currency_converter.rates.get("USD", 1.08)
            price_usd = round(price_eur * rate, 2)

            converted_price, used_rate = currency_converter.convert(price_usd, "USD")

            dep_tz = get_airport_timezone(origin)
            arr_tz = get_airport_timezone(destination)

            flight = FlightData(
                source_name=self.source_name,
                origin=origin,
                destination=destination,
                departure_time=f["departure_time"],
                arrival_time=f["arrival_time"],
                departure_timezone=dep_tz[0],
                arrival_timezone=arr_tz[0],
                airline=f["airline"],
                flight_number=f["flight_number"],
                stops=f["stops"],
                stop_airports=f["stop_airports"] if f["stop_airports"] else "",
                cabin_class=cabin_class,
                cabin_class_original=orig_cabin_label,
                original_price=price_usd,
                original_currency=original_currency,
                base_currency=cfg.BASE_CURRENCY,
                exchange_rate_used=used_rate,
                converted_price_base=converted_price,
                ticket_link=f"https://www.flightfinder.com/redirect/{f['airline']}/{f['flight_number']}/{date}",
                baggage_info="Check airline policy",
                fare_rules="Price is an estimate. Final price at booking.",
                search_time="",
                search_date=date,
                is_cheapest=False,
            )
            results.append(flight)

        return results


class MockSource_07_AirlinePartner(BaseSource):
    """
    Simulates Star Alliance partner network. EUR prices.
    Shows codeshare and partner flights.
    """
    def __init__(self):
        super().__init__()
        self.source_name = "Airline Partner (Star Alliance)"

    def search(self, origin, destination, date, cabin_class, currency_converter):
        results = []

        mock_flights = [
            {"airline": "Lufthansa (operated by CityLine)", "flight_number": "LH9415",
             "stops": 0, "stop_airports": "",
             "departure_time": "06:30", "arrival_time": "09:15", "base_price_eur": 135},
            {"airline": "SAS", "flight_number": "SK2613",
             "stops": 1, "stop_airports": "CPH",
             "departure_time": "09:00", "arrival_time": "12:15", "base_price_eur": 118},
            {"airline": "TAP Air Portugal", "flight_number": "TP1347",
             "stops": 1, "stop_airports": "LIS",
             "departure_time": "07:45", "arrival_time": "11:00", "base_price_eur": 125},
            {"airline": "LOT Polish Airlines", "flight_number": "LO3821",
             "stops": 1, "stop_airports": "WAW",
             "departure_time": "13:00", "arrival_time": "16:15", "base_price_eur": 105},
            {"airline": "Brussels Airlines", "flight_number": "SN2572",
             "stops": 1, "stop_airports": "BRU",
             "departure_time": "07:00", "arrival_time": "10:30", "base_price_eur": 112},
        ]

        cabin_map = {
            "economy": ("Economy (Y)", 1.0),
            "premium_economy": ("Premium (W)", 1.6),
            "business": ("Business (C)", 3.0),
            "first": ("First (F)", 4.8),
        }

        original_currency = "EUR"
        orig_cabin_label, price_multiplier = cabin_map.get(cabin_class, ("Economy", 1.0))

        for f in mock_flights:
            # Partner flights may have a slight premium
            partner_fee = random.uniform(2, 8)
            price_eur = f["base_price_eur"] * price_multiplier + partner_fee
            price_eur += random.uniform(-3, 10)

            converted_price, used_rate = currency_converter.convert(price_eur, "EUR")

            dep_tz = get_airport_timezone(origin)
            arr_tz = get_airport_timezone(destination)

            flight = FlightData(
                source_name=self.source_name,
                origin=origin,
                destination=destination,
                departure_time=f["departure_time"],
                arrival_time=f["arrival_time"],
                departure_timezone=dep_tz[0],
                arrival_timezone=arr_tz[0],
                airline=f["airline"],
                flight_number=f["flight_number"],
                stops=f["stops"],
                stop_airports=f["stop_airports"] if f["stop_airports"] else "",
                cabin_class=cabin_class,
                cabin_class_original=orig_cabin_label,
                original_price=price_eur,
                original_currency=original_currency,
                base_currency=cfg.BASE_CURRENCY,
                exchange_rate_used=used_rate,
                converted_price_base=converted_price,
                ticket_link=f"https://www.staralliance.com/book/{f['flight_number']}/{date}",
                baggage_info="1 x 23kg included",
                fare_rules="Star Alliance fare rules apply",
                search_time="",
                search_date=date,
                is_cheapest=False,
            )
            results.append(flight)

        return results


class MockSource_08_CorporateTravel(BaseSource):
    """
    Simulates a corporate travel agency. GBP prices.
    Focus on Business class. Different cabin naming.
    """
    def __init__(self):
        super().__init__()
        self.source_name = "Corporate Travel (BizBook)"

    def search(self, origin, destination, date, cabin_class, currency_converter):
        results = []

        mock_flights = [
            {"airline": "Lufthansa", "flight_number": "LH941",
             "stops": 0, "stop_airports": "",
             "departure_time": "06:30", "arrival_time": "09:15", "base_price_eur": 200},
            {"airline": "British Airways", "flight_number": "BA1390",
             "stops": 0, "stop_airports": "",
             "departure_time": "07:15", "arrival_time": "10:00", "base_price_eur": 210},
            {"airline": "Lufthansa", "flight_number": "LH943",
             "stops": 0, "stop_airports": "",
             "departure_time": "10:00", "arrival_time": "12:45", "base_price_eur": 220},
            {"airline": "Swiss", "flight_number": "LX8111",
             "stops": 1, "stop_airports": "ZRH",
             "departure_time": "08:15", "arrival_time": "10:30", "base_price_eur": 175},
        ]

        cabin_map = {
            "economy": ("Standard", 1.0),
            "premium_economy": ("Premium Select", 1.5),
            "business": ("Club World", 3.0),
            "first": ("First Suite", 5.0),
        }

        original_currency = "GBP"
        orig_cabin_label, price_multiplier = cabin_map.get(cabin_class, ("Standard", 1.0))

        for f in mock_flights:
            # Corporate travel has booking fees
            service_fee = random.uniform(10, 25)
            price_eur = f["base_price_eur"] * price_multiplier + service_fee
            price_eur += random.uniform(-10, 20)

            rate = currency_converter.rates.get("GBP", 0.86)
            price_gbp = round(price_eur * rate, 2)

            converted_price, used_rate = currency_converter.convert(price_gbp, "GBP")

            dep_tz = get_airport_timezone(origin)
            arr_tz = get_airport_timezone(destination)

            flight = FlightData(
                source_name=self.source_name,
                origin=origin,
                destination=destination,
                departure_time=f["departure_time"],
                arrival_time=f["arrival_time"],
                departure_timezone=dep_tz[0],
                arrival_timezone=arr_tz[0],
                airline=f["airline"],
                flight_number=f["flight_number"],
                stops=f["stops"],
                stop_airports=f["stop_airports"] if f["stop_airports"] else "",
                cabin_class=cabin_class,
                cabin_class_original=orig_cabin_label,
                original_price=price_gbp,
                original_currency=original_currency,
                base_currency=cfg.BASE_CURRENCY,
                exchange_rate_used=used_rate,
                converted_price_base=converted_price,
                ticket_link=f"https://www.bizbook.com/corporate/{f['flight_number']}/{date}",
                baggage_info="Priority baggage included",
                fare_rules="Flexible corporate fare. Changes free.",
                search_time="",
                search_date=date,
                is_cheapest=False,
            )
            results.append(flight)

        return results


class MockSource_09_LastMinuteDeals(BaseSource):
    """
    Simulates a last-minute deals site. GBP prices.
    Cheaper prices, limited availability.
    """
    def __init__(self):
        super().__init__()
        self.source_name = "Last Minute (CheapDeals)"

    def search(self, origin, destination, date, cabin_class, currency_converter):
        results = []

        mock_flights = [
            {"airline": "Eurowings", "flight_number": "EW9882",
             "stops": 0, "stop_airports": "",
             "departure_time": "08:00", "arrival_time": "10:40", "base_price_eur": 75},
            {"airline": "Lufthansa", "flight_number": "LH947",
             "stops": 0, "stop_airports": "",
             "departure_time": "18:00", "arrival_time": "20:45", "base_price_eur": 95},
            {"airline": "KLM", "flight_number": "KL1080",
             "stops": 1, "stop_airports": "AMS",
             "departure_time": "09:15", "arrival_time": "12:45", "base_price_eur": 82},
        ]

        cabin_map = {
            "economy": ("Last Minute Deal", 1.0),
            "premium_economy": ("Premium Deal", 1.5),
            "business": ("Business Deal", 2.5),
            "first": ("First Deal", 4.0),
        }

        original_currency = "GBP"
        orig_cabin_label, price_multiplier = cabin_map.get(cabin_class, ("Last Minute Deal", 1.0))

        for f in mock_flights:
            # Last minute - 20% discount
            discount = 0.80
            price_eur = f["base_price_eur"] * price_multiplier * discount
            price_eur += random.uniform(-3, 5)

            rate = currency_converter.rates.get("GBP", 0.86)
            price_gbp = round(price_eur * rate, 2)

            converted_price, used_rate = currency_converter.convert(price_gbp, "GBP")

            dep_tz = get_airport_timezone(origin)
            arr_tz = get_airport_timezone(destination)

            flight = FlightData(
                source_name=self.source_name,
                origin=origin,
                destination=destination,
                departure_time=f["departure_time"],
                arrival_time=f["arrival_time"],
                departure_timezone=dep_tz[0],
                arrival_timezone=arr_tz[0],
                airline=f["airline"],
                flight_number=f["flight_number"],
                stops=f["stops"],
                stop_airports=f["stop_airports"] if f["stop_airports"] else "",
                cabin_class=cabin_class,
                cabin_class_original=orig_cabin_label,
                original_price=price_gbp,
                original_currency=original_currency,
                base_currency=cfg.BASE_CURRENCY,
                exchange_rate_used=used_rate,
                converted_price_base=converted_price,
                ticket_link=f"https://www.cheapdeals.com/deal/{f['flight_number']}",
                baggage_info="Limited baggage included",
                fare_rules="Non-refundable. No changes allowed.",
                search_time="",
                search_date=date,
                is_cheapest=False,
            )
            results.append(flight)

        return results


class MockSource_10_MultiStop(BaseSource):
    """
    Simulates a multi-stop specialist. EUR prices.
    Specializes in connecting flights with longer layovers.
    """
    def __init__(self):
        super().__init__()
        self.source_name = "Multi-Stop Specialist (WorldRoutes)"

    def search(self, origin, destination, date, cabin_class, currency_converter):
        results = []

        mock_flights = [
            {"airline": "Finnair", "flight_number": "AY1982",
             "stops": 1, "stop_airports": "HEL",
             "departure_time": "08:00", "arrival_time": "11:30", "base_price_eur": 98},
            {"airline": "Iberia", "flight_number": "IB3471",
             "stops": 1, "stop_airports": "MAD",
             "departure_time": "10:30", "arrival_time": "14:00", "base_price_eur": 105},
            {"airline": "Turkish Airlines", "flight_number": "TK1980",
             "stops": 1, "stop_airports": "IST",
             "departure_time": "11:00", "arrival_time": "14:30", "base_price_eur": 95},
            {"airline": "Air France", "flight_number": "AF1669",
             "stops": 1, "stop_airports": "CDG",
             "departure_time": "14:30", "arrival_time": "18:00", "base_price_eur": 108},
            {"airline": "KLM", "flight_number": "KL1074",
             "stops": 2, "stop_airports": "AMS,FRA",
             "departure_time": "06:00", "arrival_time": "09:30", "base_price_eur": 85},
        ]

        cabin_map = {
            "economy": ("Economy Saver", 1.0),
            "premium_economy": ("Premium Comfort", 1.55),
            "business": ("Business Flex", 2.8),
            "first": ("First Class", 4.5),
        }

        original_currency = "EUR"
        orig_cabin_label, price_multiplier = cabin_map.get(cabin_class, ("Economy", 1.0))

        for f in mock_flights:
            # Multi-stop - longer layovers means cheaper
            stop_factor = 1.0 - (f["stops"] * 0.1)  # 10% cheaper per stop
            price_eur = f["base_price_eur"] * price_multiplier * stop_factor
            price_eur += random.uniform(-5, 10)

            converted_price, used_rate = currency_converter.convert(price_eur, "EUR")

            dep_tz = get_airport_timezone(origin)
            arr_tz = get_airport_timezone(destination)

            # The stop_airports may be two stops
            stop_str = ", ".join(f["stop_airports"].split(",")) if f["stop_airports"] else ""

            flight = FlightData(
                source_name=self.source_name,
                origin=origin,
                destination=destination,
                departure_time=f["departure_time"],
                arrival_time=f["arrival_time"],
                departure_timezone=dep_tz[0],
                arrival_timezone=arr_tz[0],
                airline=f["airline"],
                flight_number=f["flight_number"],
                stops=f["stops"],
                stop_airports=stop_str,
                cabin_class=cabin_class,
                cabin_class_original=orig_cabin_label,
                original_price=price_eur,
                original_currency=original_currency,
                base_currency=cfg.BASE_CURRENCY,
                exchange_rate_used=used_rate,
                converted_price_base=converted_price,
                ticket_link=f"https://www.worldroutes.com/book/{f['flight_number']}/{date}",
                baggage_info="Varies by airline",
                fare_rules="Long layover specials",
                search_time="",
                search_date=date,
                is_cheapest=False,
            )
            results.append(flight)

        return results


# ============================================================
# SECTION 3: REAL API SOURCES (OPTIONAL)
# ============================================================
#
# These sources connect to real flight APIs.
# They require free API keys (no payment card needed).
# They only work if you register and configure the keys.
#
# If the API keys are not set, these sources return an empty list.
# If the API call fails, these sources gracefully return empty.
#

class IgnavSource(BaseSource):
    """
    Ignav API - Flight prices and booking links.
    
    WHAT IS THIS?
    Ignav is a simple REST API for flight prices and booking links.
    It replaces Amadeus Self-Service (which shut down July 17, 2026).
    
    HOW TO GET API KEY (free, no credit card):
    1. Go to https://ignav.com
    2. Sign up for a free account
    3. You get 1,000 free requests immediately (no credit card needed)
    4. Add your key to config.py or set: IGNV_API_KEY=your_key
    
    PRICING AFTER FREE TIER:
    - $2.00 per 1,000 successful requests
    - No monthly minimums, no rate limits
    - Only successful requests are billed
    
    API DETAILS:
    - No OAuth needed. Just pass X-Api-Key header.
    - Endpoint: POST https://ignav.com/api/fares/one-way
    """

    def __init__(self, api_key=""):
        super().__init__()
        self.source_name = "Ignav API"
        self.api_key = api_key

    def search(self, origin, destination, date, cabin_class, currency_converter):
        if not self.api_key:
            print(f"  [SKIP] {self.source_name}: No API key configured")
            print(f"  [SKIP] Sign up at https://ignav.com for a free key (no credit card)")
            return []

        try:
            import requests

            print(f"  [API] {self.source_name}: Searching flights...")

            url = "https://ignav.com/api/fares/one-way"
            headers = {
                "X-Api-Key": self.api_key,
                "Content-Type": "application/json",
            }

            # Build the request body
            body = {
                "origin": origin,
                "destination": destination,
                "departure_date": date,
            }

            # Add cabin class filter only if not economy (Ignav defaults to all cabins)
            if cabin_class != "economy":
                body["cabin_class"] = cabin_class

            response = requests.post(url, json=body, headers=headers, timeout=20)

            if response.status_code == 402:
                print(f"  [ERROR] {self.source_name}: Free tier exhausted (402). Add a payment method.")
                return []
            elif response.status_code != 200:
                print(f"  [ERROR] {self.source_name}: API error - {response.status_code}")
                print(f"  [ERROR] Response: {response.text[:200]}")
                return []

            data = response.json()
            itineraries = data.get("itineraries", [])

            if not itineraries:
                print(f"  [INFO] {self.source_name}: No flights found")
                return []

            results = []
            ignav_ids = []

            for itin in itineraries:
                try:
                    outbound = itin.get("outbound", {})
                    segments = outbound.get("segments", [])
                    if not segments:
                        continue

                    first_seg = segments[0]
                    last_seg = segments[-1]

                    # Price
                    price_info = itin.get("price", {})
                    price_eur = float(price_info.get("amount", 0))
                    orig_currency = price_info.get("currency", "USD")

                    # Convert if needed
                    if orig_currency != "EUR":
                        rate_eur = currency_converter.rates.get(orig_currency, 1.0)
                        price_in_eur = price_eur / rate_eur
                    else:
                        price_in_eur = price_eur

                    converted_price, used_rate = currency_converter.convert(price_eur, orig_currency)

                    # Stops
                    stops_count = len(segments) - 1
                    stop_airports = ""
                    if stops_count > 0:
                        stop_airports = ",".join([s["arrival_airport"] for s in segments[:-1]])

                    # Times - Ignav returns full datetime strings
                    dep_raw = first_seg.get("departure_time_local", "")
                    arr_raw = last_seg.get("arrival_time_local", "")
                    dep_time = dep_raw[11:16] if len(dep_raw) >= 16 else dep_raw
                    arr_time = arr_raw[11:16] if len(arr_raw) >= 16 else arr_raw

                    # Airline info
                    carrier = first_seg.get("marketing_carrier_code", "")
                    flight_num = first_seg.get("flight_number", "")
                    carrier_name = first_seg.get("operating_carrier_name", carrier)

                    # Ignav returns cabin class in the itinerary
                    itin_cabin = itin.get("cabin_class", cabin_class)

                    # Filter: when searching economy, only include economy results
                    if cabin_class == "economy" and itin_cabin != "economy":
                        print(f"  [DEBUG] Ignav: Skipping non-economy itinerary ({itin_cabin})")
                        continue

                    # Store ignav_id for later booking-link fetch
                    ignav_ids.append((len(results), itin.get("ignav_id", "")))

                    dep_tz_info = get_airport_timezone(origin)
                    arr_tz_info = get_airport_timezone(destination)

                    flight = FlightData(
                        source_name=self.source_name,
                        origin=origin,
                        destination=destination,
                        departure_time=dep_time,
                        arrival_time=arr_time,
                        departure_timezone=dep_tz_info[0],
                        arrival_timezone=arr_tz_info[0],
                        airline=carrier_name,
                        flight_number=f"{carrier}{flight_num}",
                        stops=stops_count,
                        stop_airports=stop_airports,
                        cabin_class=itin_cabin,
                        cabin_class_original=itin_cabin,
                        original_price=price_eur,
                        original_currency=orig_currency,
                        base_currency=cfg.BASE_CURRENCY,
                        exchange_rate_used=used_rate,
                        converted_price_base=converted_price,
                        ticket_link="",
                        baggage_info="Check airline",
                        fare_rules=itin.get("price", {}).get("status", "Standard fare"),
                        search_time="",
                        search_date=date,
                        is_cheapest=False,
                    )
                    results.append(flight)
                except Exception as e:
                    print(f"  [WARNING] {self.source_name}: Parse error: {e}")
                    continue

            # Fetch booking links for cheapest 5 itineraries (second pass to minimize API calls)
            results.sort(key=lambda f: f.converted_price_base)
            fetched = 0
            for idx, ignav_id in ignav_ids:
                if not ignav_id or fetched >= 5:
                    continue
                try:
                    bl_response = requests.post(
                        "https://ignav.com/api/fares/booking-links",
                        json={"ignav_id": ignav_id},
                        headers=headers,
                        timeout=8,
                    )
                    if bl_response.status_code == 200:
                        bl_data = bl_response.json()
                        opts = bl_data.get("booking_options", [])
                        if opts:
                            links = opts[0].get("links", [])
                            if links:
                                results[idx].ticket_link = links[0].get("url", "")
                                fetched += 1
                except Exception:
                    pass

            print(f"  [OK] {self.source_name}: Found {len(results)} flights")
            return results

        except ImportError:
            print(f"  [ERROR] {self.source_name}: requests library not installed")
            return []
        except Exception as e:
            print(f"  [ERROR] {self.source_name}: {e}")
            return []


class AviationStackSource(BaseSource):
    """
    AviationStack API - Flight schedules.
    
    WHAT IS THIS?
    AviationStack provides flight schedule data.
    
    HOW TO GET API KEY (free, no credit card):
    1. Go to https://aviationstack.com
    2. Sign up for a free account
    3. Get your API key
    4. Add it to config.py or set: AVIATIONSTACK_API_KEY=your_key
    
    NOTE: Free tier allows 500 requests/month.
    This source provides schedules, not prices.
    We use it to get flight numbers and times.
    
    NOTE: The AviationStack free plan does NOT support filtering by route/date.
    So this source can only show current/real-time flights, not future schedules.
    Prices shown are rough ESTIMATES (not real quotes).
    
    For real prices, use Ignav or Kiwi.com instead.
    """

    def __init__(self, api_key=""):
        super().__init__()
        self.source_name = "AviationStack"
        self.api_key = api_key

    def search(self, origin, destination, date, cabin_class, currency_converter):
        if not self.api_key:
            print(f"  [SKIP] {self.source_name}: No API key configured")
            print(f"  [SKIP] Register at https://aviationstack.com for a free key")
            return []

        try:
            import requests

            print(f"  [API] {self.source_name}: Fetching flight schedule data...")

            # AviationStack API
            # Free plan: HTTP only, no filter parameters allowed, 100 requests/month
            url = "http://api.aviationstack.com/v1/flights"
            params = {
                "access_key": self.api_key,
                "limit": 100,
            }

            response = requests.get(url, params=params, timeout=15)

            if response.status_code == 403:
                # Try without filter params (free plan limitation)
                print(f"  [INFO] {self.source_name}: Free plan doesn't support filters.")
                print(f"  [INFO] {self.source_name}: Fetching all flights and filtering locally...")
                params = {"access_key": self.api_key, "limit": 100}
                response = requests.get(url, params=params, timeout=15)

            if response.status_code != 200:
                print(f"  [ERROR] {self.source_name}: API error - {response.status_code}")
                print(f"  [ERROR] Response: {response.text[:200]}")
                return []

            data = response.json()
            all_flights = data.get("data", [])

            if not all_flights:
                print(f"  [INFO] {self.source_name}: No flights found")
                return []

            # Filter locally by origin and destination
            flights_data = []
            for f in all_flights:
                dep = f.get("departure", {})
                arr = f.get("arrival", {})
                if dep.get("iata") == origin and arr.get("iata") == destination:
                    flights_data.append(f)

            if not flights_data:
                print(f"  [INFO] {self.source_name}: No flights for {origin}->{destination} in current data")
                print(f"  [INFO] (Free plan only shows real-time flights, not future schedules)")
                return []

            results = []
            original_currency = "USD"

            for flight_data in flights_data:
                try:
                    flight_info = flight_data.get("flight", {})
                    departure = flight_data.get("departure", {})
                    arrival = flight_data.get("arrival", {})
                    airline_info = flight_data.get("airline", {})

                    airline_name = airline_info.get("name", "Unknown")
                    flight_number = flight_info.get("iata", "")
                    dep_time = departure.get("estimated", departure.get("scheduled", ""))
                    arr_time = arrival.get("estimated", arrival.get("scheduled", ""))

                    if not dep_time or not arr_time:
                        continue

                    # Extract time portion
                    if len(dep_time) >= 16:
                        dep_time_str = dep_time[11:16]
                    else:
                        dep_time_str = dep_time

                    if len(arr_time) >= 16:
                        arr_time_str = arr_time[11:16]
                    else:
                        arr_time_str = arr_time

                    # AviationStack doesn't provide prices - estimate roughly
                    # NOTE: These are NOT real prices, just rough estimates
                    estimated_price = 150 * (1.0 + random.uniform(-0.3, 0.3))
                    price_usd = round(estimated_price, 2)

                    cabin_map = {
                        "economy": ("Economy", 1.0),
                        "premium_economy": ("Premium", 1.7),
                        "business": ("Business", 3.0),
                        "first": ("First", 5.0),
                    }
                    orig_label, mult = cabin_map.get(cabin_class, ("Economy", 1.0))
                    price_usd = round(price_usd * mult, 2)

                    converted_price, used_rate = currency_converter.convert(price_usd, "USD")

                    dep_tz_info = get_airport_timezone(origin)
                    arr_tz_info = get_airport_timezone(destination)

                    flight = FlightData(
                        source_name=self.source_name,
                        origin=origin,
                        destination=destination,
                        departure_time=dep_time_str,
                        arrival_time=arr_time_str,
                        departure_timezone=dep_tz_info[0],
                        arrival_timezone=arr_tz_info[0],
                        airline=airline_name,
                        flight_number=flight_number,
                        stops=0,
                        stop_airports="",
                        cabin_class=cabin_class,
                        cabin_class_original=orig_label,
                        original_price=price_usd,
                        original_currency=original_currency,
                        base_currency=cfg.BASE_CURRENCY,
                        exchange_rate_used=used_rate,
                        converted_price_base=converted_price,
                        ticket_link="",
                        baggage_info="Check airline",
                        fare_rules="ESTIMATED price (AviationStack has no pricing data)",
                        search_time="",
                        search_date=date,
                        is_cheapest=False,
                    )
                    results.append(flight)
                except Exception as e:
                    print(f"  [WARNING] {self.source_name}: Parse error: {e}")
                    continue

            print(f"  [OK] {self.source_name}: Found {len(results)} flights (prices are ESTIMATES)")
            return results

        except ImportError:
            print(f"  [ERROR] {self.source_name}: requests library not installed")
            return []
        except Exception as e:
            print(f"  [ERROR] {self.source_name}: {e}")
            return []


class KiwiSource(BaseSource):
    """
    Kiwi.com (Tequila) API.
    
    WHAT IS THIS?
    Kiwi.com has a travel search API called Tequila.
    They offer flight search, hotel, and other travel data.
    
    HOW TO GET API KEY (free, no credit card):
    1. Go to https://tequila.kiwi.com
    2. Sign up for a free account
    3. Get your API key
    4. Add it to config.py or set: KIWI_API_KEY=your_key
    
    NOTE: Kiwi.com offers a free tier with monthly request limits.
    """

    def __init__(self, api_key=""):
        super().__init__()
        self.source_name = "Kiwi.com (Tequila)"
        self.api_key = api_key

    def search(self, origin, destination, date, cabin_class, currency_converter):
        if not self.api_key:
            print(f"  [SKIP] {self.source_name}: No API key configured")
            print(f"  [SKIP] Register at https://tequila.kiwi.com for a free key")
            return []

        try:
            import requests

            print(f"  [API] {self.source_name}: Searching flights...")

            url = "https://tequila-api.kiwi.com/v2/search"
            headers = {"apikey": self.api_key}

            # Cabin class mapping
            cabin_map = {
                "economy": "M",
                "premium_economy": "W",
                "business": "C",
                "first": "F",
            }
            kiwi_cabin = cabin_map.get(cabin_class, "M")

            params = {
                "fly_from": origin,
                "fly_to": destination,
                "date_from": date,
                "date_to": date,
                "selected_cabins": kiwi_cabin,
                "adults": 1,
                "curr": "EUR",
                "max_stopovers": 2,
                "limit": 10,
            }

            response = requests.get(url, headers=headers, params=params, timeout=20)

            if response.status_code != 200:
                print(f"  [ERROR] {self.source_name}: API error - {response.status_code}")
                print(f"  [ERROR] Response: {response.text[:200]}")
                return []

            data = response.json()
            kiwi_data = data.get("data", [])

            if not kiwi_data:
                print(f"  [INFO] {self.source_name}: No flights found")
                return []

            results = []
            original_currency = "EUR"

            for item in kiwi_data:
                try:
                    route_segments = item.get("route", [])
                    if not route_segments:
                        continue

                    first_leg = route_segments[0]
                    last_leg = route_segments[-1]

                    stops_count = item.get("technical_stops", 0)
                    if len(route_segments) > 1:
                        stops_count = len(route_segments) - 1

                    stop_airports = ""
                    if stops_count > 0:
                        stop_codes = []
                        for seg in route_segments[:-1]:
                            stop_codes.append(seg.get("flyTo", ""))
                        stop_airports = ",".join(stop_codes)

                    price_eur = float(item.get("price", 0))
                    converted_price, used_rate = currency_converter.convert(price_eur, "EUR")

                    # Deep link for booking
                    deep_link = item.get("deep_link", "")
                    if not deep_link:
                        booking_token = item.get("booking_token", "")
                        deep_link = f"https://www.kiwi.com/deep?token={booking_token}"

                    dep_tz_info = get_airport_timezone(origin)
                    arr_tz_info = get_airport_timezone(destination)

                    flight = FlightData(
                        source_name=self.source_name,
                        origin=origin,
                        destination=destination,
                        departure_time=first_leg.get("local_departure", "")[11:16] if len(first_leg.get("local_departure", "")) > 16 else first_leg.get("local_departure", ""),
                        arrival_time=last_leg.get("local_arrival", "")[11:16] if len(last_leg.get("local_arrival", "")) > 16 else last_leg.get("local_arrival", ""),
                        departure_timezone=dep_tz_info[0],
                        arrival_timezone=arr_tz_info[0],
                        airline=first_leg.get("airline", ""),
                        flight_number=f"{first_leg.get('airline', '')}{first_leg.get('flight_no', '')}",
                        stops=stops_count,
                        stop_airports=stop_airports,
                        cabin_class=cabin_class,
                        cabin_class_original=item.get("selected_cabins", kiwi_cabin),
                        original_price=price_eur,
                        original_currency=original_currency,
                        base_currency=cfg.BASE_CURRENCY,
                        exchange_rate_used=used_rate,
                        converted_price_base=converted_price,
                        ticket_link=deep_link,
                        baggage_info=f"{item.get('bags_price', {}).get('1', 0)} EUR for 1 bag" if item.get('bags_price') else "Check airline",
                        fare_rules=f"Duration: {item.get('flight_duration', 'N/A')}h",
                        search_time="",
                        search_date=date,
                        is_cheapest=False,
                    )
                    results.append(flight)
                except Exception as e:
                    print(f"  [WARNING] {self.source_name}: Parse error: {e}")
                    continue

            print(f"  [OK] {self.source_name}: Found {len(results)} flights")
            return results

        except ImportError:
            print(f"  [ERROR] {self.source_name}: requests library not installed")
            return []
        except Exception as e:
            print(f"  [ERROR] {self.source_name}: {e}")
            return []


# ============================================================
# SECTION 4: GOOGLE FLIGHTS SOURCE (fast-flights library)
# ============================================================

class GoogleFlightsSource(BaseSource):
    """
    Google Flights via reverse-engineered Protobuf API.
    Uses the fast-flights library which bypasses browser requirements.
    Returns real flight prices, schedules, and booking links.

    This works by reverse-engineering the internal Google Flights API
    that the web UI uses internally. No browser or API key needed.
    """

    def __init__(self):
        super().__init__()
        self.source_name = "Google Flights"

    def search(self, origin, destination, date, cabin_class, currency_converter):
        try:
            from fast_flights import FlightQuery, create_filter, get_flights, Passengers

            gseat = cabin_class.replace("_", "-")
            if gseat not in ("economy", "premium-economy", "business", "first"):
                gseat = "economy"

            query = create_filter(
                flights=[
                    FlightQuery(date=date, from_airport=origin, to_airport=destination)
                ],
                seat=gseat,
                trip="one-way",
                passengers=Passengers(adults=1, children=0, infants_in_seat=0, infants_on_lap=0),
                currency="EUR",
            )

            print(f"  [API] {self.source_name}: Searching flights via Protobuf API...")
            result = get_flights(query)

            if not result:
                print(f"  [INFO] {self.source_name}: No flights found")
                return []

            flights_list = list(result)
            if not flights_list:
                print(f"  [INFO] {self.source_name}: No flights found")
                return []

            results = []
            for item in flights_list:
                try:
                    price_eur = float(item.price)
                    if price_eur <= 0:
                        continue

                    airline_name = "Unknown"
                    if item.airlines and len(item.airlines) > 0:
                        airline_name = item.airlines[0]
                    carrier_code = getattr(item, "type", "")

                    segments_raw = getattr(item, "flights", None)
                    segments = list(segments_raw) if segments_raw else []
                    if not segments or len(segments) == 0:
                        continue

                    first_seg = segments[0]
                    last_seg = segments[-1]

                    stops_count = len(segments) - 1
                    stop_codes = []
                    for seg in segments[:-1]:
                        to_code = getattr(getattr(seg, "to_airport", None), "code", "")
                        if to_code:
                            stop_codes.append(to_code)
                    stop_airports = ",".join(stop_codes)

                    dep_t = getattr(getattr(first_seg, "departure", None), "time", [0, 0])
                    arr_t = getattr(getattr(last_seg, "arrival", None), "time", [0, 0])
                    if len(dep_t) >= 2:
                        dep_time = f"{dep_t[0]:02d}:{dep_t[1]:02d}"
                        flight_num = f"{carrier_code}{dep_t[0]:02d}{dep_t[1]:02d}"
                    else:
                        dep_time = "00:00"
                        flight_num = carrier_code or ""
                    if len(arr_t) >= 2:
                        arr_time = f"{arr_t[0]:02d}:{arr_t[1]:02d}"
                    else:
                        arr_time = "00:00"

                    duration = 0
                    for seg in segments:
                        d = getattr(seg, "duration", 0)
                        if d:
                            duration += int(d)

                    converted_price, used_rate = currency_converter.convert(price_eur, "EUR")

                    dep_tz_info = get_airport_timezone(origin)
                    arr_tz_info = get_airport_timezone(destination)

                    flight = FlightData(
                        source_name=self.source_name,
                        origin=origin,
                        destination=destination,
                        departure_time=dep_time,
                        arrival_time=arr_time,
                        departure_timezone=dep_tz_info[0],
                        arrival_timezone=arr_tz_info[0],
                        airline=airline_name,
                        flight_number=flight_num,
                        stops=stops_count,
                        stop_airports=stop_airports,
                        cabin_class=cabin_class,
                        cabin_class_original=cabin_class.replace("_", " ").title(),
                        original_price=price_eur,
                        original_currency="EUR",
                        base_currency=cfg.BASE_CURRENCY,
                        exchange_rate_used=used_rate,
                        converted_price_base=converted_price,
                        ticket_link=f"https://www.google.com/travel/flights?q=Flights+to+{destination}+from+{origin}+on+{date}",
                        baggage_info="Check airline",
                        fare_rules=f"Duration: {duration}min",
                        search_time="",
                        search_date=date,
                        is_cheapest=False,
                    )
                    results.append(flight)
                except Exception as e:
                    print(f"  [WARNING] {self.source_name}: Parse error: {e}")
                    continue

            print(f"  [OK] {self.source_name}: Found {len(results)} flights")
            return results

        except ImportError:
            print(f"  [ERROR] {self.source_name}: fast-flights library not installed")
            print(f"  [ERROR] Install with: pip install fast-flights")
            return []
        except Exception as e:
            print(f"  [ERROR] {self.source_name}: {e}")
            return []


# ============================================================
# SECTION 5: RYANAIR SOURCE (direct API)
# ============================================================

class RyanairSource(BaseSource):
    """
    Ryanair flight search via Ryanair's public API.
    Uses the undocumented Ryanair services API directly.

    Ryanair primarily operates from smaller/regional airports.
    For MAN->FRA this may return 0 results, but for routes
    Ryanair actually flies, it provides real pricing.
    """

    def __init__(self):
        super().__init__()
        self.source_name = "Ryanair"

    def search(self, origin, destination, date, cabin_class, currency_converter):
        if cabin_class != "economy":
            print(f"  [INFO] {self.source_name}: Only economy class available, skipping non-economy search")
            return []

        try:
            import requests

            print(f"  [API] {self.source_name}: Searching flights...")

            url = "https://services-api.ryanair.com/farfnd/v4/oneWayFares"
            params = {
                "departureAirportIataCode": origin,
                "outboundDepartureDateFrom": date,
                "outboundDepartureDateTo": date,
                "outboundDepartureTimeFrom": "00:00",
                "outboundDepartureTimeTo": "23:59",
                "arrivalAirportIataCode": destination,
            }

            response = requests.get(url, params=params, timeout=15)

            if response.status_code != 200:
                print(f"  [ERROR] {self.source_name}: API error - {response.status_code}")
                return []

            data = response.json()
            fares = data.get("fares", [])

            if not fares:
                print(f"  [INFO] {self.source_name}: No flights found (Ryanair may not fly this route)")
                return []

            results = []
            for fare in fares:
                try:
                    outbound = fare.get("outbound", {})
                    if not outbound:
                        continue

                    price_info = outbound.get("price", {})
                    price_value = float(price_info.get("value", 0))
                    currency = price_info.get("currencyCode", "EUR")

                    flight_number = outbound.get("flightNumber", "")
                    carrier = flight_number[:2] if flight_number else "FR"

                    time_segments = outbound.get("time", [])
                    dep_time_raw = time_segments[0] if len(time_segments) > 0 else {}
                    arr_time_raw = time_segments[-1] if time_segments else {}
                    dep_time = dep_time_raw.get("time", "00:00")[:5] if isinstance(dep_time_raw, dict) else "00:00"
                    arr_time = arr_time_raw.get("time", "00:00")[:5] if isinstance(arr_time_raw, dict) else "00:00"

                    segments = outbound.get("segments", [])
                    stops_count = max(0, len(segments) - 1)
                    stop_airports = ""
                    if stops_count > 0:
                        stop_codes = []
                        for seg in segments[:-1]:
                            stop_codes.append(seg.get("arrivalAirportIataCode", ""))
                        stop_airports = ",".join(stop_codes)

                    converted_price, used_rate = currency_converter.convert(price_value, currency)

                    dep_tz_info = get_airport_timezone(origin)
                    arr_tz_info = get_airport_timezone(destination)

                    flight = FlightData(
                        source_name=self.source_name,
                        origin=origin,
                        destination=destination,
                        departure_time=dep_time,
                        arrival_time=arr_time,
                        departure_timezone=dep_tz_info[0],
                        arrival_timezone=arr_tz_info[0],
                        airline=f"Ryanair ({carrier})",
                        flight_number=flight_number,
                        stops=stops_count,
                        stop_airports=stop_airports,
                        cabin_class="economy",
                        cabin_class_original="Ryanair Standard",
                        original_price=price_value,
                        original_currency=currency,
                        base_currency=cfg.BASE_CURRENCY,
                        exchange_rate_used=used_rate,
                        converted_price_base=converted_price,
                        ticket_link=f"https://www.ryanair.com/gb/en/booking/{flight_number}",
                        baggage_info="No checked bag included. Cabin bag only.",
                        fare_rules="Non-refundable. Change fee applies.",
                        search_time="",
                        search_date=date,
                        is_cheapest=False,
                    )
                    results.append(flight)
                except Exception as e:
                    print(f"  [WARNING] {self.source_name}: Parse error: {e}")
                    continue

            print(f"  [OK] {self.source_name}: Found {len(results)} flights")
            return results

        except ImportError:
            print(f"  [ERROR] {self.source_name}: requests library not installed")
            return []
        except Exception as e:
            print(f"  [ERROR] {self.source_name}: {e}")
            return []


# ============================================================
# SECTION 6: PLAYWRIGHT WEB SCRAPERS
# ============================================================
#
# These scrapers use Playwright to extract flight data from
# travel websites. They run a headless Chromium browser.
#
# ANTI-BOT NOTES:
# Major travel sites (Kayak, Expedia, Skyscanner) use various
# anti-bot protections. These scrapers attempt to bypass by:
#   - Using realistic user-agent strings
#   - Randomizing viewport size
#   - Waiting for elements properly
#   - Handling cookie consent banners
# If a site blocks the scraper, it fails gracefully (empty results).


class KayakScraper(BaseSource):
    """
    Scrapes Kayak for flight prices.
    Uses Playwright to render the page and extract results.
    """

    def __init__(self):
        super().__init__()
        self.source_name = "Kayak"

    def search(self, origin, destination, date, cabin_class, currency_converter):
        if cabin_class != "economy":
            print(f"  [INFO] {self.source_name}: Cabin filtering not supported, skipping non-economy search")
            return []

        try:
            from playwright.sync_api import sync_playwright
            import re
            import time

            print(f"  [SCRAPE] {self.source_name}: Opening browser...")

            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
                )
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                    locale="en-GB",
                )
                page = context.new_page()

                url = f"https://www.kayak.co.uk/flights/{origin}-{destination}/{date}"
                print(f"  [SCRAPE] {self.source_name}: Navigating to {url}")

                # Load the page and let JS render flight results
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                # Give page time to render dynamic flight results
                try:
                    page.wait_for_selector('[class*="result"]', timeout=6000)
                except Exception:
                    pass
                page.wait_for_timeout(5000)

                # Accept cookie banner if present
                try:
                    accept_btn = page.query_selector('button:has-text("Accept all")')
                    if accept_btn and accept_btn.is_visible():
                        accept_btn.click()
                        page.wait_for_timeout(1000)
                except Exception:
                    pass

                # Click "Show more results" to load additional prices
                for attempt in range(2):
                    try:
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        page.wait_for_timeout(800)
                        load_more = None
                        for sel in [
                            'button:has-text("Show more results")',
                            'button:has-text("Show more")',
                            '[class*="more" i]',
                        ]:
                            el = page.query_selector(sel)
                            if el and el.is_visible():
                                text = el.inner_text().strip()
                                if "show" in text.lower() or "more" in text.lower():
                                    load_more = el
                                    break
                        if not load_more:
                            break
                        load_more.click()
                        page.wait_for_timeout(1500)
                        print(f"  [SCRAPE] {self.source_name}: Loaded more results (click {attempt+1})")
                    except Exception:
                        break

                # Extract structured flight data using JavaScript evaluation
                flight_entries = page.evaluate("""
                    () => {
                        const results = [];
                        // Find all price elements on the page
                        const priceEls = document.querySelectorAll('[class*="price"], [class*="Price"]');
                        const seen = new Set();
                        priceEls.forEach(el => {
                            const text = el.textContent.trim();
                            const match = text.match(/[£€$]([\\d,]+)/);
                            if (match) {
                                const price = parseFloat(match[1].replace(/,/g, ''));
                                if (price > 0 && price < 5000) {
                                    // Find nearby text for context
                                    const parent = el.closest('[class*="result"], [class*="Result"], [class*="card"], [class*="Card"]') || el.parentElement;
                                    const context = parent ? parent.textContent : '';
                                    results.push({ price, context });
                                }
                            }
                        });
                        return results;
                    }
                """)

                # If JS evaluation didn't work well, fall back to text extraction
                if not flight_entries or len(flight_entries) < 5:
                    body_text = page.inner_text("body")
                    lines = body_text.split("\n")
                    flight_entries = []
                    for i, line in enumerate(lines):
                        line = line.strip()
                        if not line:
                            continue
                        price_match = re.search(r'[£€$]([\d,]+)', line)
                        if price_match:
                            try:
                                price_val = float(price_match.group(1).replace(",", ""))
                                # Get surrounding context (5 lines before and after)
                                start = max(0, i - 5)
                                end = min(len(lines), i + 6)
                                context = " ".join(lines[start:end])
                                flight_entries.append({"price": price_val, "context": context[:500]})
                            except ValueError:
                                pass

                browser.close()

            # Build results from extracted entries
            results = []
            seen_keys = set()
            for entry in flight_entries:
                price_gbp = entry["price"]
                if price_gbp <= 0 or price_gbp > 5000:
                    continue
                dedup_key = round(price_gbp)
                if dedup_key in seen_keys:
                    continue
                seen_keys.add(dedup_key)

                # Try to parse airline and stops from context
                context = entry.get("context", "")
                airline_match = re.search(r'(Lufthansa|British Airways|Ryanair|KLM|Air France|Eurowings|Swiss|SWISS|Scandinavian|Aer Lingus|Trip\.com|Multiple airlines|Vueling|Wizz Air|Jet2|easyJet|Emirates|Qatar Airways|Turkish Airlines|Aegean|Finnair|Iberia|SAS|Brussels Airlines|TAP Air Portugal|LOT|Air Baltic)', context)
                airline = airline_match.group(1) if airline_match else "Kayak (multiple airlines)"

                stops_match = re.search(r'(direct|non.?stop|0 stop|\b1 stop\b|\b2 stop\b|\b\d+\+ stop)', context)
                stops = 0
                if stops_match:
                    st = stops_match.group(1)
                    if "1 stop" in st:
                        stops = 1
                    elif "2 stop" in st or "2+" in st:
                        stops = 2

                times_match = re.findall(r'(\d{2}:\d{2})\s*[–\-—]\s*(\d{2}:\d{2})', context)
                dep_time = times_match[0][0] if times_match else ""
                arr_time = times_match[0][1] if times_match else ""

                converted_price, used_rate = currency_converter.convert(price_gbp, "GBP")
                dep_tz_info = get_airport_timezone(origin)
                arr_tz_info = get_airport_timezone(destination)

                flight = FlightData(
                    source_name=self.source_name,
                    origin=origin,
                    destination=destination,
                    departure_time=dep_time,
                    arrival_time=arr_time,
                    departure_timezone=dep_tz_info[0],
                    arrival_timezone=arr_tz_info[0],
                    airline=airline,
                    flight_number="",
                    stops=stops,
                    stop_airports="",
                    cabin_class=cabin_class,
                    cabin_class_original=cabin_class.replace("_", " ").title(),
                    original_price=price_gbp,
                    original_currency="GBP",
                    base_currency=cfg.BASE_CURRENCY,
                    exchange_rate_used=used_rate,
                    converted_price_base=converted_price,
                    ticket_link=url,
                    baggage_info="Check booking site",
                    fare_rules="Price from Kayak",
                    search_time="",
                    search_date=date,
                    is_cheapest=False,
                )
                results.append(flight)

            print(f"  [SCRAPE] {self.source_name}: Extracted {len(results)} unique prices from page")
            if results:
                return results[:100]

            print(f"  [INFO] {self.source_name}: Kayak data not extractable")
            return []

        except ImportError:
            print(f"  [ERROR] {self.source_name}: playwright not installed")
            return []
        except Exception as e:
            print(f"  [ERROR] {self.source_name}: {e}")
            return []


class SkyscannerScraper(BaseSource):
    """
    Scrapes Skyscanner for flight prices.
    Skyscanner has a direct API endpoint that returns JSON.
    """

    def __init__(self):
        super().__init__()
        self.source_name = "Skyscanner"

    def search(self, origin, destination, date, cabin_class, currency_converter):
        try:
            import requests

            print(f"  [API] {self.source_name}: Searching via Skyscanner API...")

            cabin_map = {
                "economy": "economy",
                "premium_economy": "premium_economy",
                "business": "business",
                "first": "first",
            }
            sc_cabin = cabin_map.get(cabin_class, "economy")

            url = (
                f"https://www.skyscanner.net/transport/flights/{origin}/{destination}/{date}/"
                f"?adultsv2=1&cabinclass={sc_cabin}&currency=EUR&stops=0%7E2"
            )

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-GB,en;q=0.9",
            }

            response = requests.get(url, headers=headers, timeout=20)

            if response.status_code != 200:
                print(f"  [ERROR] {self.source_name}: HTTP {response.status_code}")
                return []

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")

            text_lower = response.text.lower()
            if "captcha" in text_lower or "blocked" in text_lower or "automated" in text_lower:
                print(f"  [INFO] {self.source_name}: Anti-bot protection detected")
                return []

            print(f"  [INFO] {self.source_name}: No structured results extractable from HTML")
            print(f"  [INFO] Skyscanner requires JavaScript rendering for flight data")
            return []

        except ImportError:
            print(f"  [ERROR] {self.source_name}: requests/bs4 not installed")
            return []
        except Exception as e:
            print(f"  [ERROR] {self.source_name}: {e}")
            return []


class ExpediaScraper(BaseSource):
    """
    Scrapes Expedia for flight prices.
    """

    def __init__(self):
        super().__init__()
        self.source_name = "Expedia"

    def search(self, origin, destination, date, cabin_class, currency_converter):
        try:
            import requests

            print(f"  [API] {self.source_name}: Searching via Expedia...")

            cabin_map = {
                "economy": "economy",
                "premium_economy": "premium_economy",
                "business": "business",
                "first": "first",
            }
            cabin = cabin_map.get(cabin_class, "economy")

            url = (
                f"https://www.expedia.co.uk/Flights-Search?"
                f"flight-type=on&starDate={date}&mode=search"
                f"&trip=oneway&leg1=from:{origin},to:{destination},departure:{date}"
                f"&passengers=adults:1,children:0&cabin={cabin}"
            )

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }

            response = requests.get(url, headers=headers, timeout=20)

            if response.status_code != 200:
                print(f"  [ERROR] {self.source_name}: HTTP {response.status_code}")
                return []

            text_lower = response.text.lower()
            if "captcha" in text_lower or "blocked" in text_lower:
                print(f"  [INFO] {self.source_name}: Anti-bot protection detected")
                return []

            print(f"  [INFO] {self.source_name}: Expedia requires JavaScript rendering")
            return []

        except ImportError:
            print(f"  [ERROR] {self.source_name}: requests not installed")
            return []
        except Exception as e:
            print(f"  [ERROR] {self.source_name}: {e}")
            return []


# ============================================================
# SECTION 6B: WHENTOFLY SOURCE (free API, no signup)
# ============================================================

# ============================================================
# SECTION 6C: OCTOTRIP SOURCE (MCP, free, no API key)
# ============================================================

class OctoTripSource(BaseSource):
    """
    OctoTrip flights - Free MCP server for flight search.
    No API key or login required.
    Uses MCP protocol (JSON-RPC + SSE) to search flights.

    Returns real-time pricing from multiple booking platforms.
    """

    def __init__(self):
        super().__init__()
        self.source_name = "OctoTrip"

    def search(self, origin, destination, date, cabin_class, currency_converter):
        if cabin_class != "economy":
            print(f"  [INFO] {self.source_name}: Cabin filtering not supported, skipping non-economy search")
            return []

        try:
            import requests, json, time

            print(f"  [API] {self.source_name}: Searching flights...")

            url = "https://mcp.octotrip.app/flights/mcp"
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            }

            payload = {
                "jsonrpc": "2.0",
                "id": int(time.time() * 1000) % 100000,
                "method": "tools/call",
                "params": {
                    "name": "search",
                    "arguments": {
                        "origin": origin,
                        "destination": destination,
                        "departure_date": date,
                    },
                },
            }

            response = requests.post(url, json=payload, headers=headers, timeout=30)

            if response.status_code != 200:
                print(f"  [ERROR] {self.source_name}: HTTP {response.status_code}")
                return []

            text = response.text
            results_list = []

            for line in text.split("\n"):
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        content = data.get("result", {}).get("content", [])
                        for c in content:
                            if c.get("type") == "text":
                                flights_data = json.loads(c["text"])
                                results_list = flights_data.get("results", [])
                    except (json.JSONDecodeError, KeyError):
                        continue

            if not results_list:
                print(f"  [INFO] {self.source_name}: No flights found")
                return []

            results = []
            for item in results_list:
                try:
                    airline = item.get("airline", "Unknown")
                    price = float(item.get("price", 0))
                    currency = item.get("currency", "EUR")
                    stops = item.get("stops", 0)
                    is_direct = item.get("is_direct", False)
                    flight_nums = item.get("flight_numbers", [])
                    duration = item.get("total_duration_minutes", 0)
                    outbound = item.get("outbound", {})
                    dep_time = outbound.get("departure_time", "")
                    arr_time = outbound.get("arrival_time", "")
                    gate = item.get("gate", "OctoTrip")
                    booking_url = item.get("booking_url", "")

                    if price <= 0:
                        continue

                    stop_airports = ""
                    if stops > 0:
                        legs = outbound.get("legs", [])
                        stop_codes = []
                        for leg in legs[:-1]:
                            stop_codes.append(leg.get("arrival", ""))
                        stop_airports = ",".join(stop_codes)

                    converted_price, used_rate = currency_converter.convert(price, currency)

                    dep_tz_info = get_airport_timezone(origin)
                    arr_tz_info = get_airport_timezone(destination)

                    flight_number = flight_nums[0] if flight_nums else ""

                    flight = FlightData(
                        source_name=self.source_name,
                        origin=origin,
                        destination=destination,
                        departure_time=dep_time[:5] if len(dep_time) >= 5 else dep_time,
                        arrival_time=arr_time[:5] if len(arr_time) >= 5 else arr_time,
                        departure_timezone=dep_tz_info[0],
                        arrival_timezone=arr_tz_info[0],
                        airline=airline,
                        flight_number=flight_number,
                        stops=stops,
                        stop_airports=stop_airports,
                        cabin_class=cabin_class,
                        cabin_class_original=cabin_class.replace("_", " ").title(),
                        original_price=price,
                        original_currency=currency,
                        base_currency=cfg.BASE_CURRENCY,
                        exchange_rate_used=used_rate,
                        converted_price_base=converted_price,
                        ticket_link=booking_url,
                        baggage_info="Check provider",
                        fare_rules=f"Duration: {duration}min",
                        search_time="",
                        search_date=date,
                        is_cheapest=False,
                    )
                    results.append(flight)
                except Exception as e:
                    print(f"  [WARNING] {self.source_name}: Parse error: {e}")
                    continue

            print(f"  [OK] {self.source_name}: Found {len(results)} flights")
            return results

        except ImportError:
            print(f"  [ERROR] {self.source_name}: requests library not installed")
            return []
        except Exception as e:
            print(f"  [ERROR] {self.source_name}: {e}")
            return []


_AIRLINE_CODES = {
    "AA": "American Airlines", "AF": "Air France", "AM": "Aeromexico",
    "AY": "Finnair", "AZ": "IT Airways", "BA": "British Airways",
    "BR": "EVA Air", "CA": "Air China", "CI": "China Airlines",
    "CZ": "China Southern", "DL": "Delta Air Lines", "EK": "Emirates",
    "EN": "Air Dolomiti", "ET": "Ethiopian Airlines", "EY": "Etihad",
    "FZ": "flydubai", "GA": "Garuda Indonesia", "HU": "Hainan Airlines",
    "IB": "Iberia", "JL": "Japan Airlines", "KL": "KLM",
    "KQ": "Kenya Airways", "KU": "Kuwait Airways", "LA": "LATAM",
    "LH": "Lufthansa", "LO": "LOT Polish", "LX": "Swiss",
    "LY": "El Al", "MH": "Malaysia Airlines", "MS": "EgyptAir",
    "MU": "China Eastern", "NH": "ANA", "NX": "Air Macau",
    "OS": "Austrian", "OZ": "Asiana", "PC": "Pegasus",
    "QR": "Qatar Airways", "RJ": "Royal Jordanian", "RO": "Tarom",
    "SA": "SAA", "SC": "Shandong Airlines", "SK": "SAS",
    "SN": "Brussels Airlines", "SQ": "Singapore Airlines",
    "SU": "Aeroflot", "SV": "Saudia", "TG": "Thai Airways",
    "TK": "Turkish Airlines", "TP": "TAP Air Portugal",
    "TU": "Tunisair", "UA": "United Airlines", "UK": "Vistara",
    "UL": "SriLankan", "VN": "Vietnam Airlines", "VS": "Virgin Atlantic",
    "VY": "Vueling", "W6": "Wizz Air", "WY": "Oman Air",
    "CA": "Air China", "CX": "Cathay Pacific",
    "EI": "Aer Lingus", "EW": "Eurowings",
    "FR": "Ryanair", "GF": "Gulf Air",
    "HM": "Air Seychelles", "HY": "Uzbekistan Airways",
    "IR": "Iran Air", "IZ": "Arkia",
    "JP": "Adria Airways", "KC": "Air Astana",
    "KE": "Korean Air", "LT": "LATAM",
    "MK": "Air Mauritius", "MO": "Calm Air",
    "NF": "Air Vanuatu", "NZ": "Air New Zealand",
    "OU": "Croatia Airlines", "PK": "Pakistan Intl",
    "PR": "Philippine Airlines", "PS": "Ukraine Intl",
    "PT": "WestJet", "PW": "Precision Air",
    "PX": "Air Niugini", "QF": "Qantas",
    "QR": "Qatar Airways", "RA": "Nepal Airlines",
    "RB": "Syrian Arab", "SB": "Aircalin",
    "S7": "S7 Airlines", "SM": "Air Cairo",
    "TB": "TUI fly Belgium", "TK": "Turkish Airlines",
    "T5": "Turkmenistan", "U6": "Ural Airlines",
    "UU": "Air Austral", "W5": "Mahan Air",
    "WB": "RwandAir", "XQ": "SunExpress",
    "ZB": "Monarch", "ZF": "Air Sial",
}


class WhentoFlySource(BaseSource):
    """
    WhentoFly.io - Free flight search API, no signup required.
    Returns real-time pricing from multiple providers (Aviasales, etc.).
    Note: This API does NOT return flight numbers, departure times, or arrival times.
    """

    def __init__(self):
        super().__init__()
        self.source_name = "WhentoFly"

    def search(self, origin, destination, date, cabin_class, currency_converter):
        try:
            import requests

            cabin = cabin_class.replace("_", "-") if cabin_class in ("premium_economy",) else cabin_class

            url = (
                f"https://whentofly.io/search"
                f"?from={origin}&to={destination}"
                f"&earliest={date}&latest={date}"
                f"&one_way=true&cabin={cabin}"
            )

            print(f"  [API] {self.source_name}: Fetching prices...")
            import time as _time

            response = requests.get(url, timeout=20)

            # Exponential backoff on server errors (Cloudflare tunnel down, etc.)
            max_retries = 3
            retry_delay = 2
            for attempt in range(max_retries):
                if response.status_code < 500:
                    break
                print(f"  [RETRY] {self.source_name}: HTTP {response.status_code}, retry {attempt+1}/{max_retries} in {retry_delay}s")
                _time.sleep(retry_delay)
                retry_delay *= 2
                response = requests.get(url, timeout=20)

            if response.status_code != 200:
                print(f"  [ERROR] {self.source_name}: HTTP {response.status_code}")
                return []

            data = response.json()
            results_list = data.get("results", [])

            if not results_list:
                print(f"  [INFO] {self.source_name}: No prices found")
                return []

            results = []
            for item in results_list:
                try:
                    price_info = item.get("price", {})
                    amount = float(price_info.get("amount", 0))
                    currency = price_info.get("currency", "USD")
                    if amount <= 0:
                        continue

                    airline_code = item.get("airline", "")
                    airline = _AIRLINE_CODES.get(airline_code, airline_code or "Unknown")
                    transfers = item.get("transfers", 0)
                    book_url = item.get("book_url", "")

                    converted_price, used_rate = currency_converter.convert(amount, currency)

                    dep_tz_info = get_airport_timezone(origin)
                    arr_tz_info = get_airport_timezone(destination)

                    flight = FlightData(
                        source_name=self.source_name,
                        origin=origin,
                        destination=destination,
                        departure_time="",
                        arrival_time="",
                        departure_timezone=dep_tz_info[0],
                        arrival_timezone=arr_tz_info[0],
                        airline=airline,
                        flight_number="",
                        stops=transfers,
                        stop_airports="",
                        cabin_class=cabin_class,
                        cabin_class_original=cabin_class.capitalize(),
                        original_price=amount,
                        original_currency=currency,
                        base_currency=cfg.BASE_CURRENCY,
                        exchange_rate_used=used_rate,
                        converted_price_base=converted_price,
                        ticket_link=book_url,
                        baggage_info="Check provider",
                        fare_rules="Price via Aviasales/WhentoFly",
                        search_time="",
                        search_date=date,
                        is_cheapest=False,
                    )
                    results.append(flight)
                except Exception as e:
                    print(f"  [WARNING] {self.source_name}: Parse error: {e}")
                    continue

            print(f"  [OK] {self.source_name}: Found {len(results)} flights")
            return results

        except ImportError:
            print(f"  [ERROR] {self.source_name}: requests library not installed")
            return []
        except Exception as e:
            print(f"  [ERROR] {self.source_name}: {e}")
            return []


class MomondoScraper(BaseSource):
    """
    Scrapes Momondo for flight prices.
    Momondo is owned by the same group as Kayak.
    """

    def __init__(self):
        super().__init__()
        self.source_name = "Momondo"

    def search(self, origin, destination, date, cabin_class, currency_converter):
        try:
            import requests

            print(f"  [API] {self.source_name}: Searching via Momondo...")

            url = f"https://www.momondo.co.uk/flights/{origin}-{destination}/{date}"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }

            response = requests.get(url, headers=headers, timeout=20)

            if response.status_code != 200:
                print(f"  [ERROR] {self.source_name}: HTTP {response.status_code}")
                return []

            text_lower = response.text.lower()
            if "captcha" in text_lower or "blocked" in text_lower:
                print(f"  [INFO] {self.source_name}: Anti-bot protection detected")
                return []

            print(f"  [INFO] {self.source_name}: Momondo requires JavaScript rendering")
            return []

        except ImportError:
            print(f"  [ERROR] {self.source_name}: requests not installed")
            return []
        except Exception as e:
            print(f"  [ERROR] {self.source_name}: {e}")
            return []


# ============================================================
# SECTION 7: SOURCE MANAGER
# ============================================================

class SourceManager:
    """
    Manages all flight data sources.
    
    RESPONSIBILITIES:
    1. Create all enabled sources
    2. Run all sources (in parallel or sequential)
    3. Collect all results
    4. Handle errors from individual sources
    5. Return combined results
    
    HOW IT HANDLES ERRORS:
    - Each source runs in its own try/except block
    - If a source fails, we log the error and continue
    - Other sources are not affected
    - The user sees which sources succeeded and which failed
    """

    def __init__(self, currency_converter):
        self.currency_converter = currency_converter
        self.sources = []
        self.results = []
        self.errors = []

        # Build the list of sources based on configuration
        self._setup_sources()

    def _setup_sources(self):
        """Create all the source objects based on configuration."""

        # --- MOCK SOURCES (always available, no API keys) ---
        if cfg.MOCK_SOURCE_COUNT > 0:
            mock_source_classes = [
                MockSource_01_AirlineDirect,
                MockSource_02_AggregatorOne,
                MockSource_03_AirlineGerman,
                MockSource_04_BudgetAir,
                MockSource_05_OTAPremium,
                MockSource_06_MetaSearch,
                MockSource_07_AirlinePartner,
                MockSource_08_CorporateTravel,
                MockSource_09_LastMinuteDeals,
                MockSource_10_MultiStop,
            ]

            # Only add as many mock sources as configured
            count = min(cfg.MOCK_SOURCE_COUNT, len(mock_source_classes))
            for i in range(count):
                self.sources.append(mock_source_classes[i]())

        # --- REAL APIS (optional, needs API keys) ---
        if cfg.ENABLE_IGNV:
            self.sources.append(IgnavSource(
                api_key=cfg.IGNV_API_KEY,
            ))

        if cfg.ENABLE_AVIATIONSTACK:
            self.sources.append(AviationStackSource(
                api_key=cfg.AVIATIONSTACK_API_KEY,
            ))

        if cfg.ENABLE_KIWI:
            self.sources.append(KiwiSource(
                api_key=cfg.KIWI_API_KEY,
            ))

        # --- NEW REAL SOURCES (no API keys, direct APIs) ---
        if cfg.ENABLE_GOOGLE_FLIGHTS:
            self.sources.append(GoogleFlightsSource())

        if cfg.ENABLE_RYANAIR:
            self.sources.append(RyanairSource())

        # --- ADDITIONAL FREE APIS ---
        if cfg.ENABLE_WHENTOFLY:
            self.sources.append(WhentoFlySource())

        if cfg.ENABLE_OCTOTRIP:
            self.sources.append(OctoTripSource())

        # --- PLAYWRIGHT SCRAPERS (best-effort) ---
        if cfg.ENABLE_KAYAK:
            self.sources.append(KayakScraper())

        if cfg.ENABLE_SKYSCANNER:
            self.sources.append(SkyscannerScraper())

        if cfg.ENABLE_EXPEDIA:
            self.sources.append(ExpediaScraper())

        if cfg.ENABLE_MOMONDO:
            self.sources.append(MomondoScraper())

        # Report the setup
        print(f"  [SETUP] Total sources configured: {len(self.sources)}")
        for s in self.sources:
            print(f"    - {s.name()}")

    def search_all(self, origin, destination, date, cabin_class):
        """
        Search all sources for flights.
        
        This runs EACH source one at a time.
        If a source fails, we catch the error and move on.
        
        RETURNS:
        - List of FlightData objects from all successful sources
        """
        self.results = []
        self.errors = []

        print(f"\n{'='*60}")
        print(f"  SEARCHING {len(self.sources)} SOURCES")
        print(f"  Route: {origin} -> {destination}")
        print(f"  Date:  {date}")
        print(f"  Cabin: {cabin_class}")
        print(f"{'='*60}\n")

        for source in self.sources:
            try:
                print(f"  [SEARCH] Querying: {source.name()}...")
                flights = source.search(origin, destination, date, cabin_class, self.currency_converter)

                if flights:
                    self.results.extend(flights)
                    print(f"  [OK] {source.name()}: {len(flights)} flights found")
                else:
                    print(f"  [INFO] {source.name()}: No flights returned")

            except Exception as e:
                error_msg = f"{source.name()}: {e}"
                self.errors.append(error_msg)
                print(f"  [ERROR] {error_msg}")
                print(f"  [ERROR] Continuing with other sources...")

        # Post-process: enrich WhentoFly results with flight details from detailed sources
        self._enrich_whentofly()

        enriched = sum(1 for f in self.results if f.source_name == "WhentoFly" and f.flight_number)
        whentofly_total = sum(1 for f in self.results if f.source_name == "WhentoFly")
        if whentofly_total > 0:
            print(f"  [ENRICH] WhentoFly: {enriched}/{whentofly_total} flights enriched with details from other sources")

        print(f"\n{'='*60}")
        print(f"  SEARCH COMPLETE")
        print(f"  Successful: {len(self.results)} flights from "
              f"{len(set(f.source_name for f in self.results))} sources")
        print(f"  Failed:     {len(self.errors)} sources")
        print(f"{'='*60}\n")

        if self.errors:
            print("  Sources that failed:")
            for err in self.errors:
                print(f"    - {err}")
            print()

        return self.results

    def _enrich_whentofly(self):
        """Fill flight_number, departure_time, arrival_time for WhentoFly results
        by matching against detailed sources (Ignav, Google Flights, OctoTrip)."""
        detailed = [f for f in self.results if f.source_name in ("Ignav API", "Google Flights", "OctoTrip")]
        if not detailed:
            return

        for flight in self.results:
            if flight.source_name != "WhentoFly":
                continue
            if flight.flight_number or flight.departure_time:
                continue

            best = None
            best_score = 0
            for cand in detailed:
                # Same route
                if cand.origin != flight.origin or cand.destination != flight.destination:
                    continue
                # Same airline
                if cand.airline != flight.airline:
                    continue
                # Same number of stops
                if cand.stops != flight.stops:
                    continue
                # Price similarity (within 40%)
                if flight.converted_price_base > 0 and cand.converted_price_base > 0:
                    ratio = cand.converted_price_base / flight.converted_price_base
                    if ratio < 0.6 or ratio > 1.4:
                        continue
                score = 100 - abs(1 - (cand.converted_price_base / max(flight.converted_price_base, 0.01))) * 50
                if score > best_score:
                    best_score = score
                    best = cand

            if best:
                flight.flight_number = best.flight_number
                flight.departure_time = best.departure_time
                flight.arrival_time = best.arrival_time
                flight.stop_airports = best.stop_airports
