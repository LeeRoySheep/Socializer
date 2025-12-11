/**
 * LLMSettings - UI component for local LLM configuration
 */

import { localLLM } from './LocalLLM.js';
import { aiService } from './AIService.js';

export class LLMSettings {
    constructor(containerId = 'llm-settings-container') {
        this.containerId = containerId;
        this.modalId = 'llm-settings-modal';
    }

    /**
     * Create and show the settings modal
     */
    show() {
        this.removeExisting();
        const modal = this.createModal();
        document.body.appendChild(modal);
        this.bindEvents();
        this.updateStatus();
    }

    /**
     * Remove existing modal
     */
    removeExisting() {
        const existing = document.getElementById(this.modalId);
        if (existing) existing.remove();
    }

    /**
     * Create the modal HTML
     */
    createModal() {
        const settings = localLLM.settings;
        const status = localLLM.getStatus();

        const modal = document.createElement('div');
        modal.id = this.modalId;
        modal.className = 'llm-settings-modal';
        modal.innerHTML = `
            <div class="llm-settings-overlay" onclick="window.llmSettings?.hide()"></div>
            <div class="llm-settings-content">
                <div class="llm-settings-header">
                    <h3>🤖 Local LLM Settings</h3>
                    <button class="llm-close-btn" onclick="window.llmSettings?.hide()">&times;</button>
                </div>
                
                <div class="llm-settings-body">
                    <div class="llm-status" id="llm-status">
                        <span class="status-indicator ${status.available ? 'online' : 'offline'}"></span>
                        <span id="llm-status-text">${status.available ? 'Connected' : 'Not Connected'}</span>
                    </div>

                    <div class="llm-setting-group">
                        <label class="llm-toggle">
                            <input type="checkbox" id="llm-enabled" ${settings.enabled ? 'checked' : ''}>
                            <span class="toggle-slider"></span>
                            <span class="toggle-label">Enable Local LLM</span>
                        </label>
                        <p class="setting-desc">Use your local LLM (LM Studio/Ollama) instead of cloud AI</p>
                    </div>

                    <div class="llm-setting-group">
                        <label>Provider</label>
                        <select id="llm-provider">
                            <option value="lmstudio" ${settings.provider === 'lmstudio' ? 'selected' : ''}>LM Studio (localhost:1234)</option>
                            <option value="ollama" ${settings.provider === 'ollama' ? 'selected' : ''}>Ollama (localhost:11434)</option>
                            <option value="custom" ${settings.provider === 'custom' ? 'selected' : ''}>Custom URL</option>
                        </select>
                    </div>

                    <div class="llm-setting-group" id="custom-url-group" style="display: ${settings.provider === 'custom' ? 'block' : 'none'}">
                        <label>Custom URL</label>
                        <input type="text" id="llm-custom-url" placeholder="http://192.168.1.100:1234/v1" value="${settings.customUrl || ''}">
                    </div>

                    <div class="llm-setting-group">
                        <label>Model Name (optional)</label>
                        <input type="text" id="llm-model" placeholder="auto-detect" value="${settings.model || ''}">
                    </div>

                    <div class="llm-actions">
                        <button class="btn-test" onclick="window.llmSettings?.testConnection()">
                            🔌 Test Connection
                        </button>
                        <button class="btn-save" onclick="window.llmSettings?.save()">
                            💾 Save Settings
                        </button>
                    </div>

                    <div class="llm-info">
                        <h4>📝 Setup Instructions</h4>
                        <ol>
                            <li><strong>LM Studio:</strong> Enable "Enable CORS" in Settings → Server</li>
                            <li><strong>Ollama:</strong> Set <code>OLLAMA_ORIGINS=*</code> environment variable</li>
                            <li>Start your local LLM server</li>
                            <li>Click "Test Connection" above</li>
                        </ol>
                    </div>
                </div>
            </div>
        `;

        // Add styles
        this.addStyles();
        
        return modal;
    }

    /**
     * Add CSS styles
     */
    addStyles() {
        if (document.getElementById('llm-settings-styles')) return;

        const styles = document.createElement('style');
        styles.id = 'llm-settings-styles';
        styles.textContent = `
            .llm-settings-modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: 10000;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .llm-settings-overlay {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
            }
            .llm-settings-content {
                position: relative;
                background: white;
                border-radius: 12px;
                width: 90%;
                max-width: 450px;
                max-height: 90vh;
                overflow-y: auto;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            }
            .llm-settings-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 16px 20px;
                border-bottom: 1px solid #eee;
            }
            .llm-settings-header h3 {
                margin: 0;
                font-size: 18px;
            }
            .llm-close-btn {
                background: none;
                border: none;
                font-size: 24px;
                cursor: pointer;
                color: #666;
            }
            .llm-settings-body {
                padding: 20px;
            }
            .llm-status {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 12px;
                background: #f5f5f5;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            .status-indicator {
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background: #ccc;
            }
            .status-indicator.online { background: #4caf50; }
            .status-indicator.offline { background: #f44336; }
            .status-indicator.testing { background: #ff9800; animation: pulse 1s infinite; }
            @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
            .llm-setting-group {
                margin-bottom: 16px;
            }
            .llm-setting-group label {
                display: block;
                font-weight: 500;
                margin-bottom: 6px;
            }
            .llm-setting-group select,
            .llm-setting-group input[type="text"] {
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
            }
            .setting-desc {
                font-size: 12px;
                color: #666;
                margin-top: 4px;
            }
            .llm-toggle {
                display: flex;
                align-items: center;
                gap: 12px;
                cursor: pointer;
            }
            .llm-toggle input { display: none; }
            .toggle-slider {
                width: 48px;
                height: 26px;
                background: #ccc;
                border-radius: 13px;
                position: relative;
                transition: 0.3s;
            }
            .toggle-slider::after {
                content: '';
                position: absolute;
                width: 22px;
                height: 22px;
                background: white;
                border-radius: 50%;
                top: 2px;
                left: 2px;
                transition: 0.3s;
            }
            .llm-toggle input:checked + .toggle-slider {
                background: #4caf50;
            }
            .llm-toggle input:checked + .toggle-slider::after {
                left: 24px;
            }
            .llm-actions {
                display: flex;
                gap: 10px;
                margin-top: 20px;
            }
            .llm-actions button {
                flex: 1;
                padding: 12px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 500;
            }
            .btn-test {
                background: #e3f2fd;
                color: #1976d2;
            }
            .btn-save {
                background: #4caf50;
                color: white;
            }
            .llm-info {
                margin-top: 20px;
                padding: 16px;
                background: #fff3e0;
                border-radius: 8px;
                font-size: 13px;
            }
            .llm-info h4 {
                margin: 0 0 10px 0;
                font-size: 14px;
            }
            .llm-info ol {
                margin: 0;
                padding-left: 20px;
            }
            .llm-info li {
                margin-bottom: 6px;
            }
            .llm-info code {
                background: #ffcc80;
                padding: 2px 6px;
                border-radius: 3px;
            }
        `;
        document.head.appendChild(styles);
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        const providerSelect = document.getElementById('llm-provider');
        if (providerSelect) {
            providerSelect.addEventListener('change', (e) => {
                const customGroup = document.getElementById('custom-url-group');
                customGroup.style.display = e.target.value === 'custom' ? 'block' : 'none';
            });
        }
    }

    /**
     * Update status display
     */
    updateStatus(text = null, state = null) {
        const statusText = document.getElementById('llm-status-text');
        const indicator = document.querySelector('.status-indicator');
        
        if (statusText && text) {
            statusText.textContent = text;
        }
        if (indicator && state) {
            indicator.className = `status-indicator ${state}`;
        }
    }

    /**
     * Test connection to local LLM (tries direct first, then backend)
     */
    async testConnection() {
        this.updateStatus('Testing connection...', 'testing');
        
        // Temporarily enable for test
        const provider = document.getElementById('llm-provider').value;
        const customUrl = document.getElementById('llm-custom-url')?.value || '';
        const model = document.getElementById('llm-model').value;
        
        localLLM.saveSettings({
            enabled: true,
            provider,
            customUrl: provider === 'custom' ? customUrl : '',
            model
        });

        // Ping tries direct first, then backend
        const result = await localLLM.ping();
        
        if (result.success) {
            const modeLabel = result.mode === 'direct' ? '🏠 Direct' : '☁️ Backend';
            this.updateStatus(
                `✅ ${modeLabel} (${result.latency_ms?.toFixed(0)}ms, ${result.models_available} models)`, 
                'online'
            );
            console.log('[LLMSettings] Ping result:', result);
        } else {
            this.updateStatus(`❌ ${result.message}`, 'offline');
        }
    }

    /**
     * Save settings
     */
    save() {
        const enabled = document.getElementById('llm-enabled').checked;
        const provider = document.getElementById('llm-provider').value;
        const customUrl = document.getElementById('llm-custom-url').value;
        const model = document.getElementById('llm-model').value;

        localLLM.saveSettings({
            enabled,
            provider,
            customUrl: provider === 'custom' ? customUrl : '',
            model
        });

        if (enabled) {
            localLLM.checkAvailability();
        }

        this.hide();
        
        // Show confirmation
        this.showToast('Settings saved!');
    }

    /**
     * Hide modal
     */
    hide() {
        const modal = document.getElementById(this.modalId);
        if (modal) modal.remove();
    }

    /**
     * Show toast notification
     */
    showToast(message) {
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #333;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            z-index: 10001;
        `;
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2000);
    }
}

// Global instance
window.llmSettings = new LLMSettings();
export const llmSettings = window.llmSettings;
