# utils/currency.py - Currency conversion utilities
import requests
from decimal import Decimal
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

# Currency symbols and formatting
CURRENCY_SYMBOLS = {
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
}

CURRENCY_NAMES = {
    'USD': 'US Dollar',
    'EUR': 'Euro',
    'GBP': 'British Pound',
}

# Default exchange rates (fallback values)
DEFAULT_RATES = {
    'USD': 1.0,
    'EUR': 0.85,
    'GBP': 0.75,
}

class CurrencyConverter:
    def __init__(self):
        self.base_currency = 'USD'
        self.cache_timeout = 3600  # 1 hour
    
    def get_exchange_rates(self):
        """Get current exchange rates from API or cache"""
        cache_key = 'exchange_rates'
        rates = cache.get(cache_key)
        
        if rates is None:
            try:
                # Using exchangerate-api.com (free tier)
                # You can replace this with your preferred API
                api_key = getattr(settings, 'EXCHANGE_RATE_API_KEY', '')
                if api_key:
                    url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/USD"
                else:
                    # Free tier without API key
                    url = "https://api.exchangerate-api.com/v4/latest/USD"
                
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                rates = {
                    'USD': 1.0,
                    'EUR': data['rates'].get('EUR', DEFAULT_RATES['EUR']),
                    'GBP': data['rates'].get('GBP', DEFAULT_RATES['GBP']),
                }
                
                cache.set(cache_key, rates, self.cache_timeout)
                logger.info("Exchange rates updated successfully")
                
            except Exception as e:
                logger.error(f"Failed to fetch exchange rates: {e}")
                rates = DEFAULT_RATES
        
        return rates
    
    def convert(self, amount, from_currency, to_currency):
        """Convert amount from one currency to another"""
        if from_currency == to_currency:
            return Decimal(str(amount))
        
        rates = self.get_exchange_rates()
        
        # Convert to USD first, then to target currency
        if from_currency != 'USD':
            amount_usd = Decimal(str(amount)) / Decimal(str(rates[from_currency]))
        else:
            amount_usd = Decimal(str(amount))
        
        if to_currency != 'USD':
            converted_amount = amount_usd * Decimal(str(rates[to_currency]))
        else:
            converted_amount = amount_usd
        
        return converted_amount.quantize(Decimal('0.01'))
    
    def format_price(self, amount, currency):
        """Format price with currency symbol"""
        symbol = CURRENCY_SYMBOLS.get(currency, currency)
        
        # Format based on currency conventions
        if currency == 'EUR':
            return f"{amount:.2f} {symbol}"
        else:
            return f"{symbol}{amount:.2f}"

# Global converter instance
converter = CurrencyConverter()

def get_user_currency(request):
    """Get user's preferred currency from session or location"""
    return request.session.get('currency', 'USD')

def set_user_currency(request, currency):
    """Set user's preferred currency in session"""
    if currency in CURRENCY_SYMBOLS:
        request.session['currency'] = currency
        return True
    return False

def get_location_currency(country_code):
    """Get default currency based on country code"""
    currency_map = {
        'US': 'USD',
        'UK': 'GBP',
        'GB': 'GBP',
        'DE': 'EUR',
        'FR': 'EUR',
        'IT': 'EUR',
        'ES': 'EUR',
        'NL': 'EUR',
        'AT': 'EUR',
        'BE': 'EUR',
        'FI': 'EUR',
        'IE': 'EUR',
        'LU': 'EUR',
        'PT': 'EUR',
        'SI': 'EUR',
        'SK': 'EUR',
        'EE': 'EUR',
        'LV': 'EUR',
        'LT': 'EUR',
        'MT': 'EUR',
        'CY': 'EUR',
    }
    return currency_map.get(country_code.upper(), 'USD')