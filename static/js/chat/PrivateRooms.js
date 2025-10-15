/**
 * Private Rooms Module
 * Handles private chat room creation, listing, and management
 * 
 * O-T-E Standards:
 * - [TRACE] for operation tracking
 * - [EVAL] for validation checks
 * - [ERROR] for error handling
 */

console.log('[TRACE] PrivateRooms.js loaded');

class PrivateRoomsManager {
    constructor() {
        this.apiBaseUrl = '/api/rooms';
        this.rooms = [];
        this.activeRoomId = null;
        this.modal = null;
        this.onRoomSelected = null; // Callback for room selection
        
        console.log('[TRACE] PrivateRoomsManager initialized');
    }

    /**
     * Initialize the private rooms system
     */
    async init() {
        console.log('[TRACE] PrivateRoomsManager.init: starting');
        
        try {
            // Get DOM elements
            this.elements = {
                privateChatBtn: document.getElementById('private-chat-btn'),
                roomsList: document.getElementById('rooms-list'),
                noRoomsMsg: document.getElementById('no-rooms-msg'),
                createRoomBtn: document.getElementById('create-room-btn'),
                roomInvitesSelect: document.getElementById('room-invites'),
                passwordToggle: document.getElementById('room-password-toggle'),
                passwordInputGroup: document.getElementById('password-input-group'),
                invitesList: document.getElementById('invites-list'),
                invitesHeader: document.getElementById('invites-header'),
                backToMainBtn: document.getElementById('back-to-main-btn')
            };

            // Setup modal
            this.modal = new bootstrap.Modal(document.getElementById('createRoomModal'));

            // Attach event listeners
            this.attachEventListeners();

            // Load rooms and invites
            await this.loadRooms();
            await this.loadPendingInvites();
            
            // Auto-refresh every 30 seconds
            setInterval(() => {
                this.loadRooms();
                this.loadPendingInvites();
            }, 30000);

            console.log('[TRACE] PrivateRoomsManager.init: complete');
        } catch (error) {
            console.error('[ERROR] PrivateRoomsManager.init failed:', error);
        }
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        console.log('[TRACE] Attaching event listeners');

        // Private chat button - open modal
        if (this.elements.privateChatBtn) {
            this.elements.privateChatBtn.addEventListener('click', () => {
                console.log('[TRACE] Private chat button clicked');
                this.openCreateRoomModal();
            });
        }

        // Create room button
        if (this.elements.createRoomBtn) {
            this.elements.createRoomBtn.addEventListener('click', () => {
                console.log('[TRACE] Create room button clicked');
                this.handleCreateRoom();
            });
        }

        // Password toggle
        if (this.elements.passwordToggle) {
            this.elements.passwordToggle.addEventListener('change', (e) => {
                const isChecked = e.target.checked;
                this.elements.passwordInputGroup.style.display = isChecked ? 'block' : 'none';
                console.log('[TRACE] Password protection toggled:', isChecked);
            });
        }
        
        // Back to main chat button
        if (this.elements.backToMainBtn) {
            this.elements.backToMainBtn.addEventListener('click', () => {
                console.log('[TRACE] Back to main chat clicked');
                // Trigger callback with null to switch back to main
                if (this.onRoomSelected) {
                    this.onRoomSelected({ id: 'main', name: 'General Chat', is_main: true });
                }
                this.elements.backToMainBtn.style.display = 'none';
                // Clear active room
                document.querySelectorAll('.room-item').forEach(item => item.classList.remove('active'));
            });
        }
    }
    
    /**
     * Load pending invites
     */
    async loadPendingInvites() {
        console.log('[TRACE] loadPendingInvites: fetching invites');
        
        try {
            const token = this.getToken();
            if (!token) return;
            
            const response = await fetch('/api/rooms/invites/pending', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const invites = await response.json();
            console.log('[TRACE] loadPendingInvites: success', { count: invites.length });
            
            this.renderInvites(invites);
        } catch (error) {
            console.error('[ERROR] loadPendingInvites failed:', error);
        }
    }
    
    /**
     * Render pending invites
     */
    renderInvites(invites) {
        if (!this.elements.invitesList) return;
        
        // Show/hide header
        if (this.elements.invitesHeader) {
            this.elements.invitesHeader.style.display = invites.length > 0 ? 'block' : 'none';
        }
        
        // Clear existing
        this.elements.invitesList.innerHTML = '';
        
        if (invites.length === 0) return;
        
        // Render each invite
        invites.forEach(invite => {
            const div = document.createElement('div');
            div.className = 'alert alert-warning p-2 mb-2';
            div.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${this.escapeHtml(invite.room_name || 'Private Room')}</strong>
                        <br>
                        <small>from ${this.escapeHtml(invite.inviter_username)}</small>
                        ${invite.has_password ? ' <i class="bi bi-lock"></i>' : ''}
                    </div>
                    <div>
                        <button class="btn btn-sm btn-success me-1" data-action="accept-invite" data-invite-id="${invite.id}" data-has-password="${invite.has_password}">
                            <i class="bi bi-check"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" data-action="decline-invite" data-invite-id="${invite.id}">
                            <i class="bi bi-x"></i>
                        </button>
                    </div>
                </div>
            `;
            
            // Add event listeners
            div.querySelector('[data-action="accept-invite"]').addEventListener('click', () => {
                this.handleAcceptInvite(invite.id, invite.has_password);
            });
            
            div.querySelector('[data-action="decline-invite"]').addEventListener('click', () => {
                this.handleDeclineInvite(invite.id);
            });
            
            this.elements.invitesList.appendChild(div);
        });
    }
    
    /**
     * Handle accept invite
     * 
     * IMPORTANT: Invited users do NOT need to provide password.
     * Password protection only applies to uninvited users joining directly.
     */
    async handleAcceptInvite(inviteId, hasPassword) {
        console.log('[TRACE] handleAcceptInvite:', { inviteId, hasPassword });
        
        // No password needed for invited users - they were explicitly invited!
        console.log('[TRACE] Accepting invite without password (invited users bypass password)');
        
        try {
            const token = this.getToken();
            const response = await fetch(`/api/rooms/invites/${inviteId}/accept`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to accept invite');
            }
            
            console.log('[TRACE] handleAcceptInvite: success');
            this.showSuccess('Invite accepted! Room added to your list.');
            
            // Reload rooms and invites
            await this.loadRooms();
            await this.loadPendingInvites();
            
        } catch (error) {
            console.error('[ERROR] handleAcceptInvite failed:', error);
            this.showError(error.message || 'Failed to accept invite');
        }
    }
    
    /**
     * Handle decline invite
     */
    async handleDeclineInvite(inviteId) {
        console.log('[TRACE] handleDeclineInvite:', { inviteId });
        
        if (!confirm('Decline this invite?')) return;
        
        try {
            const token = this.getToken();
            const response = await fetch(`/api/rooms/invites/${inviteId}/decline`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to decline invite');
            }
            
            console.log('[TRACE] handleDeclineInvite: success');
            this.showSuccess('Invite declined');
            
            // Reload invites
            await this.loadPendingInvites();
            
        } catch (error) {
            console.error('[ERROR] handleDeclineInvite failed:', error);
            this.showError('Failed to decline invite');
        }
    }

    /**
     * Get authentication token
     */
    getToken() {
        const token = window.currentUser?.token || window.ACCESS_TOKEN || localStorage.getItem('access_token');
        if (!token) {
            console.error('[ERROR] No authentication token found');
        }
        return token;
    }

    /**
     * Load rooms from API
     */
    async loadRooms() {
        console.log('[TRACE] loadRooms: fetching rooms');

        try {
            const token = this.getToken();
            if (!token) {
                console.log('[EVAL] loadRooms: no token, skipping');
                return;
            }

            const response = await fetch(`${this.apiBaseUrl}/`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            this.rooms = await response.json();
            console.log('[TRACE] loadRooms: success', { count: this.rooms.length });

            this.renderRooms();
        } catch (error) {
            console.error('[ERROR] loadRooms failed:', error);
            this.showError('Failed to load rooms');
        }
    }

    /**
     * Render rooms list
     */
    renderRooms() {
        console.log('[TRACE] renderRooms: rendering', { count: this.rooms.length });

        if (!this.elements.roomsList) {
            console.log('[EVAL] renderRooms: roomsList element not found');
            return;
        }

        // Show/hide no rooms message
        if (this.elements.noRoomsMsg) {
            this.elements.noRoomsMsg.style.display = this.rooms.length === 0 ? 'block' : 'none';
        }

        // Clear existing rooms (except no rooms message)
        const existingRooms = this.elements.roomsList.querySelectorAll('.room-item');
        existingRooms.forEach(item => item.remove());

        // Render each room
        this.rooms.forEach(room => {
            const roomElement = this.createRoomElement(room);
            this.elements.roomsList.appendChild(roomElement);
        });

        console.log('[TRACE] renderRooms: complete');
    }

    /**
     * Create room element
     */
    createRoomElement(room) {
        const div = document.createElement('div');
        div.className = 'room-item';
        div.dataset.roomId = room.id;

        // Determine icon based on room properties (priority order)
        let icon = '💬';  // Default
        
        // Priority 1: AI enabled (most common, all rooms)
        if (room.ai_enabled) {
            icon = '🤖';
        }
        
        // Priority 2: Password protection (security feature)
        if (room.has_password) {
            icon = '🔒';
        }
        
        // Priority 3: Visibility (only show if PUBLIC, since hidden is default)
        if (room.is_public) {
            icon = '👁️';  // Public/discoverable room
        }
        
        // OBSERVABILITY: Log room visibility
        console.log('[TRACE] createRoomElement:', {
            room_id: room.id,
            name: room.name,
            is_public: room.is_public,
            icon: icon
        });

        // Check if current user is creator
        const currentUserId = window.currentUser?.id;
        const isCreator = room.creator_id === currentUserId;

        div.innerHTML = `
            <div class="room-icon">${icon}</div>
            <div class="room-details">
                <div class="room-name">${this.escapeHtml(room.name || 'Unnamed Room')}</div>
                <div class="room-info">
                    <span><i class="bi bi-people"></i> ${room.member_count || 0}</span>
                    ${room.has_password ? '<span title="Password protected"><i class="bi bi-lock"></i></span>' : ''}
                    ${room.is_public ? '<span title="Public (discoverable)"><i class="bi bi-eye"></i></span>' : '<span title="Hidden (invite-only)"><i class="bi bi-eye-slash"></i></span>'}
                    ${room.ai_enabled ? '<span title="AI monitoring active"><i class="bi bi-robot"></i></span>' : ''}
                </div>
            </div>
            ${isCreator ? '<button class="btn btn-sm btn-danger delete-room-btn" data-room-id="' + room.id + '" title="Delete room"><i class="bi bi-trash"></i></button>' : ''}
        `;

        // Click handler for room selection
        const roomDetails = div.querySelector('.room-details');
        roomDetails.addEventListener('click', () => {
            console.log('[TRACE] Room selected:', { room_id: room.id, name: room.name });
            this.selectRoom(room);
        });

        // Delete button handler (if creator)
        if (isCreator) {
            const deleteBtn = div.querySelector('.delete-room-btn');
            deleteBtn.addEventListener('click', async (e) => {
                e.stopPropagation();  // Don't trigger room selection
                await this.deleteRoom(room.id, room.name);
            });
        }

        return div;
    }

    /**
     * Select a room
     */
    selectRoom(room) {
        console.log('[TRACE] selectRoom:', { room_id: room.id });

        // Update active state
        this.activeRoomId = room.id;

        // Update UI
        const allRoomItems = document.querySelectorAll('.room-item');
        allRoomItems.forEach(item => {
            if (parseInt(item.dataset.roomId) === room.id) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
        
        // Show back button
        if (this.elements.backToMainBtn) {
            this.elements.backToMainBtn.style.display = 'block';
        }

        // Trigger callback if set
        if (this.onRoomSelected) {
            this.onRoomSelected(room);
        }

        console.log('[TRACE] Room selection complete');
    }

    /**
     * Open create room modal
     */
    async openCreateRoomModal() {
        console.log('[TRACE] openCreateRoomModal: opening');

        // Populate online users for invites
        await this.populateOnlineUsers();

        // Reset form
        document.getElementById('create-room-form').reset();
        this.elements.passwordInputGroup.style.display = 'none';

        // Show modal
        this.modal.show();
    }

    /**
     * Populate online users in invite select
     */
    async populateOnlineUsers() {
        console.log('[TRACE] populateOnlineUsers: fetching users');

        if (!this.elements.roomInvitesSelect) return;

        try {
            const token = this.getToken();
            if (!token) return;

            const response = await fetch('/api/users/', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch users');
            }

            const users = await response.json();
            const currentUserId = parseInt(window.currentUser?.id);

            // Clear existing options
            this.elements.roomInvitesSelect.innerHTML = '';

            // Add users (except current user)
            users.forEach(user => {
                if (user.id !== currentUserId) {
                    const option = document.createElement('option');
                    option.value = user.id;
                    option.textContent = `${user.username}${user.is_online ? ' 🟢' : ''}`;
                    this.elements.roomInvitesSelect.appendChild(option);
                }
            });

            console.log('[TRACE] populateOnlineUsers: complete', { count: users.length });
        } catch (error) {
            console.error('[ERROR] populateOnlineUsers failed:', error);
        }
    }

    /**
     * Handle create room
     */
    async handleCreateRoom() {
        console.log('[TRACE] handleCreateRoom: starting');

        try {
            // Get form values
            const roomName = document.getElementById('room-name').value.trim() || null;
            const hasPassword = document.getElementById('room-password-toggle').checked;
            const password = hasPassword ? document.getElementById('room-password').value : null;
            const aiEnabled = true; // AI is always enabled for moderation
            const isPublic = document.getElementById('room-public-toggle').checked;
            const inviteUserIds = Array.from(this.elements.roomInvitesSelect.selectedOptions).map(opt => parseInt(opt.value));

            // Validation
            if (hasPassword && !password) {
                console.log('[EVAL] handleCreateRoom: password required but empty');
                this.showError('Please enter a password or disable password protection');
                return;
            }

            console.log('[TRACE] handleCreateRoom: creating room', {
                name: roomName,
                has_password: hasPassword,
                ai_enabled: aiEnabled,
                is_public: isPublic,
                invites_count: inviteUserIds.length
            });

            // Create room via API
            const token = this.getToken();
            if (!token) {
                throw new Error('No authentication token');
            }

            const response = await fetch(`${this.apiBaseUrl}/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: roomName,
                    password: password,
                    ai_enabled: aiEnabled,
                    is_public: isPublic,
                    invitees: inviteUserIds
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create room');
            }

            const newRoom = await response.json();
            console.log('[TRACE] handleCreateRoom: room created', { room_id: newRoom.id });

            // Send invites if any
            if (inviteUserIds.length > 0) {
                await this.sendInvites(newRoom.id, inviteUserIds);
            }

            // Close modal
            this.modal.hide();

            // Reload rooms
            await this.loadRooms();

            // Show success
            this.showSuccess(`Room "${newRoom.name}" created successfully!`);

            // Auto-select new room
            this.selectRoom(newRoom);

        } catch (error) {
            console.error('[ERROR] handleCreateRoom failed:', error);
            this.showError(error.message || 'Failed to create room');
        }
    }

    /**
     * Send invites to users
     */
    async sendInvites(roomId, userIds) {
        console.log('[TRACE] sendInvites:', { room_id: roomId, user_ids: userIds });

        try {
            const token = this.getToken();
            if (!token) return;

            const response = await fetch(`${this.apiBaseUrl}/${roomId}/invite`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ user_ids: userIds })
            });

            if (!response.ok) {
                throw new Error('Failed to send invites');
            }

            console.log('[TRACE] sendInvites: success');
        } catch (error) {
            console.error('[ERROR] sendInvites failed:', error);
        }
    }

    /**
     * Delete a room (creator only)
     * 
     * OBSERVABILITY: Logs deletion attempts
     * TRACEABILITY: Tracks room_id
     * EVALUATION: Confirms deletion with user
     */
    async deleteRoom(roomId, roomName) {
        console.log('[TRACE] deleteRoom:', { room_id: roomId, name: roomName });
        
        // EVALUATION: Confirm deletion
        const confirmed = confirm(`Are you sure you want to delete "${roomName}"?\n\nThis will remove the room for all members. This action cannot be undone.`);
        if (!confirmed) {
            console.log('[EVAL] deleteRoom: cancelled by user');
            return;
        }
        
        try {
            const token = this.getToken();
            const response = await fetch(`${this.apiBaseUrl}/${roomId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to delete room');
            }
            
            console.log('[TRACE] deleteRoom: success');
            this.showSuccess('Room deleted successfully');
            
            // Reload rooms list
            await this.loadRooms();
            
            // If deleted room was active, clear selection
            if (this.activeRoomId === roomId) {
                this.activeRoomId = null;
                if (this.elements.backToMainBtn) {
                    this.elements.backToMainBtn.style.display = 'none';
                }
            }
            
        } catch (error) {
            console.error('[ERROR] deleteRoom failed:', error);
            this.showError(error.message || 'Failed to delete room');
        }
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        console.log('[TRACE] showSuccess:', message);
        this.showToast(message, 'success');
    }

    /**
     * Show error message
     */
    showError(message) {
        console.log('[ERROR] showError:', message);
        this.showToast(message, 'danger');
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
        toast.style.zIndex = '9999';
        toast.style.minWidth = '300px';
        toast.innerHTML = `
            <div class="d-flex align-items-center">
                <span class="flex-grow-1">${this.escapeHtml(message)}</span>
                <button type="button" class="btn-close ms-2" data-bs-dismiss="alert"></button>
            </div>
        `;

        document.body.appendChild(toast);

        // Auto-remove after 3 seconds
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export singleton instance
export const privateRoomsManager = new PrivateRoomsManager();
