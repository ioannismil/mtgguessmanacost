// Toast Notification System
// Provides modern, non-blocking notifications to replace browser alerts

// Create toast container on page load
document.addEventListener('DOMContentLoaded', () => {
    if (!document.getElementById('toast-container')) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    // Modal will be created on-demand by showUsernameModal()
});

// Toast notification manager
let toastId = 0;

/**
 * Show a toast notification
 * @param {string} message - Main message to display
 * @param {string} type - Toast type: 'success', 'error', 'info', 'warning'
 * @param {number} duration - How long to show (ms), default 4000
 * @param {string} description - Optional sub-message
 */
function showToast(message, type = 'info', duration = 4000, description = '') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const id = `toast-${toastId++}`;
    const toast = document.createElement('div');
    toast.id = id;
    toast.className = `toast ${type}`;

    // Icon based on type
    const icons = {
        success: '✅',
        error: '❌',
        info: 'ℹ️',
        warning: '⚠️'
    };

    toast.innerHTML = `
    <div class="toast-icon">${icons[type] || icons.info}</div>
    <div class="toast-content">
      <div class="toast-message">${message}</div>
      ${description ? `<div class="toast-description">${description}</div>` : ''}
    </div>
    <div class="toast-progress" style="width: 100%"></div>
  `;

    // Add to container
    container.appendChild(toast);

    // Click to dismiss
    toast.addEventListener('click', () => removeToast(id));

    // Animate progress bar
    const progressBar = toast.querySelector('.toast-progress');
    setTimeout(() => {
        progressBar.style.transition = `width ${duration}ms linear`;
        progressBar.style.width = '0%';
    }, 10);

    // Auto-dismiss after duration
    setTimeout(() => removeToast(id), duration);

    return id;
}

/**
 * Remove a toast notification
 */
function removeToast(id) {
    const toast = document.getElementById(id);
    if (!toast) return;

    toast.classList.add('removing');
    setTimeout(() => toast.remove(), 300); // Match animation duration
}

// Convenience functions
function showSuccess(message, description = '') {
    return showToast(message, 'success', 4000, description);
}

function showError(message, description = '') {
    return showToast(message, 'error', 5000, description);
}

function showInfo(message, description = '') {
    return showToast(message, 'info', 4000, description);
}

function showWarning(message, description = '') {
    return showToast(message, 'warning', 4500, description);
}

// Username Modal Functions
let usernameModalResolver = null;

/**
 * Show username input modal
 * @returns {Promise<string>} - Resolves with username or "Anonymous"
 */
function showUsernameModal() {
    return new Promise((resolve) => {
        // Ensure modal exists
        let modal = document.getElementById('username-modal');
        if (!modal) {
            // Create modal if it doesn't exist yet
            modal = document.createElement('div');
            modal.id = 'username-modal';
            modal.className = 'username-modal-overlay';
            modal.innerHTML = `
                <div class="username-modal-content" onclick="event.stopPropagation()">
                    <h3>🏆 Leaderboard Submission</h3>
                    <p>Enter your name (or leave blank for Anonymous)</p>
                    <input 
                        type="text" 
                        id="username-input" 
                        class="username-modal-input" 
                        maxlength="50" 
                        placeholder="Your name..."
                    />
                    <div class="username-modal-actions">
                        <button class="username-modal-btn cancel" id="cancel-username-btn">Cancel</button>
                        <button class="username-modal-btn submit" id="submit-username-btn">Submit Score</button>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);

            // Close modal when clicking outside
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    closeUsernameModal();
                }
            });
        }

        const input = document.getElementById('username-input');
        const submitBtn = document.getElementById('submit-username-btn');
        const cancelBtn = document.getElementById('cancel-username-btn');

        // Store resolver
        usernameModalResolver = resolve;

        // Reset and show modal
        input.value = '';
        modal.classList.add('show');

        // Focus input after animation
        setTimeout(() => input.focus(), 100);

        // Handle submit
        const handleSubmit = () => {
            const username = input.value.trim() || 'Anonymous';
            closeUsernameModal();
            if (usernameModalResolver) {
                usernameModalResolver(username);
                usernameModalResolver = null;
            }
        };

        // Handle cancel
        const handleCancel = () => {
            closeUsernameModal();
        };

        // Remove old listeners and add new ones
        submitBtn.onclick = handleSubmit;
        cancelBtn.onclick = handleCancel;

        // Handle Enter and Escape keys
        const keyHandler = (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleSubmit();
            } else if (e.key === 'Escape') {
                e.preventDefault();
                handleCancel();
            }
        };

        // Remove old key listener and add new one
        input.removeEventListener('keydown', keyHandler);
        input.addEventListener('keydown', keyHandler);
    });
}

/**
 * Close username modal
 */
function closeUsernameModal() {
    const modal = document.getElementById('username-modal');
    modal.classList.remove('show');

    // If modal was cancelled, resolve with Anonymous
    if (usernameModalResolver) {
        usernameModalResolver('Anonymous');
        usernameModalResolver = null;
    }
}
