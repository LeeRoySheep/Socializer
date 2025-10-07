/**
 * Authentication Service
 * Handles all authentication-related functionality
 */
class AuthService {
    constructor() {
        this.baseUrl = '';  // Changed from '/api' to '' since /token is at root level
        this.tokenKey = 'auth_token';
        this.currentUser = null;
    }

    /**
     * Get the current authentication token
     * @returns {Object|null} Token data or null if not authenticated
     */
    getToken() {
        const tokenStr = localStorage.getItem(this.tokenKey);
        if (!tokenStr) return null;
        
        try {
            return JSON.parse(tokenStr);
        } catch (e) {
            console.error('Failed to parse token data:', e);
            return null;
        }
    }

    /**
     * Get the authorization header for authenticated requests
     * @returns {Object} Headers object with Authorization if authenticated
     */
    getAuthHeader() {
        const tokenData = this.getToken();
        if (!tokenData) return {};
        
        return {
            'Authorization': `Bearer ${tokenData.access_token}`,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
    }

    /**
     * Check if the user is authenticated
     * @returns {boolean} True if authenticated, false otherwise
     */
    isAuthenticated() {
        const tokenData = this.getToken();
        if (!tokenData) return false;
        
        // Check if token is expired
        if (tokenData.expires_at && Date.now() >= tokenData.expires_at * 1000) {
            this._clearAuthData();
            return false;
        }
        
        return true;
    }

    /**
     * Attempt to log in with username and password
     * @param {string} username 
     * @param {string} password 
     * @returns {Promise<Object>} User data if successful
     */
    async login(username, password) {
        try {
            // Create form data for the token request
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);
            formData.append('grant_type', 'password');
            
            // Request token from the /token endpoint
            const response = await fetch(`${this.baseUrl}/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                },
                body: formData,
                credentials: 'include' // Important for cookies if using session-based auth
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Login failed');
            }

            const tokenData = await response.json();
            console.log('Token received:', {
                ...tokenData,
                access_token: tokenData.access_token ? '***' + tokenData.access_token.slice(-10) : 'none'
            });
            
            // Store token data
            const tokenToStore = {
                access_token: tokenData.access_token,
                token_type: tokenData.token_type || 'bearer',
                expires_in: tokenData.expires_in || 3600,
                created_at: Math.floor(Date.now() / 1000)
            };
            
            localStorage.setItem(this.tokenKey, JSON.stringify(tokenToStore));
            
            // Set cookie for WebSocket and page authentication (backend expects 'Bearer ' prefix)
            document.cookie = `access_token=Bearer ${tokenData.access_token}; Path=/; SameSite=Strict`;
            
            // Get and return user data
            return await this.getCurrentUser();
            
        } catch (error) {
            console.error('Login error:', error);
            this._clearAuthData();
            throw error;
        }
    }

    /**
     * Get the current authenticated user
     * @returns {Promise<Object>} User data
     */
    async getCurrentUser() {
        // Return cached user if available
        if (this.currentUser) {
            return this.currentUser;
        }

        const tokenData = this.getToken();
        if (!tokenData || !tokenData.access_token) {
            throw new Error('Not authenticated');
        }

        try {
            // Try to get user data from the /users/me endpoint
            const response = await fetch(`${this.baseUrl}/users/me/`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${tokenData.access_token}`,
                    'Accept': 'application/json'
                },
                credentials: 'include'
            });

            if (response.status === 401) {
                // Token might be expired or invalid
                console.log('Token validation failed (401)');
                
                // Only try to refresh if we have a refresh token
                if (tokenData.refresh_token) {
                    console.log('Attempting to refresh token...');
                    await this.refreshToken();
                    return this.getCurrentUser(); // Retry with new token
                } else {
                    // No refresh token available, clear auth and throw error
                    console.log('No refresh token available, clearing auth data');
                    this._clearAuthData();
                    throw new Error('Authentication failed. Please log in again.');
                }
            }

            if (!response.ok) {
                throw new Error(`Failed to fetch user data: ${response.status}`);
            }

            this.currentUser = await response.json();
            return this.currentUser;
            
        } catch (error) {
            console.error('Error fetching current user:', error);
            this._clearAuthData();
            throw error;
        }
    }

    /**
     * Log out the current user
     */
    logout() {
        this._clearAuthData();
        // Redirect to login page or home page
        window.location.href = '/login';
    }

    /**
     * Get token data from storage
     * @private
     */
    _getTokenData() {
        return this.getToken();
    }

    /**
     * Clear all authentication data
     * @private
     */
    _clearAuthData() {
        localStorage.removeItem(this.tokenKey);
        document.cookie = 'access_token=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
        this.currentUser = null;
    }
    
    /**
     * Refresh the access token using the refresh token
     * @private
     */
    async refreshToken() {
        const tokenData = this.getToken();
        if (!tokenData || !tokenData.refresh_token) {
            throw new Error('No refresh token available');
        }
        
        try {
            const formData = new URLSearchParams();
            formData.append('grant_type', 'refresh_token');
            formData.append('refresh_token', tokenData.refresh_token);
            
            const response = await fetch(`${this.baseUrl}/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                },
                body: formData,
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error('Failed to refresh token');
            }
            
            const newTokenData = await response.json();
            
            // Update stored token data
            const updatedTokenData = {
                ...tokenData,
                access_token: newTokenData.access_token,
                token_type: newTokenData.token_type || tokenData.token_type,
                expires_in: newTokenData.expires_in || tokenData.expires_in,
                created_at: Math.floor(Date.now() / 1000)
            };
            
            localStorage.setItem(this.tokenKey, JSON.stringify(updatedTokenData));
            
            // Update the cookie for WebSocket auth
            document.cookie = `access_token=Bearer ${newTokenData.access_token}; Path=/; SameSite=Strict; Secure`;
            
            return updatedTokenData;
            
        } catch (error) {
            console.error('Error refreshing token:', error);
            this._clearAuthData();
            throw error;
        }
    }
}

// Export a singleton instance as named export
export const authService = new AuthService();
