/**
 * @jest-environment jsdom
 */

import { authService } from '../../static/js/auth/AuthService';

// Mock the global fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock localStorage
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: jest.fn((key) => store[key] || null),
    setItem: jest.fn((key, value) => {
      store[key] = value.toString();
    }),
    removeItem: jest.fn((key) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
  };
})();

// Mock document.cookie
Object.defineProperty(document, 'cookie', {
  writable: true,
  value: '',
});

describe('AuthService', () => {
  const mockToken = 'test-token-123';
  const mockUser = { username: 'testuser', id: 1 };
  
  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();
    localStorageMock.clear();
    document.cookie = '';
    
    // Set up the fetch mock
    mockFetch.mockReset();
    
    // Mock the login response
    mockFetch.mockImplementation((url, options) => {
      if (url === '/token' && options?.method === 'POST') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            access_token: mockToken,
            token_type: 'bearer',
            user: mockUser
          })
        });
      }
      
      // Mock the user data response
      if (url === '/api/users/me') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockUser)
        });
      }
      
      return Promise.reject(new Error('Unexpected URL'));
    });
    
    // Replace the global localStorage with our mock
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
    });
  });

  describe('login', () => {
    it('should store the token and user data on successful login', async () => {
      // Act
      const result = await authService.login('testuser', 'password123');
      
      // Assert
      expect(result).toEqual(mockUser);
      expect(localStorage.setItem).toHaveBeenCalledWith('auth_token', mockToken);
      expect(document.cookie).toContain(`access_token=Bearer ${mockToken}`);
    });

    it('should handle login failure', async () => {
      // Arrange
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Invalid credentials' })
      });
      
      // Act & Assert
      await expect(authService.login('wrong', 'credentials'))
        .rejects
        .toThrow('Invalid credentials');
    });
  });

  describe('getToken', () => {
    it('should return token from localStorage', () => {
      // Arrange
      localStorage.setItem('auth_token', mockToken);
      
      // Act
      const token = authService.getToken();
      
      // Assert
      expect(token).toBe(mockToken);
    });
    
    it('should return null when no token exists', () => {
      // Act
      const token = authService.getToken();
      
      // Assert
      expect(token).toBeNull();
    });
  });

  describe('isAuthenticated', () => {
    it('should return true when token exists', () => {
      // Arrange
      localStorage.setItem('auth_token', mockToken);
      
      // Act
      const isAuth = authService.isAuthenticated();
      
      // Assert
      expect(isAuth).toBe(true);
    });
    
    it('should return false when no token exists', () => {
      // Act
      const isAuth = authService.isAuthenticated();
      
      // Assert
      expect(isAuth).toBe(false);
    });
  });

  describe('logout', () => {
    it('should clear all auth data', async () => {
      // Arrange
      localStorage.setItem('auth_token', mockToken);
      document.cookie = 'access_token=test-token';
      
      // Act
      await authService.logout();
      
      // Assert
      expect(localStorage.removeItem).toHaveBeenCalledWith('auth_token');
      expect(document.cookie).toContain('access_token=;');
    });
  });

  describe('fetchWithAuth', () => {
    it('should add Authorization header with token', async () => {
      // Arrange
      localStorage.setItem('auth_token', mockToken);
      let requestHeaders;
      
      mockFetch.mockImplementationOnce((url, options) => {
        requestHeaders = options.headers;
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({})
        });
      });
      
      // Act
      await authService.fetchWithAuth('/api/test');
      
      // Assert
      expect(requestHeaders.Authorization).toBe(`Bearer ${mockToken}`);
    });
    
    it('should handle 401 Unauthorized by clearing auth and redirecting', async () => {
      // Arrange
      localStorage.setItem('auth_token', mockToken);
      const originalLocation = window.location;
      delete window.location;
      window.location = { href: '' };
      
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Token expired' })
      });
      
      // Act
      await authService.fetchWithAuth('/api/protected');
      
      // Assert
      expect(localStorage.removeItem).toHaveBeenCalledWith('auth_token');
      expect(window.location.href).toContain('/login');
      
      // Cleanup
      window.location = originalLocation;
    });
  });
});
