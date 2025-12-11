/**
 * LocalLLM - Direct browser-to-local-LLM communication
 * Enables using LM Studio or Ollama directly from the browser
 * while the app is hosted on a public server.
 */

export class LocalLLM {
    constructor() {
        this.providers = {
            lmstudio: { url: 'http://localhost:1234/v1', name: 'LM Studio' },
            ollama: { url: 'http://localhost:11434/v1', name: 'Ollama' }
        };
        this.activeProvider = null;
        this.isAvailable = false;
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
            model: 'local-model'
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
     * Get the base URL for the active provider
     */
    getBaseUrl() {
        if (this.settings.customUrl) {
            return this.settings.customUrl;
        }
        return this.providers[this.settings.provider]?.url || this.providers.lmstudio.url;
    }

    /**
     * Check if local LLM is available
     */
    async checkAvailability() {
        if (!this.settings.enabled) {
            this.isAvailable = false;
            return false;
        }

        const baseUrl = this.getBaseUrl();
        
        try {
            const response = await fetch(`${baseUrl}/models`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
                signal: AbortSignal.timeout(3000) // 3 second timeout
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('[LocalLLM] Available models:', data);
                this.isAvailable = true;
                this.activeProvider = this.settings.provider;
                return true;
            }
        } catch (error) {
            console.log('[LocalLLM] Not available:', error.message);
        }
        
        this.isAvailable = false;
        return false;
    }

    /**
     * Send a chat message directly to local LLM
     */
    async chat(messages, options = {}) {
        if (!this.isAvailable) {
            throw new Error('Local LLM not available');
        }

        const baseUrl = this.getBaseUrl();
        const model = options.model || this.settings.model || 'local-model';

        const payload = {
            model: model,
            messages: messages,
            temperature: options.temperature || 0.7,
            max_tokens: options.max_tokens || 2000,
            stream: options.stream || false
        };

        try {
            const response = await fetch(`${baseUrl}/chat/completions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`LLM error: ${response.status}`);
            }

            const data = await response.json();
            return {
                content: data.choices[0]?.message?.content || '',
                model: data.model,
                usage: data.usage,
                provider: 'local'
            };
        } catch (error) {
            console.error('[LocalLLM] Chat error:', error);
            throw error;
        }
    }

    /**
     * Stream chat response from local LLM
     */
    async *streamChat(messages, options = {}) {
        if (!this.isAvailable) {
            throw new Error('Local LLM not available');
        }

        const baseUrl = this.getBaseUrl();
        const model = options.model || this.settings.model || 'local-model';

        const payload = {
            model: model,
            messages: messages,
            temperature: options.temperature || 0.7,
            max_tokens: options.max_tokens || 2000,
            stream: true
        };

        const response = await fetch(`${baseUrl}/chat/completions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`LLM error: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    if (data === '[DONE]') return;
                    
                    try {
                        const parsed = JSON.parse(data);
                        const content = parsed.choices[0]?.delta?.content;
                        if (content) {
                            yield content;
                        }
                    } catch (e) {
                        // Skip invalid JSON
                    }
                }
            }
        }
    }

    /**
     * Get status info for UI display
     */
    getStatus() {
        return {
            enabled: this.settings.enabled,
            available: this.isAvailable,
            provider: this.activeProvider || this.settings.provider,
            providerName: this.providers[this.settings.provider]?.name || 'Custom',
            url: this.getBaseUrl()
        };
    }
}

// Singleton instance
export const localLLM = new LocalLLM();
