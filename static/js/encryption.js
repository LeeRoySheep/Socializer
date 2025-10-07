// Encryption service for end-to-end encrypted chat
class EncryptionService {
    constructor() {
        this.algorithm = 'AES-GCM';
        this.key = null;
        this.iv = null;
    }

    // Generate a new encryption key and IV
    async generateKey() {
        try {
            // Generate a random key
            this.key = await crypto.subtle.generateKey(
                {
                    name: this.algorithm,
                    length: 256,
                },
                true,
                ['encrypt', 'decrypt']
            );

            // Generate a random IV (Initialization Vector)
            this.iv = crypto.getRandomValues(new Uint8Array(12));
            
            return {
                key: this.key,
                iv: this.iv
            };
        } catch (error) {
            console.error('Error generating encryption key:', error);
            throw error;
        }
    }

    // Export the key to a string for storage/transmission
    async exportKey() {
        if (!this.key) {
            throw new Error('No key generated yet');
        }
        const exported = await crypto.subtle.exportKey('raw', this.key);
        return this.arrayBufferToBase64(exported);
    }

    // Import a key from a string
    async importKey(keyData) {
        try {
            const keyDataBuffer = this.base64ToArrayBuffer(keyData);
            this.key = await crypto.subtle.importKey(
                'raw',
                keyDataBuffer,
                { name: this.algorithm, length: 256 },
                false,
                ['encrypt', 'decrypt']
            );
            return this.key;
        } catch (error) {
            console.error('Error importing key:', error);
            throw error;
        }
    }

    // Encrypt a message
    async encrypt(message) {
        if (!this.key) {
            throw new Error('Encryption key not set');
        }

        try {
            const encodedMessage = new TextEncoder().encode(message);
            const encryptedData = await crypto.subtle.encrypt(
                {
                    name: this.algorithm,
                    iv: this.iv,
                },
                this.key,
                encodedMessage
            );

            // Combine IV and encrypted data
            const encryptedArray = new Uint8Array(encryptedData);
            const combined = new Uint8Array(this.iv.length + encryptedArray.length);
            combined.set(new Uint8Array(this.iv));
            combined.set(encryptedArray, this.iv.length);

            return this.arrayBufferToBase64(combined);
        } catch (error) {
            console.error('Encryption error:', error);
            throw error;
        }
    }

    // Decrypt a message
    async decrypt(encryptedMessage) {
        if (!this.key) {
            throw new Error('Encryption key not set');
        }

        try {
            const encryptedData = this.base64ToArrayBuffer(encryptedMessage);
            
            // Extract IV from the first 12 bytes
            const iv = encryptedData.slice(0, 12);
            const data = encryptedData.slice(12);

            const decryptedData = await crypto.subtle.decrypt(
                {
                    name: this.algorithm,
                    iv: iv,
                },
                this.key,
                data
            );

            return new TextDecoder().decode(decryptedData);
        } catch (error) {
            console.error('Decryption error:', error);
            throw error;
        }
    }

    // Helper: Convert ArrayBuffer to Base64
    arrayBufferToBase64(buffer) {
        let binary = '';
        const bytes = new Uint8Array(buffer);
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }

    // Helper: Convert Base64 to ArrayBuffer
    base64ToArrayBuffer(base64) {
        const binaryString = atob(base64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        return bytes.buffer;
    }
}

// Export as a singleton
export const encryptionService = new EncryptionService();
