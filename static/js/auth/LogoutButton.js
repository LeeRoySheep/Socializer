import { authService } from './AuthService.js';

export class LogoutButton {
    constructor(buttonId = 'logout-btn') {
        this.button = document.getElementById(buttonId);
        if (this.button) {
            this.initialize();
        } else {
            console.warn(`Logout button with ID '${buttonId}' not found`);
        }
    }

    initialize() {
        this.button.addEventListener('click', this.handleClick.bind(this));
    }

    async handleClick(event) {
        event.preventDefault();
        
        // Optional: Add confirmation dialog
        const shouldLogout = confirm('Are you sure you want to log out?');
        if (!shouldLogout) return;
        
        // Show loading state if needed
        const originalText = this.button.innerHTML;
        this.button.disabled = true;
        this.button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Logging out...';
        
        try {
            await authService.logout();
            // The logout method will handle the redirect
        } catch (error) {
            console.error('Logout error:', error);
            // Still redirect to login page even if there was an error
            window.location.href = '/login';
        } finally {
            // Reset button state (shouldn't be needed due to redirect, but just in case)
            this.button.disabled = false;
            this.button.innerHTML = originalText;
        }
    }
}

// Auto-initialize if this script is included directly
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new LogoutButton());
} else {
    new LogoutButton();
}
