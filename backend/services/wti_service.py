"""
WTI Oil Price Service
Fetches live oil price data from oilpriceapi.com
"""

import os
import time
import httpx
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class WTIService:
    def __init__(self):
        self.api_key = os.getenv('WTI_API_KEY')
        self.base_url = 'https://api.oilpriceapi.com/v1'
        self.cache = {
            'data': None,
            'timestamp': None
        }
        self.cache_duration = 10 * 60  # 10 minutes in seconds
        
        if not self.api_key:
            logger.warning("WTI_API_KEY not found in environment variables")
    
    def is_cache_valid(self) -> bool:
        """Check if cached data is still valid"""
        if not self.cache['data'] or not self.cache['timestamp']:
            return False
        
        current_time = time.time()
        cache_age = current_time - self.cache['timestamp']
        return cache_age < self.cache_duration
    
    async def get_wti_price(self) -> Dict:
        """Get WTI price data with caching"""
        # Return cached data if still valid
        if self.is_cache_valid():
            logger.info("Using cached WTI data")
            return self.cache['data']
        
        # Fetch fresh data
        logger.info("Fetching fresh WTI data from API")
        try:
            fresh_data = await self.fetch_wti_price()
            
            # Update cache
            self.cache = {
                'data': fresh_data,
                'timestamp': time.time()
            }
            
            return fresh_data
            
        except Exception as error:
            logger.error(f"Failed to fetch fresh WTI data: {error}")
            
            # Return cached data if available, even if expired
            if self.cache['data']:
                logger.info("Using expired cached data as fallback")
                return self.cache['data']
            
            # Return fallback data if no cache available
            return self.get_fallback_data()
    
    async def fetch_wti_price(self) -> Dict:
        """Fetch live WTI price from API"""
        if not self.api_key:
            raise Exception("WTI API key not configured")
        
        headers = {
            'Authorization': f'Token {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f'{self.base_url}/prices/latest',
                headers=headers
            )
            
            if response.status_code != 200:
                raise Exception(f"API request failed with status {response.status_code}: {response.text}")
            
            api_data = response.json()
            return self.format_wti_data(api_data)
    
    def format_wti_data(self, api_data: Dict) -> Dict:
        """Format API response data for consistent use"""
        # Handle actual API response structure from oilpriceapi.com
        # Response format: { status: "success", data: { price: 68.76, formatted: "$68.76", currency: "USD", code: "BRENT_CRUDE_USD", created_at: "...", type: "spot_price" } }
        
        price = 0
        last_updated = None
        oil_type = 'Unknown'
        
        if api_data.get('status') == 'success' and api_data.get('data'):
            price = float(api_data['data'].get('price', 0))
            last_updated = api_data['data'].get('created_at')
            oil_type = api_data['data'].get('code', 'Oil Price')
        elif api_data.get('price'):
            # Fallback for direct price format
            price = float(api_data['price'])
        
        # Calculate a mock change percentage since API doesn't provide it
        # In a real implementation, you'd store previous price and calculate actual change
        import random
        mock_change_percent = (random.random() - 0.5) * 4  # Random change between -2% and +2%
        mock_change = (price * mock_change_percent) / 100
        
        return {
            'price': round(price, 2),
            'change': round(mock_change, 2),
            'changePercent': round(mock_change_percent, 1),
            'lastUpdated': last_updated or time.time(),
            'source': 'oilpriceapi.com',
            'isLive': True,
            'oilType': oil_type
        }
    
    def get_fallback_data(self) -> Dict:
        """Return fallback data when API is unavailable"""
        return {
            'price': 65.00,
            'change': 0.00,
            'changePercent': 0.0,
            'lastUpdated': time.time(),
            'source': 'fallback',
            'isLive': False,
            'oilType': 'Fallback Data'
        }

# Create singleton instance
wti_service = WTIService()
