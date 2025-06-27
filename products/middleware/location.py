# middleware/location.py - Location detection and currency middleware
import requests
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from utils.currency import get_location_currency, set_user_currency
import logging

logger = logging.getLogger(__name__)

class LocationMiddleware(MiddlewareMixin):
    """Middleware to detect user location and set appropriate currency"""
    
    def process_request(self, request):
        # Skip location detection for admin, static files, etc.
        if (request.path.startswith('/admin/') or 
            request.path.startswith('/static/') or
            request.path.startswith('/media/')):
            return None
        
        # Check if location is already determined
        if 'location_detected' in request.session:
            return None
        
        # Get user's IP address
        ip_address = self.get_client_ip(request)
        
        if ip_address and not self.is_local_ip(ip_address):
            location_data = self.get_location_from_ip(ip_address)
            if location_data:
                country_code = location_data.get('country_code', 'US')
                country_name = location_data.get('country_name', 'United States')
                
                # Store location in session
                request.session['country_code'] = country_code
                request.session['country_name'] = country_name
                request.session['location_detected'] = True
                
                # Set currency based on location if not already set
                if 'currency' not in request.session:
                    currency = get_location_currency(country_code)
                    set_user_currency(request, currency)
                
                logger.info(f"Location detected: {country_name} ({country_code})")
        else:
            # Default to US if IP detection fails
            request.session.setdefault('country_code', 'US')
            request.session.setdefault('country_name', 'United States')
            request.session.setdefault('currency', 'USD')
            request.session['location_detected'] = True
        
        return None
    
    def get_client_ip(self, request):
        """Get real IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_local_ip(self, ip):
        """Check if IP is local/private"""
        if not ip:
            return True
        
        # Common local IP patterns
        local_patterns = [
            '127.', '192.168.', '10.', '172.16.', '172.17.', '172.18.',
            '172.19.', '172.20.', '172.21.', '172.22.', '172.23.',
            '172.24.', '172.25.', '172.26.', '172.27.', '172.28.',
            '172.29.', '172.30.', '172.31.', 'localhost'
        ]
        
        return any(ip.startswith(pattern) for pattern in local_patterns)
    
    def get_location_from_ip(self, ip_address):
        """Get location data from IP address using free API"""
        cache_key = f"location_{ip_address}"
        location_data = cache.get(cache_key)
        
        if location_data is None:
            try:
                # Using ipapi.co (free tier: 1000 requests/day)
                url = f"https://ipapi.co/{ip_address}/json/"
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                data = response.json()
                
                if 'error' not in data:
                    location_data = {
                        'country_code': data.get('country_code', 'US'),
                        'country_name': data.get('country_name', 'United States'),
                        'city': data.get('city', ''),
                        'region': data.get('region', ''),
                    }
                    
                    # Cache for 24 hours
                    cache.set(cache_key, location_data, 86400)
                else:
                    logger.warning(f"IP location API error: {data.get('reason', 'Unknown')}")
                    return None
                    
            except Exception as e:
                logger.error(f"Failed to get location for IP {ip_address}: {e}")
                return None
        
        return location_data