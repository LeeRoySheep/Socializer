/**
 * Authentication Module Entry Point
 * 
 * This file serves as the main entry point for the authentication module.
 * It initializes the authentication service and any related UI components.
 */

console.log('🔵 auth/index.js loaded');

// Import the auth service and components
import { authService } from './AuthService.js';
import { LoginForm } from './LoginForm.js';

console.log('✅ AuthService imported:', authService);
console.log('✅ LoginForm imported:', LoginForm);

// Export the public API
export { authService, LoginForm };

// Auto-initialize the login form if we're on the login page
const loginFormElement = document.getElementById('login-form');
console.log('🔍 Looking for login-form element:', loginFormElement);

if (loginFormElement) {
    console.log('✅ Login form found, initializing LoginForm...');
    const loginForm = new LoginForm();
    console.log('✅ LoginForm initialized:', loginForm);
    
    // Make the form instance available globally for debugging
    window.loginForm = loginForm;
} else {
    console.log('⚠️ No login form found on this page');
}

// Make authService available globally for debugging
window.authService = authService;
console.log('✅ authService available at window.authService');
