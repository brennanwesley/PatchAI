// Simple event emitter for paywall events
class PaywallEventEmitter {
  constructor() {
    this.listeners = [];
  }

  subscribe(callback) {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter(listener => listener !== callback);
    };
  }

  emit(eventType, data) {
    this.listeners.forEach(callback => {
      try {
        callback(eventType, data);
      } catch (error) {
        console.error('Error in paywall event listener:', error);
      }
    });
  }
}

export const paywallEvents = new PaywallEventEmitter();

// Event types
export const PAYWALL_EVENTS = {
  SHOW_PAYWALL: 'SHOW_PAYWALL',
  HIDE_PAYWALL: 'HIDE_PAYWALL',
  PAYMENT_REQUIRED: 'PAYMENT_REQUIRED'
};
