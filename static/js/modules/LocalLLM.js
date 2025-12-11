/**
 * LocalLLM - Backend-managed local LLM communication
 * 
 * ARCHITECTURE: Frontend → Backend API → Local LLM
 * - All LLM calls go through authenticated backend endpoints
 * - No direct browser-to-LLM connections
 * - Frontend only communicates via API routes
 * 
 * Backend endpoints:
 * - GET  /api/local-llm/ping   - Test connection
 * - GET  /api/local-llm/status - Get status and models
 * - POST /api/local-llm/chat   - Send chat message
 * - GET  /api/local-llm/models - List models
 */

export class LocalLLM {
    constructor() {
        this.apiBase = '/api/local-llm';
        this.isAvailable = false;
        this.lastPingResult = null;
        this.settings = this.loadSettings();
    }

    /**
     * Load settings from localStorage
     */
    loadSettings() {
        const saved = localStorage.getItem('localLLM_settings');
        return saved ? JSON.parse(saved) : {
            enabled: false,
            provider: 'lmstudio',
            model: 'ibm/granite-4-h-tiny'
        };
    }

    /**
     * Save settings to localStorage
     */
    saveSettings(settings) {
        this.settings = { ...this.settings, ...settings };
        localStorage.setItem('localLLM_settings', JSON.stringify(this.settings));
    }

    /**
     * Get auth headers from current session
     */
    _getAuthHeaders() {
        const token = window.ACCESS_TOKEN || localStorage.getItem('access_token');
        if (!token) {
            console.warn('[LocalLLM] No auth token available');
            return { 'Content-Type': 'application/json' };
        }
        const cleanToken = token.replace(/^Bearer\s+/, '');
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${cleanToken}`
        };
    }

    /**
     * Ping backend to test local LLM connection
     * Returns ping result with latency and status
     */
    async ping() {
        console.log('[LocalLLM] Pinging backend for local LLM status...');
        
        try {
            const response = await fetch(`${this.apiBase}/ping`, {
                method: 'GET',
                headers: this._getAuthHeaders()
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('[LocalLLM] Ping result:', data);
                this.lastPingResult = data;
                this.isAvailable = data.success;
                return data;
            } else if (response.status === 401) {
                console.warn('[LocalLLM] Not authenticated');
                return { success: false, message: 'Not authenticated', trace_id: '-' };
            } else {
                const error = await response.json();
                return { success: false, message: error.detail || 'Ping failed', trace_id: '-' };
            }
        } catch (error) {
            console.error('[LocalLLM] Ping error:', error);
            return { success: false, message: error.message, trace_id: '-' };
        }
    }

    /**
     * Check if local LLM is available (via backend)
     */
    async checkAvailability() {
        if (!this.settings.enabled) {
            this.isAvailable = false;
            return false;
        }

        const result = await this.ping();
        this.isAvailable = result.success;
        return result.success;
    }

    /**
     * Get local LLM status from backend
     */
    async getStatus() {
        try {
            const response = await fetch(`${this.apiBase}/status`, {
                method: 'GET',
                headers: this._getAuthHeaders()
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('[LocalLLM] Status:', data);
                this.isAvailable = data.available;
                return data;
            }
        } catch (error) {
            console.error('[LocalLLM] Status error:', error);
        }
        
        return { available: false, models: [], endpoint: '', provider: 'unknown' };
    }

    /**
     * Get available models from backend
     */
    async getModels() {
        try {
            const response = await fetch(`${this.apiBase}/models`, {
                method: 'GET',
                headers: this._getAuthHeaders()
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('[LocalLLM] Models:', data);
                return data.models || [];
            }
        } catch (error) {
            console.error('[LocalLLM] Models error:', error);
        }
        
        return [];
    }

    /**
     * Send chat message via backend to local LLM
     */
    async chat(messages, options = {}) {
        if (!this.settings.enabled) {
            throw new Error('Local LLM not enabled');
        }

        const model = options.model || this.settings.model || 'ibm/granite-4-h-tiny';
        
        console.log('[LocalLLM] Sending chat via backend API...');
        console.log('[LocalLLM] Model:', model);
        console.log('[LocalLLM] Messages:', messages.length);

        const payload = {
            messages: messages,
            model: model,
            temperature: options.temperature || 0.7,
            max_tokens: options.max_tokens || 1000
        };

        try {
            const response = await fetch(`${this.apiBase}/chat`, {
                method: 'POST',
                headers: this._getAuthHeaders(),
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error('Not authenticated');
                }
                if (response.status === 503) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Local LLM not available');
                }
                throw new Error(`API error: ${response.status}`);
            }

            const data = await response.json();
            console.log('[LocalLLM] Response received:', {
                success: data.success,
                trace_id: data.trace_id,
                latency_ms: data.latency_ms,
                response_preview: data.response?.substring(0, 50) + '...'
            });

            return {
                content: data.response || '',
                model: data.model,
                usage: data.tokens,
                provider: 'local',
                trace_id: data.trace_id,
                latency_ms: data.latency_ms
            };
        } catch (error) {
            console.error('[LocalLLM] Chat error:', error);
            throw error;
        }
    }

    /**
     * Get status info for UI display
     */
    getStatusSync() {
        return {
            enabled: this.settings.enabled,
            available: this.isAvailable,
            provider: this.settings.provider,
            providerName: this.settings.provider === 'lmstudio' ? 'LM Studio' : 'Ollama',
            model: this.settings.model,
            lastPing: this.lastPingResult
        };
    }
}

// Singleton instance
export const localLLM = new LocalLLM();
