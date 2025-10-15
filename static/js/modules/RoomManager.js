/**
 * RoomManager - Modern ES6 Module for Private Chat Rooms
 * 
 * Features:
 * - Create password-protected rooms
 * - Send/accept/decline invites
 * - Real-time WebSocket messaging
 * - O-T-E Standards: Observability, Traceability, Evaluation
 * 
 * Best Practices:
 * - ES6 classes and async/await
 * - Event delegation for performance
 * - Separation of concerns
 * - Comprehensive error handling
 * - Logging for observability
 */

export class RoomManager {
    constructor(apiBaseUrl = '/api', wsBaseUrl = 'ws://localhost:8000/ws') {
        this.apiBaseUrl = apiBaseUrl;
        this.wsBaseUrl = wsBaseUrl;
        this.currentRoomId = null;
        this.rooms = [];
        this.pendingInvites = [];
        this.roomSocket = null;
        
        // OBSERVABILITY: Log initialization
        console.log('[TRACE] RoomManager initialized', { apiBaseUrl, wsBaseUrl });
    }

    /**
     * Get auth token from storage
     * TRACEABILITY: Tracks token presence
     */
    getAuthToken() {
        const token = localStorage.getItem('access_token') || window.ACCESS_TOKEN;
        const hasToken = !!token;
        
        // OBSERVABILITY: Log token check
        console.log('[TRACE] getAuthToken', { hasToken });
        
        return token ? token.replace(/^Bearer\s+/, '') : null;
    }

    /**
     * Get auth headers for API requests
     */
    getAuthHeaders() {
        const token = this.getAuthToken();
        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }

    /**
     * Fetch user's rooms from API
     * EVALUATION: Validates response and handles errors
     */
    async fetchRooms() {
        console.log('[TRACE] fetchRooms: starting');
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/rooms/`, {
                headers: this.getAuthHeaders()
            });

            // EVALUATION: Check response status
            if (!response.ok) {
                console.log('[EVAL] fetchRooms failed', { status: response.status });
                throw new Error(`Failed to fetch rooms: ${response.statusText}`);
            }

            this.rooms = await response.json();
            
            // OBSERVABILITY: Log success
            console.log('[TRACE] fetchRooms success', { count: this.rooms.length });
            
            return this.rooms;
        } catch (error) {
            // OBSERVABILITY: Log error with context
            console.error('[ERROR] fetchRooms exception', { error: error.message });
            return [];
        }
    }

    /**
     * Fetch pending invites
     * TRACEABILITY: Tracks invite count and IDs
     */
    async fetchPendingInvites() {
        console.log('[TRACE] fetchPendingInvites: starting');
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/rooms/invites/pending`, {
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                console.log('[EVAL] fetchPendingInvites failed', { status: response.status });
                throw new Error(`Failed to fetch invites: ${response.statusText}`);
            }

            this.pendingInvites = await response.json();
            
            // OBSERVABILITY: Log invites
            console.log('[TRACE] fetchPendingInvites success', { 
                count: this.pendingInvites.length,
                invite_ids: this.pendingInvites.map(i => i.id)
            });
            
            return this.pendingInvites;
        } catch (error) {
            console.error('[ERROR] fetchPendingInvites exception', { error: error.message });
            return [];
        }
    }

    /**
     * Create a new room
     * TRACEABILITY: Logs room creation with all parameters
     */
    async createRoom(name, inviteeIds = [], password = null, aiEnabled = true) {
        console.log('[TRACE] createRoom: starting', { 
            name, 
            invitees: inviteeIds.length,
            protected: !!password,
            ai: aiEnabled 
        });
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/rooms/`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify({
                    name: name || null,
                    invitees: inviteeIds,
                    room_type: 'group',
                    ai_enabled: aiEnabled,
                    password: password || null
                })
            });

            // EVALUATION: Validate response
            if (!response.ok) {
                const errorData = await response.json();
                console.log('[EVAL] createRoom failed', { 
                    status: response.status,
                    detail: errorData.detail 
                });
                throw new Error(errorData.detail || 'Failed to create room');
            }

            const room = await response.json();
            
            // OBSERVABILITY: Log successful creation
            console.log('[TRACE] createRoom success', { 
                room_id: room.id,
                name: room.name,
                members: room.member_count 
            });
            
            // Refresh rooms list
            await this.fetchRooms();
            
            return room;
        } catch (error) {
            console.error('[ERROR] createRoom exception', { error: error.message });
            throw error;
        }
    }

    /**
     * Accept an invite
     * EVALUATION: Validates password requirement and success
     */
    async acceptInvite(inviteId, password = null) {
        console.log('[TRACE] acceptInvite: starting', { 
            invite_id: inviteId,
            has_password: !!password 
        });
        
        try {
            const body = password ? { password } : {};
            
            const response = await fetch(`${this.apiBaseUrl}/rooms/invites/${inviteId}/accept`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify(body)
            });

            // EVALUATION: Check if password was needed
            if (!response.ok) {
                const errorData = await response.json();
                console.log('[EVAL] acceptInvite failed', { 
                    invite_id: inviteId,
                    status: response.status,
                    detail: errorData.detail 
                });
                
                // Return error info for UI to handle (e.g., show password prompt)
                return { 
                    success: false, 
                    needsPassword: response.status === 400,
                    error: errorData.detail 
                };
            }

            // OBSERVABILITY: Log success
            console.log('[TRACE] acceptInvite success', { invite_id: inviteId });
            
            // Refresh rooms and invites
            await Promise.all([
                this.fetchRooms(),
                this.fetchPendingInvites()
            ]);
            
            return { success: true };
        } catch (error) {
            console.error('[ERROR] acceptInvite exception', { 
                invite_id: inviteId,
                error: error.message 
            });
            return { success: false, error: error.message };
        }
    }

    /**
     * Decline an invite
     * TRACEABILITY: Logs invite ID being declined
     */
    async declineInvite(inviteId) {
        console.log('[TRACE] declineInvite: starting', { invite_id: inviteId });
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/rooms/invites/${inviteId}/decline`, {
                method: 'POST',
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                console.log('[EVAL] declineInvite failed', { 
                    invite_id: inviteId,
                    status: response.status 
                });
                throw new Error('Failed to decline invite');
            }

            console.log('[TRACE] declineInvite success', { invite_id: inviteId });
            
            // Refresh invites
            await this.fetchPendingInvites();
            
            return true;
        } catch (error) {
            console.error('[ERROR] declineInvite exception', { 
                invite_id: inviteId,
                error: error.message 
            });
            return false;
        }
    }

    /**
     * Connect to a room's WebSocket
     * OBSERVABILITY: Logs connection status and events
     */
    connectToRoom(roomId, onMessage) {
        const token = this.getAuthToken();
        
        if (!token) {
            console.error('[ERROR] connectToRoom: no auth token');
            return null;
        }

        console.log('[TRACE] connectToRoom: starting', { room_id: roomId });

        // Close existing connection
        if (this.roomSocket) {
            console.log('[TRACE] connectToRoom: closing existing connection');
            this.roomSocket.close();
        }

        // Create WebSocket connection
        const wsUrl = `${this.wsBaseUrl}/rooms/${roomId}?token=${token}`;
        this.roomSocket = new WebSocket(wsUrl);
        this.currentRoomId = roomId;

        // OBSERVABILITY: Log connection events
        this.roomSocket.onopen = () => {
            console.log('[TRACE] WebSocket connected', { room_id: roomId });
        };

        this.roomSocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('[TRACE] WebSocket message received', { 
                    type: data.type,
                    room_id: roomId 
                });
                
                if (onMessage) {
                    onMessage(data);
                }
            } catch (error) {
                console.error('[ERROR] WebSocket message parse error', { error: error.message });
            }
        };

        this.roomSocket.onerror = (error) => {
            console.error('[ERROR] WebSocket error', { room_id: roomId, error });
        };

        this.roomSocket.onclose = () => {
            console.log('[TRACE] WebSocket closed', { room_id: roomId });
            this.roomSocket = null;
            this.currentRoomId = null;
        };

        return this.roomSocket;
    }

    /**
     * Send message to current room
     * EVALUATION: Validates message and connection
     */
    sendMessage(content) {
        // EVALUATION: Check connection
        if (!this.roomSocket || this.roomSocket.readyState !== WebSocket.OPEN) {
            console.error('[EVAL] sendMessage failed: WebSocket not connected');
            return false;
        }

        // EVALUATION: Validate message
        if (!content || !content.trim()) {
            console.error('[EVAL] sendMessage failed: empty message');
            return false;
        }

        console.log('[TRACE] sendMessage: sending', { 
            room_id: this.currentRoomId,
            length: content.length 
        });

        this.roomSocket.send(JSON.stringify({
            type: 'message',
            content: content.trim()
        }));

        return true;
    }

    /**
     * Disconnect from current room
     * OBSERVABILITY: Logs disconnection
     */
    disconnectFromRoom() {
        if (this.roomSocket) {
            console.log('[TRACE] disconnectFromRoom', { room_id: this.currentRoomId });
            this.roomSocket.close();
            this.roomSocket = null;
            this.currentRoomId = null;
        }
    }

    /**
     * Leave a room
     * TRACEABILITY: Logs room leave with user and room IDs
     */
    async leaveRoom(roomId) {
        console.log('[TRACE] leaveRoom: starting', { room_id: roomId });
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/rooms/${roomId}/leave`, {
                method: 'POST',
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                console.log('[EVAL] leaveRoom failed', { 
                    room_id: roomId,
                    status: response.status 
                });
                throw new Error('Failed to leave room');
            }

            console.log('[TRACE] leaveRoom success', { room_id: roomId });
            
            // Disconnect WebSocket if this is the current room
            if (this.currentRoomId === roomId) {
                this.disconnectFromRoom();
            }
            
            // Refresh rooms
            await this.fetchRooms();
            
            return true;
        } catch (error) {
            console.error('[ERROR] leaveRoom exception', { 
                room_id: roomId,
                error: error.message 
            });
            return false;
        }
    }
}

// Export for use in other modules
export default RoomManager;
