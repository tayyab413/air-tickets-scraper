"""
Currency conversion utilities.
Converts prices from different currencies into one base currency for fair comparison.

HOW CURRENCY CONVERSION WORKS:
Imagine you have 3 flight prices:
  - Flight A: 100 GBP (British Pounds)
  - Flight B: 120 EUR (Euros)
  - Flight C: 130 USD (US Dollars)

You cannot just compare 100 vs 120 vs 130 because they're in different currencies.
100 GBP might be worth 116 EUR, making it the cheapest when converted fairly.

HOW WE SOLVE THIS:
1. Pick one "base" currency (EUR by default)
2. Find the exchange rate for each currency against EUR
   - Example: 1 EUR = 0.86 GBP, so 1 GBP = 1/0.86 = 1.163 EUR
3. Convert every price to EUR:
   - 100 GBP / 0.86 = 116.28 EUR
   - 120 EUR / 1.0 = 120.00 EUR
   - 130 USD / 1.08 = 120.37 EUR
4. Now we can fairly compare: 116.28 < 120.00 < 120.37

THE FORMULA:
  converted_price = original_price / exchange_rate
  where exchange_rate = "how many units of the foreign currency for 1 EUR"

So if 1 EUR = 0.86 GBP, then exchange_rate for GBP = 0.86
  100 GBP / 0.86 = 116.28 EUR

WHERE DO EXCHANGE RATES COME FROM?
1. First try: a free live API (open.er-api.com) - gives current rates
2. Fallback: hardcoded rates (not as current, but always available)

WHAT WE STORE:
- original_price: the price as given by the source (e.g., 100 GBP)
- original_currency: the currency from the source (e.g., "GBP")
- base_currency: our comparison currency (e.g., "EUR")  
- exchange_rate_used: the rate we used (e.g., 0.86)
- converted_price_base: the converted price (e.g., 116.28 EUR)
"""

import requests

# ============================================================
# FALLBACK EXCHANGE RATES
# ============================================================
# These are used if the live API is not available.
# Each rate tells us: "1 EUR = X of this currency"
# Example: 1 EUR = 0.86 GBP, so GBP rate is 0.86
#
# We keep these updated with reasonable approximate values.
# You can manually update them if needed.

FALLBACK_RATES = {
    "EUR": 1.0,
    "GBP": 0.86,      # 1 EUR = 0.86 GBP (British Pound)
    "USD": 1.08,      # 1 EUR = 1.08 USD (US Dollar)
    "CHF": 0.96,      # 1 EUR = 0.96 CHF (Swiss Franc)
    "SEK": 11.30,     # 1 EUR = 11.30 SEK (Swedish Krona)
    "NOK": 11.50,     # 1 EUR = 11.50 NOK (Norwegian Krone)
    "DKK": 7.46,      # 1 EUR = 7.46 DKK (Danish Krone)
    "PLN": 4.35,      # 1 EUR = 4.35 PLN (Polish Zloty)
    "CZK": 24.50,     # 1 EUR = 24.50 CZK (Czech Koruna)
    "HUF": 385.0,     # 1 EUR = 385.00 HUF (Hungarian Forint)
    "CAD": 1.60,      # 1 EUR = 1.60 CAD (Canadian Dollar) — live: 1.6045 (Jul 2026)
    "AUD": 1.63,      # 1 EUR = 1.63 AUD (Australian Dollar)
    "JPY": 186.0,     # 1 EUR = 186.00 JPY (Japanese Yen) — live: 186.43 (Jul 2026)
    "CNY": 7.85,      # 1 EUR = 7.85 CNY (Chinese Yuan)
    "INR": 89.5,      # 1 EUR = 89.50 INR (Indian Rupee)
    "TRY": 54.0,      # 1 EUR = 54.00 TRY (Turkish Lira) — live: 53.92 (Jul 2026)
    "BRL": 5.35,      # 1 EUR = 5.35 BRL (Brazilian Real)
    "ZAR": 20.0,      # 1 EUR = 20.00 ZAR (South African Rand)
    "MXN": 18.5,      # 1 EUR = 18.50 MXN (Mexican Peso)
    "SGD": 1.45,      # 1 EUR = 1.45 SGD (Singapore Dollar)
    "HKD": 8.45,      # 1 EUR = 8.45 HKD (Hong Kong Dollar)
    "KRW": 1350.0,    # 1 EUR = 1350.00 KRW (South Korean Won)
    "NZD": 1.74,      # 1 EUR = 1.74 NZD (New Zealand Dollar)
    "AED": 3.97,      # 1 EUR = 3.97 AED (UAE Dirham)
    "SAR": 4.05,      # 1 EUR = 4.05 SAR (Saudi Riyal)
}


class ExchangeRateFetcher:
    """
    Fetches exchange rates and converts prices.
    
    Usage:
        converter = ExchangeRateFetcher(base_currency="EUR")
        converted_price, rate = converter.convert(100, "GBP")
        # Returns (116.28, 0.86) - 100 GBP = 116.28 EUR
    """

    def __init__(self, base_currency="EUR"):
        self.base_currency = base_currency.upper()
        self.rates = {}          # Dictionary of currency -> rate
        self.rates_loaded = False
        self.rate_source = "none"  # Tells us where rates came from

    def load_rates(self):
        """
        Load exchange rates.
        
        Step 1: Try the free live API (open.er-api.com)
        Step 2: If that fails, use hardcoded fallback rates
        
        The API endpoint returns something like:
        {
            "result": "success",
            "base_code": "EUR",
            "rates": {
                "GBP": 0.86,
                "USD": 1.08,
                ...
            }
        }
        """
        # Try the live API first
        try:
            url = f"https://open.er-api.com/v6/latest/{self.base_currency}"
            print(f"  [CURRENCY] Fetching live exchange rates from: {url}")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("result") == "success":
                    self.rates = data["rates"]
                    self.rate_source = "live (open.er-api.com)"
                    self.rates_loaded = True
                    print(f"  [CURRENCY] Loaded {len(self.rates)} exchange rates from live API")
                    return
                else:
                    print(f"  [CURRENCY] API returned error: {data.get('error-type', 'unknown')}")
            else:
                print(f"  [CURRENCY] API returned status {response.status_code}")
        except requests.exceptions.Timeout:
            print("  [CURRENCY] Live API timed out (no internet? slow connection?)")
        except requests.exceptions.ConnectionError:
            print("  [CURRENCY] Live API connection failed (are you offline?)")
        except Exception as e:
            print(f"  [CURRENCY] Live API error: {e}")

        # Fallback to hardcoded rates
        print("  [CURRENCY] Using fallback (hardcoded) exchange rates")
        print("  [CURRENCY] These are approximate and may not be current")
        self.rates = FALLBACK_RATES.copy()
        self.rate_source = "fallback (hardcoded)"
        self.rates_loaded = True

    def convert(self, amount, from_currency):
        """
        Convert an amount from one currency to the base currency.
        
        PARAMETERS:
        - amount: the price to convert (e.g., 100.00)
        - from_currency: the currency code (e.g., "GBP")
        
        RETURNS:
        - (converted_price, exchange_rate)
        
        EXAMPLE:
        convert(100, "GBP") where base is EUR and rate is 0.86
        => (116.28, 0.86)
        
        HOW THE MATH WORKS:
        - Rate of 0.86 means: 1 EUR = 0.86 GBP
        - So 1 GBP = 1/0.86 = 1.163 EUR
        - 100 GBP = 100 / 0.86 = 116.28 EUR
        
        KEY INSIGHT: We divide by the rate, not multiply.
        Because the rate tells us "how many GBP for 1 EUR".
        To go FROM GBP TO EUR, we divide.
        """
        if not self.rates_loaded:
            self.load_rates()

        # Make sure the currency code is uppercase
        from_currency = from_currency.upper()

        # If same currency, no conversion needed
        if from_currency == self.base_currency:
            return round(amount, 2), 1.0

        # Look up the exchange rate
        rate = self.rates.get(from_currency)
        if rate is None:
            print(f"  [WARNING] No exchange rate found for '{from_currency}'")
            print(f"  [WARNING] Using rate of 1.0 (treating as equal to {self.base_currency})")
            return round(amount, 2), 1.0

        # Convert: divide by the rate
        # Example: 100 GBP / 0.86 = 116.28 EUR
        converted = amount / rate

        return round(converted, 2), rate
