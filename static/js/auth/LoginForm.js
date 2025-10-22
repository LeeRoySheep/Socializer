import { authService } from './AuthService.js';

export class LoginForm {
    constructor(formId = 'login-form') {
        this.form = document.getElementById(formId);
        this.errorElement = document.getElementById('login-error');
        this.submitButton = this.form?.querySelector('button[type="submit"]');
        this.initialize();
    }

    initialize() {
        if (!this.form) {
            console.warn('Login form not found');
            return;
        }

        this.form.addEventListener('submit', this.handleSubmit.bind(this));
    }

    async handleSubmit(event) {
        event.preventDefault();
        
        const formData = new FormData(this.form);
        const username = formData.get('username')?.trim();
        const password = formData.get('password');
        
        // Basic validation
        if (!username) {
            this.showError('Please enter your username');
            return;
        }
        if (!password) {
            this.showError('Please enter your password');
            return;
        }
        
        this.setLoading(true);
        this.clearError();
        
        try {
            console.log('Attempting login...');
            const loginResult = await authService.login(username, password);
            console.log('Login successful, redirecting...', loginResult);
            
            // Add a delay to ensure cookie is properly set before redirect
            // This is critical - the cookie must be available when the next page loads
            console.log('Waiting for cookie to be set...');
            await new Promise(resolve => setTimeout(resolve, 500)); // Increased delay
            
            console.log('Cookies before redirect:', document.cookie);
            
            // ALWAYS use URL token method (most reliable)
            // Cookies can fail due to SameSite, browser settings, etc.
            console.log('Using URL token method (most reliable)');
            const tokenData = JSON.parse(localStorage.getItem('auth_token'));
            if (tokenData && tokenData.access_token) {
                window.location.href = `/chat?token=${tokenData.access_token}`;
            } else {
                console.error('No token found in localStorage');
                this.showError('Authentication failed. Please try again.');
            }
            
        } catch (error) {
            console.error('Login error:', error);
            
            // More specific error messages based on error type
            let errorMessage = 'Login failed. Please try again.';
            
            if (error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
                errorMessage = 'Unable to connect to the server. Please check your internet connection.';
            } else if (error.message.includes('401')) {
                errorMessage = 'Invalid username or password. Please try again.';
            } else if (error.message) {
                // Use the error message from the server if available
                errorMessage = error.message;
            }
            
            this.showError(errorMessage);
            
            // Clear password field on error
            if (this.form) {
                const passwordField = this.form.querySelector('input[type="password"]');
                if (passwordField) passwordField.value = '';
            }
        } finally {
            this.setLoading(false);
        }
    }

    setLoading(isLoading) {
        if (!this.submitButton) return;
        
        const spinner = this.submitButton.querySelector('.spinner-border');
        const buttonText = this.submitButton.querySelector('.login-text');
        
        if (spinner) spinner.classList.toggle('d-none', !isLoading);
        if (buttonText) {
            buttonText.textContent = isLoading ? 'Logging in...' : 'Login';
        }
        
        this.submitButton.disabled = isLoading;
    }

    showError(message) {
        if (!this.errorElement) return;
        
        this.errorElement.textContent = message;
        this.errorElement.style.display = 'block';
    }
    
    /**
     * Clear any error messages
     */
    clearError() {
        if (this.errorElement) {
            this.errorElement.textContent = '';
            this.errorElement.style.display = 'none';
        }
    }
}
