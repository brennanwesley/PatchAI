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
    // Note: Adjust this based on actual API response structure
    // This is a best-guess format based on typical oil price APIs
    const wtiData = apiData.data?.prices?.WTI || apiData.prices?.WTI || apiData.WTI || apiData;
    
    return {
      price: parseFloat(wtiData.price || wtiData.value || 0),
      change: parseFloat(wtiData.change || 0),
      changePercent: parseFloat(wtiData.change_percent || wtiData.changePercent || 0),
      lastUpdated: new Date().toISOString(),
      source: 'oilpriceapi.com',
      isLive: true
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
