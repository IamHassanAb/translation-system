class ChatApp {
    constructor() {
        this.socket = null;
        this.roomId = 'default-room';
        this.lastStatusResponse = null; // Track the last status to avoid duplicate notifications
        this.statusCheckInterval = null; // Store interval reference
        this.initializeElements();
        this.setupEventListeners();
        this.connectWebSocket();
        this.startAutoStatusCheck();
    }

    initializeElements() {
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatMessages = document.getElementById('chatMessages');
        this.targetLang = document.getElementById('targetLang');
        this.statusButton = document.getElementById('statusButton');
        this.notificationContainer = document.getElementById('notification-container');
    }

    setupEventListeners() {
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
        this.statusButton.addEventListener('click', () => this.getStatus(true)); // Force notification when manually clicked
    }

    // Start automatic status check every second
    startAutoStatusCheck() {
        // Clear any existing interval
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
        }
        
        // Set up the new interval
        this.statusCheckInterval = setInterval(() => {
            this.getStatus(false); // Don't force notification on auto-check
        }, 1000); // Check every 1000ms (1 second)
    }

    // Stop automatic status check
    stopAutoStatusCheck() {
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
            this.statusCheckInterval = null;
        }
    }

    getStatus(forceNotification = false) {
        const protocol = window.location.protocol
        const host = window.location.hostname;
        const port = '8000'; // Match your FastAPI server port
        // Only show checking notification when manually clicked
        if (forceNotification) {
            this.showNotification('info', 'Checking server status...');
        }
        
        fetch(`${protocol}//${host}:${port}/status`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Status Response:', data);
            
            // Determine if we should show a notification
            const shouldNotify = forceNotification || 
                                 !this.lastStatusResponse || 
                                 JSON.stringify(data) !== JSON.stringify(this.lastStatusResponse);
            
            // Update the last status response
            this.lastStatusResponse = data;
            
            // If status changed or notification is forced, show it
            if (shouldNotify) {
                // Determine the notification type based on status
                let type = 'info';
                if (data.status === 'online' || data.status === 'ok') {
                    type = 'success';
                } else if (data.status === 'offline' || data.status === 'error') {
                    type = 'error';
                } else if (data.status === 'warning') {
                    type = 'warning';
                }
                
                // Display the notification with the message from the server
                this.showNotification(type, data.message || `Server status: ${data.status}`);
            }
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error);
            // Only show error notification on forced check or when status changes
            if (forceNotification || (this.lastStatusResponse !== null)) {
                this.showNotification('error', 'Failed to fetch server status');
                this.lastStatusResponse = null;
            }
        });
    }

    // New method to show notification
    showNotification(type, message) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        // Create content container
        const content = document.createElement('div');
        content.className = 'notification-content';
        
        // Create icon
        const icon = document.createElement('div');
        icon.className = 'notification-icon';
        
        // Set icon based on type
        switch(type) {
            case 'success':
                icon.innerHTML = '✓';
                break;
            case 'error':
                icon.innerHTML = '✕';
                break;
            case 'info':
                icon.innerHTML = 'ℹ';
                break;
            case 'warning':
                icon.innerHTML = '!';
                break;
        }
        
        // Create message text
        const messageText = document.createElement('div');
        messageText.className = 'notification-message';
        messageText.textContent = message;
        
        // Create close button
        const closeButton = document.createElement('button');
        closeButton.className = 'notification-close';
        closeButton.innerHTML = '&times;';
        closeButton.addEventListener('click', () => {
            notification.remove();
        });
        
        // Assemble notification
        content.appendChild(icon);
        content.appendChild(messageText);
        notification.appendChild(content);
        notification.appendChild(closeButton);
        
        // Add to container
        this.notificationContainer.appendChild(notification);
        
        // Automatically remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.hostname;
        const port = '8000'; // Match your FastAPI server port
        const wsUrl = `${protocol}//${host}:${port}/ws/chat/${this.roomId}`;

        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = () => {
            console.log('WebSocket connection established');
            this.addSystemMessage('Connected to chat server');
            this.showNotification('success', 'Connected to chat server');
        };

        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Message received:', data);
            this.handleMessage(data);
        };

        this.socket.onclose = () => {
            console.log('WebSocket connection closed');
            this.addSystemMessage('Disconnected from chat server');
            this.showNotification('error', 'Disconnected from chat server');
            // Attempt to reconnect after 5 seconds
            setTimeout(() => this.connectWebSocket(), 5000);
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.addSystemMessage('Connection error occurred');
            this.showNotification('error', 'WebSocket connection error');
        };
    }

    sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || !this.socket || this.socket.readyState !== WebSocket.OPEN) return;

        const data = {
            text: message,
            target_lang: this.targetLang.value
        };

        this.socket.send(JSON.stringify(data));
        this.addMessage(message, 'sent');
        this.messageInput.value = '';
    }

    handleMessage(data) {
        if (data.type === 'system') {
            this.addSystemMessage(data.message);
        } else if (data.type === 'status') {
            this.addStatusMessage(data.message);
            this.showNotification('info', data.message);
        } else {
            this.addMessage(data.text, 'received', data.translation_text);
        }
    }

    addMessage(text, type, translation_text = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = text;

        if (translation_text) {
            const translationDiv = document.createElement('div');
            translationDiv.className = 'translation';
            translationDiv.textContent = translation_text;
            messageDiv.appendChild(translationDiv);
        }

        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    addSystemMessage(message) {
        const systemDiv = document.createElement('div');
        systemDiv.className = 'message system';
        systemDiv.textContent = message;
        this.chatMessages.appendChild(systemDiv);
        this.scrollToBottom();
    }

    addStatusMessage(message) {
        const statusDiv = document.createElement('div');
        statusDiv.className = 'message status';
        statusDiv.textContent = message;
        this.chatMessages.appendChild(statusDiv);
        this.scrollToBottom();
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
}

// Initialize the chat application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});