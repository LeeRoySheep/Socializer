/**
 * Authentication Flow Test
 * 
 * This script helps debug the authentication flow by executing each step
 * and logging detailed information about what's happening.
 */

// Import the auth service
import { authService } from '../auth/AuthService.js';

class AuthFlowTest {
    constructor() {
        this.testUser = {
            username: 'testuser',
            password: 'testpass123'
        };
        this.testResults = [];
    }

    async runTests() {
        try {
            console.log('=== Starting Authentication Flow Test ===');
            
            // 1. Clear existing auth data
            await this.testClearAuthData();
            
            // 2. Test login with invalid credentials
            await this.testInvalidLogin();
            
            // 3. Test login with valid credentials
            await this.testValidLogin();
            
            // 4. Test token storage and retrieval
            await this.testTokenStorage();
            
            // 5. Test authenticated request
            await this.testAuthenticatedRequest();
            
            // 6. Test logout
            await this.testLogout();
            
            console.log('=== Test Results ===');
            this.testResults.forEach((result, index) => {
                console.log(`Test ${index + 1}: ${result.passed ? '✅' : '❌'} ${result.name}`);
                if (!result.passed) {
                    console.log(`   Error: ${result.error}`);
                }
                if (result.details) {
                    console.log(`   Details:`, result.details);
                }
            });
            
        } catch (error) {
            console.error('Test failed with error:', error);
        }
    }
    
    async testClearAuthData() {
        const testName = 'Clear Authentication Data';
        try {
            console.log('\n--- Testing Clear Auth Data ---');
            authService._clearAuthData();
            
            // Verify all storage is cleared
            const localStorageToken = localStorage.getItem(authService.tokenKey);
            const sessionStorageToken = sessionStorage.getItem(authService.tokenKey);
            const cookies = document.cookie;
            
            const details = {
                localStorageCleared: !localStorageToken,
                sessionStorageCleared: !sessionStorageToken,
                cookiesCleared: !cookies.includes('access_token=')
            };
            
            const passed = !localStorageToken && !sessionStorageToken && !cookies.includes('access_token=');
            
            this.testResults.push({
                name: testName,
                passed,
                details
            });
            
            console.log(`${testName}: ${passed ? 'PASSED' : 'FAILED'}`, details);
            
        } catch (error) {
            this.testResults.push({
                name: testName,
                passed: false,
                error: error.message
            });
            console.error(`${testName} failed:`, error);
        }
    }
    
    async testInvalidLogin() {
        const testName = 'Invalid Login Attempt';
        try {
            console.log('\n--- Testing Invalid Login ---');
            
            try {
                await authService.login('invalid', 'credentials');
                // If we get here, login didn't throw an error as expected
                throw new Error('Login with invalid credentials did not fail');
            } catch (error) {
                const passed = error.message.includes('Login failed') || 
                             error.message.includes('Invalid credentials') ||
                             error.message.includes('401');
                
                this.testResults.push({
                    name: testName,
                    passed,
                    details: {
                        expectedError: true,
                        receivedError: error.message
                    }
                });
                
                console.log(`${testName}: ${passed ? 'PASSED' : 'FAILED'}`, error.message);
            }
            
        } catch (error) {
            this.testResults.push({
                name: testName,
                passed: false,
                error: error.message
            });
            console.error(`${testName} failed:`, error);
        }
    }
    
    async testValidLogin() {
        const testName = 'Valid Login';
        try {
            console.log('\n--- Testing Valid Login ---');
            
            // First clear any existing auth data
            authService._clearAuthData();
            
            // Perform login
            const user = await authService.login(this.testUser.username, this.testUser.password);
            
            // Verify login was successful
            const token = authService.getToken();
            const isAuthenticated = authService.isAuthenticated();
            const cookies = document.cookie;
            
            const details = {
                user: user ? 'User object received' : 'No user object',
                hasToken: !!token,
                tokenLength: token ? token.length : 0,
                isAuthenticated,
                hasCookie: cookies.includes('access_token=')
            };
            
            const passed = !!user && !!token && isAuthenticated && details.hasCookie;
            
            this.testResults.push({
                name: testName,
                passed,
                details
            });
            
            console.log(`${testName}: ${passed ? 'PASSED' : 'FAILED'}`, details);
            
        } catch (error) {
            this.testResults.push({
                name: testName,
                passed: false,
                error: error.message
            });
            console.error(`${testName} failed:`, error);
        }
    }
    
    async testTokenStorage() {
        const testName = 'Token Storage Verification';
        try {
            console.log('\n--- Testing Token Storage ---');
            
            const token = authService.getToken();
            if (!token) {
                throw new Error('No token found, login may have failed');
            }
            
            // Check token in different storage locations
            const localStorageToken = localStorage.getItem(authService.tokenKey);
            const sessionStorageToken = sessionStorage.getItem(authService.tokenKey);
            const cookies = document.cookie;
            
            const details = {
                memoryToken: token ? `Token exists (${token.length} chars)` : 'No token',
                localStorageMatch: localStorageToken === token,
                sessionStorageMatch: sessionStorageToken === token,
                hasCookie: cookies.includes('access_token='),
                cookieHasBearer: cookies.includes('Bearer%20')
            };
            
            const passed = details.localStorageMatch && 
                          details.sessionStorageMatch && 
                          details.hasCookie &&
                          details.cookieHasBearer;
            
            this.testResults.push({
                name: testName,
                passed,
                details
            });
            
            console.log(`${testName}: ${passed ? 'PASSED' : 'FAILED'}`, details);
            
        } catch (error) {
            this.testResults.push({
                name: testName,
                passed: false,
                error: error.message
            });
            console.error(`${testName} failed:`, error);
        }
    }
    
    async testAuthenticatedRequest() {
        const testName = 'Authenticated Request';
        try {
            console.log('\n--- Testing Authenticated Request ---');
            
            if (!authService.isAuthenticated()) {
                throw new Error('Not authenticated, cannot test authenticated request');
            }
            
            // Make a request to a protected endpoint
            const response = await authService.fetchWithAuth('/api/users/me');
            const userData = await response.json();
            
            const details = {
                status: response.status,
                userData: userData ? 'Received user data' : 'No user data',
                username: userData?.username || 'N/A'
            };
            
            const passed = response.ok && userData && userData.username;
            
            this.testResults.push({
                name: testName,
                passed,
                details
            });
            
            console.log(`${testName}: ${passed ? 'PASSED' : 'FAILED'}`, details);
            
        } catch (error) {
            this.testResults.push({
                name: testName,
                passed: false,
                error: error.message,
                details: error.response ? {
                    status: error.response.status,
                    statusText: error.response.statusText
                } : undefined
            });
            console.error(`${testName} failed:`, error);
        }
    }
    
    async testLogout() {
        const testName = 'Logout';
        try {
            console.log('\n--- Testing Logout ---');
            
            await authService.logout();
            
            // Verify all auth data is cleared
            const token = authService.getToken();
            const isAuthenticated = authService.isAuthenticated();
            const cookies = document.cookie;
            
            const details = {
                tokenCleared: !token,
                isAuthenticated,
                cookiesCleared: !cookies.includes('access_token=')
            };
            
            const passed = !token && !isAuthenticated && details.cookiesCleared;
            
            this.testResults.push({
                name: testName,
                passed,
                details
            });
            
            console.log(`${testName}: ${passed ? 'PASSED' : 'FAILED'}`, details);
            
        } catch (error) {
            this.testResults.push({
                name: testName,
                passed: false,
                error: error.message
            });
            console.error(`${testName} failed:`, error);
        }
    }
}

// Run the tests when the page loads
window.addEventListener('load', () => {
    const testButton = document.createElement('button');
    testButton.textContent = 'Run Auth Tests';
    testButton.style.position = 'fixed';
    testButton.style.bottom = '20px';
    testButton.style.right = '20px';
    testButton.style.zIndex = '9999';
    testButton.style.padding = '10px 20px';
    testButton.style.backgroundColor: '#4CAF50';
    testButton.style.color: 'white';
    testButton.style.border: 'none';
    testButton.style.borderRadius: '4px';
    testButton.style.cursor = 'pointer';
    
    testButton.addEventListener('click', () => {
        const test = new AuthFlowTest();
        test.runTests();
    });
    
    document.body.appendChild(testButton);
});

// Export for testing purposes
export default AuthFlowTest;
