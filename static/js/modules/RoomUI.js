/**
 * RoomUI - Modern UI Controller for Private Rooms
 * 
 * Best Practices:
 * - Template literals for clean HTML generation
 * - Event delegation for performance
 * - Separation of concerns (UI separate from logic)
 * - Accessibility (ARIA labels, keyboard navigation)
 * - Responsive design (Bootstrap 5)
 * - O-T-E Standards throughout
 */

import { RoomManager } from './RoomManager.js';

export class RoomUI {
    constructor(containerId = 'room-container') {
        this.roomManager = new RoomManager();
        this.container = document.getElementById(containerId);
        
        if (!this.container) {
            console.error('[ERROR] RoomUI: container not found', { id: containerId });
            return;
        }
        
        console.log('[TRACE] RoomUI initialized', { container: containerId });
        
        // Initialize UI
        this.render();
        this.attachEventListeners();
        this.loadRooms();
        this.loadInvites();
    }

    /**
     * Render main UI structure
     * OBSERVABILITY: Logs UI rendering
     */
    render() {
        console.log('[TRACE] RoomUI.render: rendering main structure');
        
        this.container.innerHTML = `
            <!-- Room List Sidebar -->
            <div class="room-sidebar" id="room-sidebar">
                <div class="room-sidebar-header">
                    <h5>💬 Private Rooms</h5>
                    <button class="btn btn-sm btn-primary" id="create-room-btn" title="Create New Room">
                        <i class="bi bi-plus-lg"></i> New
                    </button>
                </div>
                
                <!-- Pending Invites -->
                <div id="pending-invites-container"></div>
                
                <!-- Rooms List -->
                <div id="rooms-list-container">
                    <div class="text-center text-muted p-3">
                        <div class="spinner-border spinner-border-sm" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <div>Loading rooms...</div>
                    </div>
                </div>
            </div>

            <!-- Room Chat Area -->
            <div class="room-chat-area" id="room-chat-area">
                <div class="room-chat-placeholder">
                    <i class="bi bi-chat-dots" style="font-size: 4rem; color: #ccc;"></i>
                    <h4>Select a room to start chatting</h4>
                    <p class="text-muted">or create a new room to invite others</p>
                </div>
            </div>

            <!-- Modals -->
            ${this.getCreateRoomModal()}
            ${this.getPasswordPromptModal()}
        `;
    }

    /**
     * Create Room Modal HTML
     */
    getCreateRoomModal() {
        return `
            <div class="modal fade" id="createRoomModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Create Private Room</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="create-room-form">
                                <div class="mb-3">
                                    <label for="room-name" class="form-label">Room Name</label>
                                    <input type="text" class="form-control" id="room-name" 
                                           placeholder="My Private Room" maxlength="100">
                                    <small class="form-text text-muted">Optional - auto-generated if empty</small>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">🔒 Password Protection</label>
                                    <div class="form-check form-switch mb-2">
                                        <input class="form-check-input" type="checkbox" id="enable-password">
                                        <label class="form-check-label" for="enable-password">
                                            Protect with password
                                        </label>
                                    </div>
                                    <input type="password" class="form-control" id="room-password" 
                                           placeholder="Enter password" disabled>
                                    <small class="form-text text-muted">Invitees will need this password to join</small>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">🤖 AI Assistant</label>
                                    <div class="form-check form-switch">
                                        <input class="form-check-input" type="checkbox" id="enable-ai" checked>
                                        <label class="form-check-label" for="enable-ai">
                                            Include AI to help with communication
                                        </label>
                                    </div>
                                </div>
                                
                                <div class="alert alert-info" role="alert">
                                    <strong>Note:</strong> You can invite users to the room after creating it.
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="create-room-submit">
                                Create Room
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Password Prompt Modal HTML
     */
    getPasswordPromptModal() {
        return `
            <div class="modal fade" id="passwordPromptModal" tabindex="-1">
                <div class="modal-dialog modal-sm">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">🔒 Password Required</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p class="text-muted mb-3">This room is password-protected</p>
                            <input type="password" class="form-control" id="invite-password" 
                                   placeholder="Enter room password" autocomplete="off">
                            <div id="password-error" class="text-danger small mt-2" style="display:none;"></div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="submit-password">Join</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Attach event listeners using event delegation
     * OBSERVABILITY: Logs all user interactions
     */
    attachEventListeners() {
        console.log('[TRACE] RoomUI.attachEventListeners: setting up listeners');
        
        // Event delegation on container
        this.container.addEventListener('click', (e) => {
            const target = e.target.closest('[data-action]');
            if (!target) return;
            
            const action = target.dataset.action;
            const data = { ...target.dataset };
            
            // OBSERVABILITY: Log user action
            console.log('[TRACE] User action', { action, data });
            
            this.handleAction(action, data, target);
        });
        
        // Create room button
        const createBtn = document.getElementById('create-room-btn');
        if (createBtn) {
            createBtn.addEventListener('click', () => this.showCreateRoomModal());
        }
        
        // Create room form submission
        const submitBtn = document.getElementById('create-room-submit');
        if (submitBtn) {
            submitBtn.addEventListener('click', () => this.handleCreateRoom());
        }
        
        // Password toggle
        const passwordToggle = document.getElementById('enable-password');
        if (passwordToggle) {
            passwordToggle.addEventListener('change', (e) => {
                document.getElementById('room-password').disabled = !e.target.checked;
            });
        }
        
        // Password prompt submission
        const submitPassword = document.getElementById('submit-password');
        if (submitPassword) {
            submitPassword.addEventListener('click', () => this.handlePasswordSubmit());
        }
    }

    /**
     * Handle user actions
     * EVALUATION: Validates actions and provides feedback
     */
    async handleAction(action, data, element) {
        console.log('[TRACE] handleAction', { action, data });
        
        switch (action) {
            case 'select-room':
                await this.selectRoom(parseInt(data.roomId));
                break;
                
            case 'accept-invite':
                await this.acceptInvite(parseInt(data.inviteId), data.hasPassword === 'true');
                break;
                
            case 'decline-invite':
                await this.declineInvite(parseInt(data.inviteId));
                break;
                
            case 'leave-room':
                await this.leaveRoom(parseInt(data.roomId));
                break;
                
            default:
                console.warn('[EVAL] Unknown action', { action });
        }
    }

    /**
     * Load and display rooms
     * TRACEABILITY: Tracks room count and IDs
     */
    async loadRooms() {
        console.log('[TRACE] loadRooms: fetching rooms');
        
        const rooms = await this.roomManager.fetchRooms();
        const container = document.getElementById('rooms-list-container');
        
        if (!container) return;
        
        if (rooms.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted p-3">
                    <p>No rooms yet</p>
                    <small>Create your first room above!</small>
                </div>
            `;
            return;
        }
        
        // OBSERVABILITY: Log rooms loaded
        console.log('[TRACE] loadRooms: rendering', { count: rooms.length });
        
        container.innerHTML = rooms.map(room => `
            <div class="room-item" data-action="select-room" data-room-id="${room.id}">
                <div class="room-icon">
                    ${room.has_password ? '🔒' : '💬'}
                </div>
                <div class="room-info">
                    <div class="room-name">${this.escapeHtml(room.name || 'Unnamed Room')}</div>
                    <div class="room-meta">
                        ${room.member_count} members
                        ${room.ai_enabled ? '• 🤖 AI' : ''}
                    </div>
                </div>
            </div>
        `).join('');
    }

    /**
     * Load and display pending invites
     * OBSERVABILITY: Logs invite count
     */
    async loadInvites() {
        console.log('[TRACE] loadInvites: fetching invites');
        
        const invites = await this.roomManager.fetchPendingInvites();
        const container = document.getElementById('pending-invites-container');
        
        if (!container) return;
        
        if (invites.length === 0) {
            container.innerHTML = '';
            return;
        }
        
        // OBSERVABILITY: Log invites loaded
        console.log('[TRACE] loadInvites: rendering', { count: invites.length });
        
        container.innerHTML = `
            <div class="invites-section">
                <div class="invites-header">
                    <small class="text-muted">📨 INVITATIONS</small>
                </div>
                ${invites.map(invite => `
                    <div class="invite-item">
                        <div class="invite-info">
                            <strong>${this.escapeHtml(invite.room_name || 'Room')}</strong>
                            <small>from ${this.escapeHtml(invite.inviter_username)}</small>
                            ${invite.has_password ? '<span class="badge bg-warning">🔒</span>' : ''}
                        </div>
                        <div class="invite-actions">
                            <button class="btn btn-sm btn-success" 
                                    data-action="accept-invite" 
                                    data-invite-id="${invite.id}"
                                    data-has-password="${invite.has_password}">
                                ✓
                            </button>
                            <button class="btn btn-sm btn-danger" 
                                    data-action="decline-invite" 
                                    data-invite-id="${invite.id}">
                                ✗
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    /**
     * Show create room modal
     */
    showCreateRoomModal() {
        console.log('[TRACE] showCreateRoomModal');
        
        const modal = new bootstrap.Modal(document.getElementById('createRoomModal'));
        modal.show();
    }

    /**
     * Handle create room form submission
     * EVALUATION: Validates input and provides feedback
     */
    async handleCreateRoom() {
        console.log('[TRACE] handleCreateRoom: validating form');
        
        const nameInput = document.getElementById('room-name');
        const passwordEnabled = document.getElementById('enable-password').checked;
        const passwordInput = document.getElementById('room-password');
        const aiEnabled = document.getElementById('enable-ai').checked;
        
        const name = nameInput.value.trim() || null;
        const password = passwordEnabled ? passwordInput.value.trim() : null;
        
        // EVALUATION: Validate password if enabled
        if (passwordEnabled && (!password || password.length < 3)) {
            alert('Password must be at least 3 characters');
            console.log('[EVAL] handleCreateRoom: password validation failed');
            return;
        }
        
        // Show loading state
        const submitBtn = document.getElementById('create-room-submit');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Creating...';
        
        try {
            await this.roomManager.createRoom(name, [], password, aiEnabled);
            
            // OBSERVABILITY: Log success
            console.log('[TRACE] handleCreateRoom: success');
            
            // Close modal
            bootstrap.Modal.getInstance(document.getElementById('createRoomModal')).hide();
            
            // Refresh rooms list
            await this.loadRooms();
            
            // Reset form
            document.getElementById('create-room-form').reset();
            
            // Show success message
            this.showToast('Room created successfully!', 'success');
            
        } catch (error) {
            console.error('[ERROR] handleCreateRoom: exception', { error: error.message });
            alert(`Failed to create room: ${error.message}`);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Create Room';
        }
    }

    /**
     * Accept an invite
     * EVALUATION: Checks if password needed and handles accordingly
     */
    async acceptInvite(inviteId, hasPassword) {
        console.log('[TRACE] acceptInvite', { invite_id: inviteId, has_password: hasPassword });
        
        if (hasPassword) {
            // Show password prompt
            this.currentInviteId = inviteId;
            const modal = new bootstrap.Modal(document.getElementById('passwordPromptModal'));
            modal.show();
            document.getElementById('invite-password').value = '';
            document.getElementById('password-error').style.display = 'none';
        } else {
            // Accept without password
            const result = await this.roomManager.acceptInvite(inviteId);
            
            if (result.success) {
                console.log('[TRACE] acceptInvite: success');
                this.showToast('Invite accepted!', 'success');
                await Promise.all([this.loadRooms(), this.loadInvites()]);
            } else {
                console.error('[ERROR] acceptInvite: failed', { error: result.error });
                alert(`Failed to accept invite: ${result.error}`);
            }
        }
    }

    /**
     * Handle password submission for protected room
     */
    async handlePasswordSubmit() {
        const password = document.getElementById('invite-password').value.trim();
        const errorDiv = document.getElementById('password-error');
        
        if (!password) {
            errorDiv.textContent = 'Please enter a password';
            errorDiv.style.display = 'block';
            return;
        }
        
        console.log('[TRACE] handlePasswordSubmit', { invite_id: this.currentInviteId });
        
        const result = await this.roomManager.acceptInvite(this.currentInviteId, password);
        
        if (result.success) {
            // Close modal
            bootstrap.Modal.getInstance(document.getElementById('passwordPromptModal')).hide();
            
            console.log('[TRACE] handlePasswordSubmit: success');
            this.showToast('Invite accepted!', 'success');
            await Promise.all([this.loadRooms(), this.loadInvites()]);
        } else {
            console.log('[EVAL] handlePasswordSubmit: wrong password');
            errorDiv.textContent = 'Invalid password. Please try again.';
            errorDiv.style.display = 'block';
        }
    }

    /**
     * Decline an invite
     */
    async declineInvite(inviteId) {
        console.log('[TRACE] declineInvite', { invite_id: inviteId });
        
        const success = await this.roomManager.declineInvite(inviteId);
        
        if (success) {
            this.showToast('Invite declined', 'info');
            await this.loadInvites();
        } else {
            alert('Failed to decline invite');
        }
    }

    /**
     * Select and open a room
     * TRACEABILITY: Logs room selection and connection
     */
    async selectRoom(roomId) {
        console.log('[TRACE] selectRoom', { room_id: roomId });
        
        // This will be implemented in the next file
        // For now, just log the selection
        this.showToast(`Room ${roomId} selected (chat interface coming next)`, 'info');
    }

    /**
     * Leave a room
     */
    async leaveRoom(roomId) {
        console.log('[TRACE] leaveRoom', { room_id: roomId });
        
        if (!confirm('Are you sure you want to leave this room?')) {
            return;
        }
        
        const success = await this.roomManager.leaveRoom(roomId);
        
        if (success) {
            this.showToast('Left room', 'info');
            await this.loadRooms();
        } else {
            alert('Failed to leave room');
        }
    }

    /**
     * Show toast notification
     * OBSERVABILITY: User feedback
     */
    showToast(message, type = 'info') {
        console.log('[TRACE] showToast', { message, type });
        
        // Simple toast implementation (can be enhanced with Bootstrap Toast)
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'} toast-notification`;
        toast.textContent = message;
        toast.style.cssText = 'position:fixed;top:20px;right:20px;z-index:9999;min-width:200px;';
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    /**
     * Escape HTML to prevent XSS
     * SECURITY: Essential for user-generated content
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

export default RoomUI;
