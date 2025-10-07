import { authService } from '../auth/AuthService.js';

// Mock fetch
const mockFetch = (status, data) => {
    return Promise.resolve({
        ok: status >= 200 && status < 300,
        status,
        json: () => Promise.resolve(data),
        text: () => Promise.resolve(JSON.stringify(data))
    });
};

describe('AuthService', () => {
    beforeEach(() => {
        // Clear localStorage and reset mocks before each test
        localStorage.clear();
        global.fetch = jest.fn();
        authService.currentUser = null;
    });

    describe('login', () => {
        it('should login successfully with valid credentials', async () => {
            const mockToken = 'test-token-123';
            const mockUser = { id: 1, username: 'testuser' };
            
            // Mock the token response
            global.fetch.mockImplementationOnce(() => 
                mockFetch(200, { access_token: mockToken, token_type: 'bearer' })
            );
            
            // Mock the user data response
            global.fetch.mockImplementationOnce(() => 
                mockFetch(200, mockUser)
            );
            
            const result = await authService.login('testuser', 'password');
            
            expect(result).toEqual(mockUser);
            expect(authService.isAuthenticated()).toBe(true);
            expect(authService.currentUser).toEqual(mockUser);
            
            // Verify token is stored
            const tokenData = JSON.parse(localStorage.getItem('auth_token'));
            expect(tokenData.access_token).toBe(mockToken);
        });

        it('should throw an error with invalid credentials', async () => {
            global.fetch.mockImplementationOnce(() => 
                mockFetch(401, { detail: 'Incorrect username or password' })
            );
            
            await expect(authService.login('wrong', 'credentials'))
                .rejects
                .toThrow('Incorrect username or password');
                
            expect(authService.isAuthenticated()).toBe(false);
        });
    });

    describe('getCurrentUser', () => {
        it('should return current user when authenticated', async () => {
            const mockUser = { id: 1, username: 'testuser' };
            
            // Set up the token first
            localStorage.setItem('auth_token', JSON.stringify({
                access_token: 'test-token',
                token_type: 'bearer',
                created_at: Math.floor(Date.now() / 1000)
            }));
            
            global.fetch.mockImplementationOnce(() => 
                mockFetch(200, mockUser)
            );
            
            const user = await authService.getCurrentUser();
            
            expect(user).toEqual(mockUser);
            expect(authService.currentUser).toEqual(mockUser);
        });
        
        it('should throw an error when not authenticated', async () => {
            await expect(authService.getCurrentUser())
                .rejects
                .toThrow('Not authenticated');
        });
    });

    describe('logout', () => {
        it('should clear authentication data on logout', async () => {
            // Set up a logged-in state
            localStorage.setItem('auth_token', JSON.stringify({
                access_token: 'test-token',
                token_type: 'bearer',
                created_at: Math.floor(Date.now() / 1000)
            }));
            
            authService.currentUser = { id: 1, username: 'testuser' };
            
            // Mock the logout endpoint
            global.fetch.mockImplementationOnce(() => 
                mockFetch(200, { success: true })
            );
            
            await authService.logout();
            
            expect(localStorage.getItem('auth_token')).toBeNull();
            expect(authService.currentUser).toBeNull();
            expect(authService.isAuthenticated()).toBe(false);
        });
    });

    describe('isAuthenticated', () => {
        it('should return true when token is valid', () => {
            localStorage.setItem('auth_token', JSON.stringify({
                access_token: 'test-token',
                token_type: 'bearer',
                created_at: Math.floor(Date.now() / 1000)
            }));
            
            expect(authService.isAuthenticated()).toBe(true);
        });
        
        it('should return false when token is expired', () => {
            // Set a token that expired 1 hour ago
            localStorage.setItem('auth_token', JSON.stringify({
                access_token: 'test-token',
                token_type: 'bearer',
                created_at: Math.floor((Date.now() - 3600 * 1000) / 1000),
                expires_in: 1800 // 30 minutes
            }));
            
            expect(authService.isAuthenticated()).toBe(false);
        });
        
        it('should return false when no token exists', () => {
            expect(authService.isAuthenticated()).toBe(false);
        });
    });
});
