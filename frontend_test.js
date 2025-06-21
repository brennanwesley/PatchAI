#!/usr/bin/env node
/**
 * Frontend Console Error Detection Script
 * Runs headless browser to detect JavaScript errors before deployment
 */

const puppeteer = require('puppeteer');
const fs = require('fs');

class FrontendTester {
    constructor() {
        this.errors = [];
        this.warnings = [];
        this.networkErrors = [];
        this.consoleMessages = [];
    }

    async testFrontend(url = 'https://patchai-frontend.vercel.app') {
        console.log('🧪 TESTING FRONTEND FOR CONSOLE ERRORS');
        console.log('=' .repeat(50));
        
        const browser = await puppeteer.launch({ 
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        
        try {
            const page = await browser.newPage();
            
            // Capture console messages
            page.on('console', (msg) => {
                const message = {
                    type: msg.type(),
                    text: msg.text(),
                    location: msg.location(),
                    timestamp: new Date().toISOString()
                };
                
                this.consoleMessages.push(message);
                
                if (msg.type() === 'error') {
                    this.errors.push(message);
                    console.log(`❌ CONSOLE ERROR: ${msg.text()}`);
                } else if (msg.type() === 'warning') {
                    this.warnings.push(message);
                    console.log(`⚠️  CONSOLE WARNING: ${msg.text()}`);
                }
            });
            
            // Capture network failures
            page.on('requestfailed', (request) => {
                const error = {
                    url: request.url(),
                    method: request.method(),
                    failure: request.failure().errorText,
                    timestamp: new Date().toISOString()
                };
                
                this.networkErrors.push(error);
                console.log(`🌐 NETWORK ERROR: ${request.method()} ${request.url()} - ${request.failure().errorText}`);
            });
            
            // Capture response errors
            page.on('response', (response) => {
                if (response.status() >= 400) {
                    const error = {
                        url: response.url(),
                        status: response.status(),
                        statusText: response.statusText(),
                        timestamp: new Date().toISOString()
                    };
                    
                    this.networkErrors.push(error);
                    console.log(`🌐 HTTP ERROR: ${response.status()} ${response.url()}`);
                }
            });
            
            console.log(`📱 Loading: ${url}`);
            
            // Navigate to the page
            await page.goto(url, { 
                waitUntil: 'networkidle2',
                timeout: 30000 
            });
            
            // Wait for React to load
            await page.waitForTimeout(3000);
            
            // Try to interact with the page
            try {
                // Check if main elements exist
                await page.waitForSelector('body', { timeout: 5000 });
                console.log('✅ Page body loaded');
                
                // Check for common React error boundaries
                const errorBoundary = await page.$('.error-boundary, [data-testid="error-boundary"]');
                if (errorBoundary) {
                    console.log('❌ React Error Boundary detected');
                    this.errors.push({
                        type: 'error',
                        text: 'React Error Boundary detected',
                        location: { url },
                        timestamp: new Date().toISOString()
                    });
                }
                
                // Check for authentication elements
                const authElements = await page.evaluate(() => {
                    return {
                        hasLoginButton: !!document.querySelector('[data-testid="login"], button:contains("Login"), button:contains("Sign In")'),
                        hasUserMenu: !!document.querySelector('[data-testid="user-menu"], .user-menu'),
                        hasAuthError: !!document.querySelector('.auth-error, [data-testid="auth-error"]')
                    };
                });
                
                console.log('🔐 Auth Elements:', authElements);
                
                // Try to trigger chat functionality
                const chatInput = await page.$('textarea, input[placeholder*="message"], input[placeholder*="chat"]');
                if (chatInput) {
                    console.log('✅ Chat input found');
                    
                    // Try to type a message
                    await chatInput.type('test message');
                    await page.waitForTimeout(1000);
                    
                    // Look for send button
                    const sendButton = await page.$('button[type="submit"], button:contains("Send"), [data-testid="send-button"]');
                    if (sendButton) {
                        console.log('✅ Send button found');
                        // Don't actually send to avoid API calls
                    }
                } else {
                    console.log('⚠️  No chat input found');
                }
                
            } catch (interactionError) {
                console.log('⚠️  Interaction test failed:', interactionError.message);
            }
            
            // Wait a bit more for any async errors
            await page.waitForTimeout(2000);
            
        } finally {
            await browser.close();
        }
        
        this.generateReport();
        return this.errors.length === 0;
    }
    
    generateReport() {
        console.log('\n' + '='.repeat(50));
        console.log('📊 FRONTEND TEST REPORT');
        console.log('='.repeat(50));
        
        console.log(`❌ Console Errors: ${this.errors.length}`);
        console.log(`⚠️  Console Warnings: ${this.warnings.length}`);
        console.log(`🌐 Network Errors: ${this.networkErrors.length}`);
        console.log(`📝 Total Console Messages: ${this.consoleMessages.length}`);
        
        if (this.errors.length > 0) {
            console.log('\n🚨 CRITICAL ERRORS:');
            this.errors.forEach((error, index) => {
                console.log(`${index + 1}. ${error.text}`);
                if (error.location && error.location.url) {
                    console.log(`   Location: ${error.location.url}:${error.location.lineNumber || '?'}`);
                }
            });
        }
        
        if (this.networkErrors.length > 0) {
            console.log('\n🌐 NETWORK ISSUES:');
            this.networkErrors.forEach((error, index) => {
                console.log(`${index + 1}. ${error.url} - ${error.failure || error.status}`);
            });
        }
        
        // Save detailed report
        const report = {
            timestamp: new Date().toISOString(),
            summary: {
                errors: this.errors.length,
                warnings: this.warnings.length,
                networkErrors: this.networkErrors.length,
                totalMessages: this.consoleMessages.length
            },
            errors: this.errors,
            warnings: this.warnings,
            networkErrors: this.networkErrors,
            allMessages: this.consoleMessages
        };
        
        fs.writeFileSync('frontend_test_report.json', JSON.stringify(report, null, 2));
        console.log('\n📄 Detailed report saved to: frontend_test_report.json');
        
        if (this.errors.length === 0) {
            console.log('\n✅ NO CRITICAL ERRORS DETECTED');
        } else {
            console.log('\n❌ CRITICAL ERRORS DETECTED - FIX BEFORE DEPLOYMENT');
        }
    }
}

// Run the test
async function main() {
    const tester = new FrontendTester();
    
    // Test production frontend
    const success = await tester.testFrontend();
    
    process.exit(success ? 0 : 1);
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = FrontendTester;
