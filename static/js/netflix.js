// Netflix-style Myflix functionality
const homeflixApp = {
    // Play title (movie or series)
    playTitle: function(type, id) {
        if (!id) {
            console.error('No ID provided for playTitle');
            return;
        }
        
        if (type === 'series') {
            // For TV series, go to series details page to see seasons and episodes
            window.location.href = `/series/${id}`;
        } else if (type === 'movie') {
            // For movies, go to movie details page (same as series)
            window.location.href = `/movie/${id}`;
        } else {
            console.error('Unknown type:', type);
        }
    },

    // Toggle My List
    toggleMyList: async function(type, id, tmdbId, title, button) {
        if (!id || !tmdbId) {
            console.error('Missing required parameters for toggleMyList');
            return;
        }

        try {
            // Check current state
            const isAdded = button.dataset.added === 'true';
            
            // Make API call to add/remove from list
            const response = await fetch('/api/my-list', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: isAdded ? 'remove' : 'add',
                    type: type,
                    id: id,
                    tmdb_id: tmdbId,
                    title: title
                })
            });

            if (!response.ok) {
                throw new Error('Failed to update My List');
            }

            const data = await response.json();
            
            // Update button state
            if (data.added || !isAdded) {
                // Added to list
                button.innerHTML = `
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z" fill="currentColor"/>
                    </svg>
                `;
                button.dataset.added = 'true';
                button.title = 'Remove from My List';
                this.showNotification(`Added "${title}" to My List`, 'success');
            } else {
                // Removed from list
                button.innerHTML = `
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" fill="currentColor"/>
                    </svg>
                `;
                button.dataset.added = 'false';
                button.title = 'Add to My List';
                this.showNotification(`Removed "${title}" from My List`, 'info');
            }
        } catch (error) {
            console.error('Error toggling My List:', error);
            // Fallback to simple toggle for now
            const isAdded = button.dataset.added === 'true';
            
            if (isAdded) {
                button.innerHTML = `
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" fill="currentColor"/>
                    </svg>
                `;
                button.dataset.added = 'false';
                button.title = 'Add to My List';
            } else {
                button.innerHTML = `
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z" fill="currentColor"/>
                    </svg>
                `;
                button.dataset.added = 'true';
                button.title = 'Remove from My List';
            }
        }
    },

    // Toggle Like
    toggleLike: async function(type, id, title, button) {
        if (!id) {
            console.error('Missing required parameters for toggleLike');
            return;
        }

        try {
            // Check current state
            const isLiked = button.dataset.liked === 'true';
            
            // Make API call to like/unlike
            const response = await fetch('/api/like', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: isLiked ? 'unlike' : 'like',
                    type: type,
                    id: id,
                    title: title
                })
            });

            if (!response.ok) {
                throw new Error('Failed to update like status');
            }

            const data = await response.json();
            
            // Update button state
            if (data.liked || !isLiked) {
                // Liked
                button.innerHTML = `
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z" fill="currentColor"/>
                    </svg>
                `;
                button.dataset.liked = 'true';
                button.title = 'Unlike';
                button.style.opacity = '1';
                this.showNotification(`You liked "${title}"`, 'success');
            } else {
                // Unliked
                button.innerHTML = `
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z" fill="currentColor"/>
                    </svg>
                `;
                button.dataset.liked = 'false';
                button.title = 'Like';
                button.style.opacity = '0.7';
                this.showNotification(`You unliked "${title}"`, 'info');
            }
        } catch (error) {
            console.error('Error toggling like:', error);
            // Fallback to simple toggle
            const isLiked = button.dataset.liked === 'true';
            
            if (isLiked) {
                button.innerHTML = `
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z" fill="currentColor"/>
                    </svg>
                `;
                button.dataset.liked = 'false';
                button.title = 'Like';
                button.style.opacity = '0.7';
            } else {
                button.innerHTML = `
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z" fill="currentColor"/>
                    </svg>
                `;
                button.dataset.liked = 'true';
                button.title = 'Unlike';
                button.style.opacity = '1';
            }
        }
    },

    // Show notification
    showNotification: function(message, type = 'info') {
        // Remove existing notifications
        const existing = document.querySelector('.homeflix-notification');
        if (existing) {
            existing.remove();
        }

        // Create notification element
        const notification = document.createElement('div');
        notification.className = `homeflix-notification homeflix-notification-${type}`;
        notification.textContent = message;
        
        // Add styles
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: rgba(0, 0, 0, 0.95);
            color: white;
            padding: 16px 24px;
            border-radius: 4px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
            z-index: 10000;
            font-size: 14px;
            font-weight: 500;
            animation: slideIn 0.3s ease-out;
            border-left: 4px solid ${type === 'success' ? '#46d369' : type === 'error' ? '#e50914' : '#fff'};
        `;

        // Add animation styles if not already present
        if (!document.getElementById('notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                @keyframes slideIn {
                    from {
                        transform: translateX(400px);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
                @keyframes slideOut {
                    from {
                        transform: translateX(0);
                        opacity: 1;
                    }
                    to {
                        transform: translateX(400px);
                        opacity: 0;
                    }
                }
            `;
            document.head.appendChild(style);
        }

        document.body.appendChild(notification);

        // Auto remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Myflix app initialized');
});
