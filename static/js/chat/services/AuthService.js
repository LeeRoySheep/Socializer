export class AuthService {
    constructor() {
        this.currentUser = null;
    }

    async checkAuth() {
        try {
            // Check if we have a token
            const token = this.getToken();
            if (!token) {
                return false;
            }

            // Verify token with the server
            const response = await fetch('/api/auth/verify', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                this.clearAuth();
                return false;
            }

            const userData = await response.json();
            this.currentUser = userData;
            return true;

        } catch (error) {
            console.error('Auth check failed:', error);
            this.clearAuth();
            return false;
        }
    }

    getCurrentUser() {
        return this.currentUser;
    }

    getToken() {
        // Check localStorage first
        let token = localStorage.getItem('access_token');
        if (token) return token;

        // Check sessionStorage
        token = sessionStorage.getItem('access_token');
        if (token) return token;

        // Check cookies
        const cookies = document.cookie.split(';');
        for (const cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'access_token') {
                return decodeURIComponent(value);
            }
        }

        return null;
    }

    async logout() {
        try {
            // Clear all authentication data
            this.clearAuth();
            
            // Try to call server-side logout if available
            try {
                await fetch('/api/auth/logout', {
                    method: 'POST',
                    credentials: 'include'
                });
            } catch (error) {
                console.log('Server logout failed (may be expected if endpoint is not implemented)');
            }
            
            // Redirect to login page
            window.location.href = '/login';
        } catch (error) {
            console.error('Logout error:', error);
            window.location.href = '/login'; // Still redirect even if there's an error
        }
    }

    clearAuth() {
        // Clear all auth data from storage
        localStorage.removeItem('access_token');
        sessionStorage.removeItem('access_token');
        
        // Clear cookie by setting expiration to past date
        document.cookie = 'access_token=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
        
        this.currentUser = null;
    }
}

export default AuthService;
