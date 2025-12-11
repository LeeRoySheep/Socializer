/**
 * BrowserAgent - Client-side AI agent with tool support
 * 
 * ARCHITECTURE: Browser → LLM (direct) + Backend (tool execution)
 * 
 * When backend can't reach local LLM (e.g., Render.com), this agent:
 * 1. Sends messages to LLM via browser (direct connection)
 * 2. Parses tool calls from LLM response
 * 3. Executes tools via backend API calls
 * 4. Sends results back to LLM
 * 5. Returns final response to user
 */

import { localLLM } from './LocalLLM.js';

export class BrowserAgent {
    constructor() {
        this.apiBase = '/api/tools';
        this.maxIterations = 5;  // Prevent infinite loops
        
        // MCP system prompt for local models
        this.systemPrompt = this._buildSystemPrompt();
        
        // Tool definitions for the LLM
        this.tools = [
            { name: 'web_search', description: 'Search the web for information (weather, news, etc.)', params: ['query'] },
            { name: 'recall_last_conversation', description: 'Recall previous conversations', params: [] },
            { name: 'skill_evaluator', description: 'Evaluate user social skills', params: ['skill_type'] },
            { name: 'user_preference', description: 'Get/set user preferences', params: ['preference_type'] },
            { name: 'life_event', description: 'Record life events', params: ['event_type', 'description'] },
        ];
    }

    /**
     * Build MCP-compatible system prompt
     */
    _buildSystemPrompt() {
        return `## BROWSER AGENT - SOCIAL SKILLS COACH

You are a Social Skills Coach AI assistant. You have access to tools to help users.

### RESPONSE FORMAT:
You MUST respond in this exact JSON format:

For direct response (no tool needed):
{"response": "Your helpful response here", "tool_call": null}

For tool call needed:
{"response": null, "tool_call": {"name": "tool_name", "arguments": {"arg": "value"}}}

### AVAILABLE TOOLS:
- web_search: Search web for info. Args: {"query": "search terms"}
- recall_last_conversation: Get previous chat history. Args: {}
- skill_evaluator: Evaluate skills. Args: {"skill_type": "general"}
- user_preference: Get/set preferences. Args: {"preference_type": "..."}
- life_event: Record events. Args: {"event_type": "...", "description": "..."}

### RULES:
1. ALWAYS respond in valid JSON format
2. For greetings/simple questions: use direct response
3. For weather/search queries: use web_search tool
4. For memory/recall: use recall_last_conversation
5. Be warm and supportive as a Social Skills Coach

### EXAMPLES:

User: "Hello!"
{"response": "Hello! Great to see you! How can I help you improve your communication skills today?", "tool_call": null}

User: "What's the weather in Berlin?"
{"response": null, "tool_call": {"name": "web_search", "arguments": {"query": "weather in Berlin"}}}

User: "What did we talk about last time?"
{"response": null, "tool_call": {"name": "recall_last_conversation", "arguments": {}}}
`;
    }

    /**
     * Get auth headers for backend API calls
     */
    _getAuthHeaders() {
        // Try multiple sources for the token
        let token = window.ACCESS_TOKEN || 
                   window.AUTH_TOKEN || 
                   localStorage.getItem('access_token') ||
                   localStorage.getItem('token');
        
        if (!token) {
            console.warn('[BrowserAgent] No auth token found');
            return { 'Content-Type': 'application/json' };
        }
        
        const cleanToken = token.replace(/^Bearer\s+/, '');
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${cleanToken}`
        };
    }

    /**
     * Parse JSON response from LLM
     */
    _parseResponse(content) {
        if (!content) return null;
        
        // Clean content
        let cleaned = content.trim();
        
        // Remove markdown code blocks if present
        if (cleaned.startsWith('```json')) {
            cleaned = cleaned.slice(7);
        } else if (cleaned.startsWith('```')) {
            cleaned = cleaned.slice(3);
        }
        if (cleaned.endsWith('```')) {
            cleaned = cleaned.slice(0, -3);
        }
        cleaned = cleaned.trim();
        
        // Try to parse JSON
        try {
            const parsed = JSON.parse(cleaned);
            return parsed;
        } catch (e) {
            console.log('[BrowserAgent] Failed to parse JSON, using as text response');
            // If not valid JSON, treat entire content as response
            return { response: content, tool_call: null };
        }
    }

    /**
     * Execute a tool via backend API
     */
    async _executeTool(toolCall) {
        const { name, arguments: args } = toolCall;
        console.log(`[BrowserAgent] 🔧 Executing tool: ${name}`, args);
        
        try {
            const response = await fetch(`${this.apiBase}/execute`, {
                method: 'POST',
                headers: this._getAuthHeaders(),
                body: JSON.stringify({
                    tool_name: name,
                    arguments: args || {}
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log(`[BrowserAgent] ✅ Tool result:`, data);
                return data.result || JSON.stringify(data);
            } else {
                const error = await response.json();
                console.error(`[BrowserAgent] ❌ Tool error:`, error);
                return `Error: ${error.detail || 'Tool execution failed'}`;
            }
        } catch (error) {
            console.error(`[BrowserAgent] ❌ Tool fetch error:`, error);
            return `Error: Could not execute tool - ${error.message}`;
        }
    }

    /**
     * Send message to LLM and get response
     */
    async _callLLM(messages) {
        const model = localLLM.settings.model || 'local-model';
        
        try {
            const result = await localLLM.chat(messages, { model });
            return result.content;
        } catch (error) {
            console.error('[BrowserAgent] LLM call failed:', error);
            throw error;
        }
    }

    /**
     * Main chat method - handles tool calling loop
     */
    async chat(userMessage) {
        console.log('[BrowserAgent] 🚀 Starting chat with message:', userMessage);
        
        try {
            const messages = [
                { role: 'system', content: this.systemPrompt },
                { role: 'user', content: userMessage }
            ];
            
            let iteration = 0;
            let toolsUsed = [];
            
            while (iteration < this.maxIterations) {
                iteration++;
                console.log(`[BrowserAgent] Iteration ${iteration}/${this.maxIterations}`);
                
                try {
                    // Call LLM
                    const llmResponse = await this._callLLM(messages);
                    console.log('[BrowserAgent] LLM response:', llmResponse);
                    
                    // Parse response
                    const parsed = this._parseResponse(llmResponse);
                    
                    if (!parsed) {
                        console.log('[BrowserAgent] Could not parse response, returning raw');
                        return { content: llmResponse, tools_used: toolsUsed };
                    }
                    
                    // Check if tool call needed
                    if (parsed.tool_call && parsed.tool_call.name) {
                        console.log('[BrowserAgent] 🔧 Tool call detected:', parsed.tool_call);
                        
                        // Execute tool
                        const toolResult = await this._executeTool(parsed.tool_call);
                        toolsUsed.push(parsed.tool_call.name);
                        
                        // Add assistant message with tool call
                        messages.push({
                            role: 'assistant',
                            content: llmResponse
                        });
                        
                        // Add tool result as user message
                        messages.push({
                            role: 'user',
                            content: `Tool "${parsed.tool_call.name}" returned: ${toolResult}\n\nPlease provide a natural response based on this result.`
                        });
                        
                        // Continue loop to get final response
                        continue;
                    }
                    
                    // Direct response - we're done
                    if (parsed.response) {
                        console.log('[BrowserAgent] ✅ Final response:', parsed.response);
                        return { content: parsed.response, tools_used: toolsUsed };
                    }
                    
                    // Fallback
                    console.log('[BrowserAgent] No response or tool_call, returning raw');
                    return { content: llmResponse, tools_used: toolsUsed };
                    
                } catch (iterError) {
                    console.error(`[BrowserAgent] Error in iteration ${iteration}:`, iterError);
                    // Try to continue if possible, or return error on last iteration
                    if (iteration === this.maxIterations) {
                        throw iterError;
                    }
                }
            }
            
            console.log('[BrowserAgent] Max iterations reached');
            return { content: 'I had trouble processing your request. Please try again.', tools_used: toolsUsed };
            
        } catch (error) {
            console.error('[BrowserAgent] Fatal error:', error);
            throw new Error(`BrowserAgent failed: ${error.message}`);
        }
    }
}

// Singleton instance
export const browserAgent = new BrowserAgent();
