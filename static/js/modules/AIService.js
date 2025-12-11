/**
 * AIService - Hybrid AI provider with local LLM fallback
 * Tries local LLM first, falls back to cloud API
 */

import { localLLM } from './LocalLLM.js';

export class AIService {
    constructor(apiBaseUrl = '') {
        this.apiBaseUrl = apiBaseUrl || window.location.origin;
        this.useLocalFirst = true;
    }

    /**
     * Initialize and check local LLM availability
     */
    async init() {
        await localLLM.checkAvailability();
        console.log('[AIService] Local LLM available:', localLLM.isAvailable);
        return this;
    }

    /**
     * Send chat message - tries local LLM first if enabled
     */
    async chat(message, conversationHistory = [], options = {}) {
        const messages = this.formatMessages(message, conversationHistory);

        // Try local LLM first if enabled and available
        if (this.useLocalFirst && localLLM.settings.enabled) {
            try {
                await localLLM.checkAvailability();
                if (localLLM.isAvailable) {
                    console.log('[AIService] Using local LLM');
                    const response = await localLLM.chat(messages, options);
                    return {
                        ...response,
                        source: 'local'
                    };
                }
            } catch (error) {
                console.warn('[AIService] Local LLM failed, falling back to cloud:', error.message);
            }
        }

        // Fallback to cloud API
        console.log('[AIService] Using cloud API');
        return await this.cloudChat(message, options);
    }

    /**
     * Stream chat - tries local LLM first if enabled
     */
    async *streamChat(message, conversationHistory = [], options = {}) {
        const messages = this.formatMessages(message, conversationHistory);

        // Try local LLM first if enabled and available
        if (this.useLocalFirst && localLLM.settings.enabled && localLLM.isAvailable) {
            try {
                console.log('[AIService] Streaming from local LLM');
                for await (const chunk of localLLM.streamChat(messages, options)) {
                    yield { content: chunk, source: 'local' };
                }
                return;
            } catch (error) {
                console.warn('[AIService] Local stream failed, falling back to cloud:', error.message);
            }
        }

        // Fallback to cloud streaming
        console.log('[AIService] Streaming from cloud API');
        for await (const chunk of this.cloudStreamChat(message, options)) {
            yield chunk;
        }
    }

    /**
     * Format messages for OpenAI-compatible API
     */
    formatMessages(userMessage, history = []) {
        const messages = [
            {
                role: 'system',
                content: 'You are a helpful AI assistant for Socializer, a social skills training app. Be friendly, supportive, and encouraging.'
            }
        ];

        // Add conversation history
        for (const msg of history.slice(-10)) { // Last 10 messages
            messages.push({
                role: msg.role || (msg.isUser ? 'user' : 'assistant'),
                content: msg.content || msg.text
            });
        }

        // Add current message
        messages.push({ role: 'user', content: userMessage });

        return messages;
    }

    /**
     * Send to cloud API (your backend)
     */
    async cloudChat(message, options = {}) {
        const token = localStorage.getItem('access_token') || window.ACCESS_TOKEN;
        
        const response = await fetch(`${this.apiBaseUrl}/api/ai/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                message: message,
                ...options
            })
        });

        if (!response.ok) {
            throw new Error(`Cloud API error: ${response.status}`);
        }

        const data = await response.json();
        return {
            content: data.response || data.message || data.content,
            source: 'cloud',
            provider: data.provider || 'cloud'
        };
    }

    /**
     * Stream from cloud API
     */
    async *cloudStreamChat(message, options = {}) {
        const token = localStorage.getItem('access_token') || window.ACCESS_TOKEN;
        
        const response = await fetch(`${this.apiBaseUrl}/api/ai/chat/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                message: message,
                stream: true,
                ...options
            })
        });

        if (!response.ok) {
            // Fallback to non-streaming
            const result = await this.cloudChat(message, options);
            yield result;
            return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const text = decoder.decode(value);
            yield { content: text, source: 'cloud' };
        }
    }

    /**
     * Get current status
     */
    getStatus() {
        const localStatus = localLLM.getStatus();
        return {
            mode: localStatus.enabled && localStatus.available ? 'local' : 'cloud',
            local: localStatus,
            useLocalFirst: this.useLocalFirst
        };
    }

    /**
     * Enable/disable local LLM
     */
    setLocalEnabled(enabled) {
        localLLM.saveSettings({ enabled });
        if (enabled) {
            localLLM.checkAvailability();
        }
    }

    /**
     * Configure local LLM
     */
    configureLocal(settings) {
        localLLM.saveSettings(settings);
    }
}

// Singleton instance
export const aiService = new AIService();
