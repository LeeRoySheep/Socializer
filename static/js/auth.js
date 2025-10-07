console.log('auth.js loaded');

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, setting up login form');
    
    const loginForm = document.getElementById('login-form');
    if (!loginForm) {
        console.log('No login form found');
        return;
    }
    
    console.log('Login form found, adding event listener');
    
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        console.log('Form submitted');
        
        const form = e.target;
        const formData = new FormData(form);
        const username = formData.get('username');
        const password = formData.get('password');
        const errorElement = document.getElementById('login-error');
        const submitButton = form.querySelector('button[type="submit"]');
        
        try {
            // Show loading state
            submitButton.disabled = true;
            const spinner = submitButton.querySelector('.spinner-border');
            const loginText = submitButton.querySelector('.login-text');
            if (spinner) spinner.classList.remove('d-none');
            if (loginText) loginText.textContent = 'Logging in...';
            
            // Hide any previous errors
            if (errorElement) {
                errorElement.style.display = 'none';
            }
            
            console.log('Sending login request...');
            const response = await fetch('/token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                },
                body: new URLSearchParams({ username, password }),
                credentials: 'include'
            });
            
            console.log('Response status:', response.status);
            
            const data = await response.json().catch(() => ({}));
            
            if (!response.ok) {
                throw new Error(data.detail || 'Login failed');
            }
            
            console.log('Login successful, token received');
            
            // Store token in localStorage
            const token = data.access_token;
            if (token) {
                localStorage.setItem('token', token);
                
                // Set cookie
                const expires = new Date();
                expires.setTime(expires.getTime() + (7 * 24 * 60 * 60 * 1000));
                document.cookie = `token=${token}; expires=${expires.toUTCString()}; path=/`;
                
                // Redirect to chat page
                console.log('Redirecting to /chat');
                window.location.href = `/chat?token=${encodeURIComponent(token)}`;
            }
            
        } catch (error) {
            console.error('Login error:', error);
            if (errorElement) {
                errorElement.textContent = error.message || 'Login failed';
                errorElement.style.display = 'block';
            }
        } finally {
            // Reset button state
            if (submitButton) {
                submitButton.disabled = false;
                const spinner = submitButton.querySelector('.spinner-border');
                const loginText = submitButton.querySelector('.login-text');
                if (spinner) spinner.classList.add('d-none');
                if (loginText) loginText.textContent = 'Login';
            }
        }
    });
});

// Function to handle registration
async function handleRegister(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const errorElement = document.getElementById('register-error');
    const submitButton = form.querySelector('button[type="submit"]');
    const username = formData.get('username');
    const email = formData.get('email');
    const password = formData.get('password');
    const confirmPassword = formData.get('confirm_password');
    
    try {
        // Client-side validation
        if (!username || !email || !password || !confirmPassword) {
            throw new Error('All fields are required');
        }
        
        if (password !== confirmPassword) {
            throw new Error('Passwords do not match');
        }
        
        if (password.length < 6) {
            throw new Error('Password must be at least 6 characters');
        }
        
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            throw new Error('Please enter a valid email address');
        }
        
        // Show loading state
        if (submitButton) {
            submitButton.disabled = true;
            const spinner = submitButton.querySelector('.spinner-border');
            const registerText = submitButton.querySelector('.register-text');
            if (spinner) spinner.classList.remove('d-none');
            if (registerText) registerText.textContent = 'Creating Account...';
        }
        
        // Hide any previous errors
        if (errorElement) {
            errorElement.style.display = 'none';
        }
        
        // Make registration request
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                email: email,
                password: password
            })
        });
        
        if (response.redirected) {
            window.location.href = response.url;
            return;
        }
        
        const responseData = await response.json();
        
        if (!response.ok) {
            throw new Error(responseData.detail || 'Registration failed');
        }
        
        // If registration is successful, redirect to login
        window.location.href = '/login?registered=true';
        
    } catch (error) {
        console.error('Registration error:', error);
        if (errorElement) {
            errorElement.textContent = error.message || 'An error occurred during registration';
            errorElement.style.display = 'block';
            errorElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    } finally {
        // Reset button state
        if (submitButton) {
            submitButton.disabled = false;
            const spinner = submitButton.querySelector('.spinner-border');
            const registerText = submitButton.querySelector('.register-text');
            if (spinner) spinner.classList.add('d-none');
            if (registerText) registerText.textContent = 'Register';
        }
    }
}

// Logout function
function logout() {
    // Clear tokens
    localStorage.removeItem('token');
    document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    
    // Redirect to login page
    window.location.href = '/login';
}

// Set up event listeners when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded, setting up auth forms');
    
    // Login form
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        console.log('Login form found, adding event listener');
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            console.log('Login form submitted');
            
            const form = e.target;
            const formData = new FormData(form);
            const username = formData.get('username');
            const password = formData.get('password');
            const errorElement = document.getElementById('login-error');
            const submitButton = form.querySelector('button[type="submit"]');
            
            try {
                // Show loading state
                if (submitButton) {
                    submitButton.disabled = true;
                    const spinner = submitButton.querySelector('.spinner-border');
                    const loginText = submitButton.querySelector('.login-text');
                    if (spinner) spinner.classList.remove('d-none');
                    if (loginText) loginText.textContent = 'Logging in...';
                }
                
                // Hide any previous errors
                if (errorElement) {
                    errorElement.style.display = 'none';
                }
                
                // Directly call the /token endpoint
                console.log('Sending login request to /token endpoint...');
                
                const formData = new URLSearchParams();
                formData.append('username', username);
                formData.append('password', password);
                formData.append('grant_type', 'password');
                
                try {
                    const response = await fetch('/token', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'Accept': 'application/json'
                        },
                        body: formData,
                        credentials: 'include'
                    });
                    
                    console.log('Login response status:', response.status);
                    
                    if (!response.ok) {
                        const errorData = await response.json().catch(() => ({}));
                        throw new Error(errorData.detail || 'Login failed');
                    }
                    
                    const tokenData = await response.json();
                    console.log('Login successful, token data:', {
                        ...tokenData,
                        access_token: tokenData.access_token ? '***' + tokenData.access_token.slice(-10) : 'none'
                    });
                    
                    // Store the token in localStorage
                    localStorage.setItem('auth_token', JSON.stringify(tokenData));
                    
                    // Set cookie for WebSocket authentication
                    document.cookie = `access_token=${tokenData.access_token}; Path=/; SameSite=Strict; Secure`;
                    
                    // Redirect to chat page
                    console.log('Redirecting to /chat...');
                    window.location.href = '/chat';
                    
                } catch (error) {
                    console.error('Login error:', error);
                    throw error; // Re-throw to be caught by the outer catch
                }
                    
                    // Force a hard redirect
                    window.location.href = redirectUrlWithToken;
                    return; // Stop further execution
                }
                
            } catch (error) {
                console.error('Login error:', error);
                if (errorElement) {
                    errorElement.textContent = error.message || 'An error occurred during login';
                    errorElement.style.display = 'block';
                }
            } finally {
                // Reset form state
                if (submitButton) {
                    submitButton.disabled = false;
                    const spinner = submitButton.querySelector('.spinner-border');
                    const loginText = submitButton.querySelector('.login-text');
                    if (spinner) spinner.classList.add('d-none');
                    if (loginText) loginText.textContent = 'Login';
                }
            }
        });
    }
    
    // Register form
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        console.log('Register form found, adding event listener');
        registerForm.addEventListener('submit', handleRegister);
    }
    
    // Setup register form if it exists
    if (registerForm) {
        registerForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            console.log('Register form submitted');
            
            const form = e.target;
            const formData = new FormData(form);
            const errorElement = document.getElementById('register-error');
            const submitButton = form.querySelector('button[type="submit"]');
            const username = formData.get('username');
            const email = formData.get('email');
            const password = formData.get('password');
            const confirmPassword = formData.get('confirm_password');
            
            // Clear previous errors and success messages
            if (errorElement) {
                errorElement.textContent = '';
                errorElement.style.display = 'none';
                errorElement.className = 'alert';
            }
            
            // Client-side validation
            let isValid = true;
            let errorMessage = '';
            
            if (!username || !email || !password || !confirmPassword) {
                errorMessage = 'All fields are required';
                isValid = false;
            } else if (password !== confirmPassword) {
                errorMessage = 'Passwords do not match';
                isValid = false;
            } else if (password.length < 6) {
                errorMessage = 'Password must be at least 6 characters';
                isValid = false;
            } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
                errorMessage = 'Please enter a valid email address';
                isValid = false;
            }
            
            if (!isValid) {
                if (errorElement) {
                    errorElement.textContent = errorMessage;
                    errorElement.style.color = '#dc3545';
                    errorElement.style.display = 'block';
                    errorElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                return;
            }
            
            // Show loading state
            if (submitButton) {
                submitButton.disabled = true;
                const spinner = submitButton.querySelector('.spinner-border');
                const registerText = submitButton.querySelector('.register-text');
                if (spinner) spinner.classList.remove('d-none');
                if (registerText) registerText.textContent = 'Creating Account...';
            }
            
            try {
                console.log('Sending registration request...');
                const response = await fetch('/api/auth/register', {
                    method: 'POST',
                    body: formData,
                    credentials: 'include',
                    headers: {
                        'Accept': 'application/json'
                    }
                });
                
                console.log('Registration response status:', response.status);
                
                if (response.redirected) {
                    // If the response is a redirect, follow it
                    window.location.href = response.url;
                    return;
                }
                
                let responseData = {};
                try {
                    responseData = await response.json();
                    console.log('Registration response data:', responseData);
                } catch (e) {
                    console.error('Error parsing JSON response:', e);
                    throw new Error('Invalid response from server');
                }
                
                if (!response.ok) {
                    // Handle validation errors from server
                    let errorMessage = 'Registration failed. Please try again.';
                    if (response.status === 400) {
                        errorMessage = 'Invalid registration data. Please check your input.';
                    } else if (response.status === 409) {
                        errorMessage = 'Username or email already exists. Please choose different ones.';
                    } else if (responseData && responseData.detail) {
                        if (typeof responseData.detail === 'string') {
                            errorMessage = responseData.detail;
                        } else if (Array.isArray(responseData.detail)) {
                            // Format field validation errors
                            errorMessage = responseData.detail.map(err => 
                                `• ${err.loc ? err.loc[err.loc.length - 1] + ': ' : ''}${err.msg}`
                            ).join('<br>');
                        }
                    }
                    throw new Error(errorMessage);
                }
                
            } catch (error) {
                console.error('Registration error:', error);
                if (errorElement) {
                    errorElement.innerHTML = error.message || 'An error occurred during registration';
                    errorElement.style.color = '#dc3545';
                    errorElement.style.display = 'block';
                    errorElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            } finally {
                // Reset button state
                if (submitButton) {
                    submitButton.disabled = false;
                    const spinner = submitButton.querySelector('.spinner-border');
                    const registerText = submitButton.querySelector('.register-text');
                    if (spinner) spinner.classList.add('d-none');
                    if (registerText) registerText.textContent = 'Create Account';
                }
            }
        });
    }

// Logout function
async function logout() {
    try {
        // Clear all authentication data
        localStorage.removeItem('token');
        sessionStorage.removeItem('token');
        
        // Clear cookies
        document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        document.cookie = 'token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        
        // Call server-side logout if available
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

// Make logout function globally available
window.logout = logout;
