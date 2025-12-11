/**
 * LocalLLM - Hybrid local LLM communication
 * 
 * ARCHITECTURE: Browser-direct with backend fallback
 * 1. Try direct browser → localhost (works when user has LM Studio)
 * 2. Fall back to backend API if direct fails
 * 
 * This allows users to use their local LM Studio even when
 * the app is hosted on a cloud server (Render.com, etc.)
 */

export class LocalLLM {
    constructor() {
        this.providers = {
            lmstudio: { url: 'http://localhost:1234/v1', name: 'LM Studio' },
            ollama: { url: 'http://localhost:11434/v1', name: 'Ollama' }
        };
        this.apiBase = '/api/local-llm';
        this.isAvailable = false;
        this.connectionMode = null; // 'direct' or 'backend'
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
            customUrl: '',
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
     * Get the base URL for direct connection
     */
    getDirectUrl() {
        if (this.settings.customUrl) {
            return this.settings.customUrl;
        }
        return this.providers[this.settings.provider]?.url || this.providers.lmstudio.url;
    }

    /**
     * Get auth headers for backend API calls
     */
    _getAuthHeaders() {
        const token = window.ACCESS_TOKEN || localStorage.getItem('access_token');
        if (!token) {
            return { 'Content-Type': 'application/json' };
        }
        const cleanToken = token.replace(/^Bearer\s+/, '');
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${cleanToken}`
        };
    }

    /**
     * Try direct browser-to-localhost connection
     */
    async _tryDirectConnection() {
        const baseUrl = this.getDirectUrl();
        console.log('[LocalLLM] Trying direct connection to:', baseUrl);
        
        try {
            const response = await fetch(`${baseUrl}/models`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
                signal: AbortSignal.timeout(3000)
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('[LocalLLM] ✅ Direct connection successful');
                return { success: true, models: data.data || [], mode: 'direct' };
            }
        } catch (error) {
            console.log('[LocalLLM] Direct connection failed:', error.message);
        }
        
        return { success: false, mode: 'direct' };
    }

    /**
     * Try backend API connection
     */
    async _tryBackendConnection() {
        console.log('[LocalLLM] Trying backend API connection...');
        
        try {
            const response = await fetch(`${this.apiBase}/ping`, {
                method: 'GET',
                headers: this._getAuthHeaders()
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    console.log('[LocalLLM] ✅ Backend connection successful');
                    return { success: true, data, mode: 'backend' };
                }
            }
        } catch (error) {
            console.log('[LocalLLM] Backend connection failed:', error.message);
        }
        
        return { success: false, mode: 'backend' };
    }

    /**
     * Ping - tries direct first, then backend
     */
    async ping() {
        console.log('[LocalLLM] Pinging local LLM...');
        const startTime = performance.now();
        
        // Try direct connection first (browser → localhost)
        const directResult = await this._tryDirectConnection();
        if (directResult.success) {
            const latency = performance.now() - startTime;
            this.isAvailable = true;
            this.connectionMode = 'direct';
            this.lastPingResult = {
                success: true,
                message: 'Connected directly to local LLM',
                mode: 'direct',
                latency_ms: latency,
                models_available: directResult.models?.length || 0
            };
            return this.lastPingResult;
        }
        
        // Fall back to backend API
        const backendResult = await this._tryBackendConnection();
        if (backendResult.success) {
            this.isAvailable = true;
            this.connectionMode = 'backend';
            this.lastPingResult = {
                ...backendResult.data,
                mode: 'backend'
            };
            return this.lastPingResult;
        }
        
        // Both failed
        this.isAvailable = false;
        this.connectionMode = null;
        this.lastPingResult = {
            success: false,
            message: 'Local LLM not available (tried direct & backend)',
            mode: null
        };
        return this.lastPingResult;
    }

    /**
     * Check if local LLM is available
     */
    async checkAvailability() {
        if (!this.settings.enabled) {
            this.isAvailable = false;
            return false;
        }

        const result = await this.ping();
        return result.success;
    }

    /**
     * Send chat via direct connection
     */
    async _chatDirect(messages, options = {}) {
        const baseUrl = this.getDirectUrl();
        const model = options.model || this.settings.model || 'local-model';

        const payload = {
            model: model,
            messages: messages,
            temperature: options.temperature || 0.7,
            max_tokens: options.max_tokens || 1000,
            stream: false
        };

        const response = await fetch(`${baseUrl}/chat/completions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`Direct LLM error: ${response.status}`);
        }

        const data = await response.json();
        return {
            content: data.choices[0]?.message?.content || '',
            model: data.model,
            usage: data.usage,
            provider: 'local-direct'
        };
    }

    /**
     * Send chat via backend API
     */
    async _chatBackend(messages, options = {}) {
        const model = options.model || this.settings.model || 'ibm/granite-4-h-tiny';

        const payload = {
            messages: messages,
            model: model,
            temperature: options.temperature || 0.7,
            max_tokens: options.max_tokens || 1000
        };

        const response = await fetch(`${this.apiBase}/chat`, {
            method: 'POST',
            headers: this._getAuthHeaders(),
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            if (response.status === 503) {
                const error = await response.json();
                throw new Error(error.detail || 'Local LLM not available via backend');
            }
            throw new Error(`Backend API error: ${response.status}`);
        }

        const data = await response.json();
        return {
            content: data.response || '',
            model: data.model,
            usage: data.tokens,
            provider: 'local-backend',
            trace_id: data.trace_id,
            latency_ms: data.latency_ms
        };
    }

    /**
     * Send chat message - tries direct first, then backend
     */
    async chat(messages, options = {}) {
        if (!this.settings.enabled) {
            throw new Error('Local LLM not enabled');
        }

        const model = options.model || this.settings.model || 'ibm/granite-4-h-tiny';
        console.log('[LocalLLM] Sending chat, model:', model);

        // If we know our connection mode, use it
        if (this.connectionMode === 'direct') {
            try {
                console.log('[LocalLLM] Using direct connection...');
                return await this._chatDirect(messages, options);
            } catch (error) {
                console.warn('[LocalLLM] Direct chat failed, trying backend:', error.message);
            }
        }

        if (this.connectionMode === 'backend') {
            console.log('[LocalLLM] Using backend API...');
            return await this._chatBackend(messages, options);
        }

        // Unknown mode - try direct first
        try {
            console.log('[LocalLLM] Trying direct chat...');
            const result = await this._chatDirect(messages, options);
            this.connectionMode = 'direct';
            return result;
        } catch (directError) {
            console.log('[LocalLLM] Direct failed, trying backend...');
            try {
                const result = await this._chatBackend(messages, options);
                this.connectionMode = 'backend';
                return result;
            } catch (backendError) {
                throw new Error(`Local LLM unavailable: ${directError.message}`);
            }
        }
    }

    /**
     * Get available models
     */
    async getModels() {
        // Try direct first
        try {
            const baseUrl = this.getDirectUrl();
            const response = await fetch(`${baseUrl}/models`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
                signal: AbortSignal.timeout(3000)
            });
            
            if (response.ok) {
                const data = await response.json();
                return data.data?.map(m => m.id) || [];
            }
        } catch (error) {
            // Try backend
            try {
                const response = await fetch(`${this.apiBase}/models`, {
                    method: 'GET',
                    headers: this._getAuthHeaders()
                });
                
                if (response.ok) {
                    const data = await response.json();
                    return data.models?.map(m => m.id || m) || [];
                }
            } catch (e) {
                // Both failed
            }
        }
        
        return [];
    }

    /**
     * Get status info for UI display
     */
    getStatusSync() {
        return {
            enabled: this.settings.enabled,
            available: this.isAvailable,
            provider: this.settings.provider,
            providerName: this.providers[this.settings.provider]?.name || 'Custom',
            model: this.settings.model,
            connectionMode: this.connectionMode,
            lastPing: this.lastPingResult
        };
    }
}

// Singleton instance
export const localLLM = new LocalLLM();
