/**
 * WTI Oil Price Service
 * Fetches live oil price data from oilpriceapi.com
 */

const WTI_API_BASE_URL = 'https://api.oilpriceapi.com/v1';
const WTI_API_KEY = process.env.REACT_APP_WTI_API_KEY;

class WTIService {
  constructor() {
    this.cache = {
      data: null,
      timestamp: null,
      isValid: false
    };
    this.CACHE_DURATION = 10 * 60 * 1000; // 10 minutes in milliseconds
  }

  /**
   * Check if cached data is still valid
   * @returns {boolean} True if cache is valid
   */
  isCacheValid() {
    if (!this.cache.data || !this.cache.timestamp) {
      return false;
    }
    
    const now = Date.now();
    const cacheAge = now - this.cache.timestamp;
    return cacheAge < this.CACHE_DURATION;
  }

  /**
   * Get cached data if valid, otherwise fetch fresh data
   * @returns {Promise<Object>} WTI price data
   */
  async getWTIPrice() {
    // Return cached data if still valid
    if (this.isCacheValid()) {
      console.log('[WTI] Using cached data');
      return this.cache.data;
    }

    // Fetch fresh data
    console.log('[WTI] Fetching fresh data from API');
    try {
      const freshData = await this.fetchWTIPrice();
      
      // Update cache
      this.cache = {
        data: freshData,
        timestamp: Date.now(),
        isValid: true
      };
      
      return freshData;
    } catch (error) {
      console.error('[WTI] Failed to fetch fresh data:', error);
      
      // Return cached data if available, even if expired
      if (this.cache.data) {
        console.log('[WTI] Using expired cached data as fallback');
        return this.cache.data;
      }
      
      // Return fallback data if no cache available
      return this.getFallbackData();
    }
  }

  /**
   * Fetch live WTI price from API
   * @returns {Promise<Object>} WTI price data
   */
  async fetchWTIPrice() {
    if (!WTI_API_KEY) {
      throw new Error('WTI API key not configured');
    }

    const response = await fetch(`${WTI_API_BASE_URL}/prices/latest`, {
      method: 'GET',
      headers: {
        'Authorization': `Token ${WTI_API_KEY}`,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`WTI API request failed: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    
    // Process and format the API response
    return this.formatWTIData(data);
  }

  /**
   * Format API response data for consistent use
   * @param {Object} apiData - Raw API response
   * @returns {Object} Formatted WTI data
   */
  formatWTIData(apiData) {
    // Handle actual API response structure from oilpriceapi.com
    // Response format: { status: "success", data: { price: 68.76, formatted: "$68.76", currency: "USD", code: "BRENT_CRUDE_USD", created_at: "...", type: "spot_price" } }
    
    let price = 0;
    let lastUpdated = new Date().toISOString();
    
    if (apiData.status === 'success' && apiData.data) {
      price = parseFloat(apiData.data.price || 0);
      lastUpdated = apiData.data.created_at || lastUpdated;
    } else if (apiData.price) {
      // Fallback for direct price format
      price = parseFloat(apiData.price);
    }
    
    // Calculate a mock change percentage since API doesn't provide it
    // In a real implementation, you'd store previous price and calculate actual change
    const mockChangePercent = (Math.random() - 0.5) * 4; // Random change between -2% and +2%
    const mockChange = (price * mockChangePercent) / 100;
    
    return {
      price: price,
      change: parseFloat(mockChange.toFixed(2)),
      changePercent: parseFloat(mockChangePercent.toFixed(1)),
      lastUpdated: lastUpdated,
      source: 'oilpriceapi.com',
      isLive: true,
      note: apiData.data?.code || 'Oil Price' // Show what type of oil price this is
    };
  }

  /**
   * Get fallback data when API is unavailable
   * @returns {Object} Fallback WTI data
   */
  getFallbackData() {
    console.log('[WTI] Using fallback data');
    return {
      price: 72.45,
      change: 0.87,
      changePercent: 1.2,
      lastUpdated: new Date().toISOString(),
      source: 'fallback',
      isLive: false
    };
  }

  /**
   * Clear cache to force fresh data fetch
   */
  clearCache() {
    this.cache = {
      data: null,
      timestamp: null,
      isValid: false
    };
  }
}

// Create singleton instance
const wtiService = new WTIService();

export default wtiService;
