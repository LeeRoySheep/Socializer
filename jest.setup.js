// Mock localStorage
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: (key) => store[key] || null,
    setItem: (key, value) => {
      store[key] = value.toString();
    },
    removeItem: (key) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

global.localStorage = localStorageMock;

// Mock window.location
const mockLocation = new URL('http://localhost/chat');
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true,
});

// Mock global variables
window.ACCESS_TOKEN = 'test-token-123';
window.USER_DATA = {
  username: 'testuser',
  id: 1,
  email: 'test@example.com'
};
