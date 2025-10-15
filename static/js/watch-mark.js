// Watch Mark Feature - Mark movies and episodes as watched/unwatched
const watchMark = {
    // Toggle watched status
    toggleWatched: async function(type, id, tmdbId, title, button, season = null, episode = null) {
        if (!id) {
            console.error('Missing required parameters for toggleWatched');
            return;
        }

        try {
            // Check current state
            const isWatched = button.dataset.watched === 'true';
            
            // Prepare request data
            const requestData = {
                type: type,
                id: id,
                imdb_id: id,
                tmdb_id: tmdbId,
                title: title
            };
            
            // Add episode info for series
            if (type === 'series' && season !== null && episode !== null) {
                requestData.season = season;
                requestData.episode = episode;
            }
            
            // Make API call to mark/unmark as watched
            const endpoint = isWatched ? '/api/unmark_watched' : '/api/mark_watched';
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                throw new Error('Failed to update watched status');
            }

            const data = await response.json();
            
            // Update button state based on response
            if (data.success) {
                if (data.is_watched) {
                    // Marked as watched
                    button.innerHTML = `
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                            <path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z"/>
                        </svg>
                    `;
                    button.dataset.watched = 'true';
                    button.classList.add('watched');
                    button.title = 'Mark as Unwatched';
                    
                    // Add watched overlay to title card if exists
                    const titleCard = button.closest('.title-card');
                    if (titleCard) {
                        this.addWatchedOverlay(titleCard);
                    }
                    
                    // Show notification
                    if (type === 'series' && season && episode) {
                        this.showNotification(`Marked S${season}E${episode} as watched`, 'success');
                    } else {
                        this.showNotification(`Marked "${title}" as watched`, 'success');
                    }
                } else {
                    // Unmarked as watched
                    button.innerHTML = `
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z" stroke="currentColor" stroke-width="2"/>
                        </svg>
                    `;
                    button.dataset.watched = 'false';
                    button.classList.remove('watched');
                    button.title = 'Mark as Watched';
                    
                    // Remove watched overlay from title card if exists
                    const titleCard = button.closest('.title-card');
                    if (titleCard) {
                        this.removeWatchedOverlay(titleCard);
                    }
                    
                    // Show notification
                    if (type === 'series' && season && episode) {
                        this.showNotification(`Unmarked S${season}E${episode} as watched`, 'info');
                    } else {
                        this.showNotification(`Unmarked "${title}" as watched`, 'info');
                    }
                }
            }
        } catch (error) {
            console.error('Error toggling watched status:', error);
            this.showNotification('Failed to update watched status', 'error');
        }
    },

    // Check if item is watched and update UI
    checkWatchedStatus: async function(type, id, season = null, episode = null, button) {
        try {
            let url = `/api/watched_status/${type}/${id}`;
            
            // Add episode params for series
            if (type === 'series' && season !== null && episode !== null) {
                url += `?season=${season}&episode=${episode}`;
            }
            
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error('Failed to fetch watched status');
            }
            
            const data = await response.json();
            
            if (data.success && data.is_watched) {
                // Update button to watched state
                button.innerHTML = `
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                        <path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z"/>
                    </svg>
                `;
                button.dataset.watched = 'true';
                button.classList.add('watched');
                button.title = 'Mark as Unwatched';
                
                // Add watched overlay to title card if exists
                const titleCard = button.closest('.title-card');
                if (titleCard) {
                    this.addWatchedOverlay(titleCard);
                }
            }
        } catch (error) {
            console.error('Error checking watched status:', error);
        }
    },

    // Add watched overlay to title card
    addWatchedOverlay: function(titleCard) {
        // Check if overlay already exists
        if (titleCard.querySelector('.watched-overlay')) {
            return;
        }
        
        const overlay = document.createElement('div');
        overlay.className = 'watched-overlay';
        overlay.innerHTML = `
            <div class="watched-badge">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                    <path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z"/>
                </svg>
                <span>Watched</span>
            </div>
        `;
        
        const posterContainer = titleCard.querySelector('.title-card-poster') || titleCard;
        posterContainer.style.position = 'relative';
        posterContainer.appendChild(overlay);
    },

    // Remove watched overlay from title card
    removeWatchedOverlay: function(titleCard) {
        const overlay = titleCard.querySelector('.watched-overlay');
        if (overlay) {
            overlay.remove();
        }
    },

    // Show notification
    showNotification: function(message, type = 'info') {
        // Remove existing notifications
        const existing = document.querySelector('.watch-mark-notification');
        if (existing) {
            existing.remove();
        }

        // Create notification element
        const notification = document.createElement('div');
        notification.className = `watch-mark-notification watch-mark-notification-${type}`;
        
        // Icon based on type
        let icon = '';
        if (type === 'success') {
            icon = `<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z"/></svg>`;
        } else if (type === 'error') {
            icon = `<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>`;
        } else {
            icon = `<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>`;
        }
        
        notification.innerHTML = `
            <div class="notification-content">
                ${icon}
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);

        // Show with animation
        setTimeout(() => notification.classList.add('show'), 10);

        // Auto remove after 3 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    },

    // Initialize watched status for all title cards on page
    initializeWatchedCards: function() {
        const titleCards = document.querySelectorAll('.title-card');
        
        titleCards.forEach(card => {
            const watchButton = card.querySelector('.watch-mark-btn');
            if (watchButton && watchButton.dataset.watched === 'true') {
                this.addWatchedOverlay(card);
            }
        });
    },

    // Mark entire season as watched
    markSeasonAsWatched: async function(imdbId, seasonNumber, episodes) {
        const totalEpisodes = episodes.length;
        let completed = 0;
        
        for (const episode of episodes) {
            try {
                const response = await fetch('/api/mark_watched', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        type: 'series',
                        id: imdbId,
                        title: episode.title || `Episode ${episode.episode_number}`,
                        season: seasonNumber,
                        episode: episode.episode_number
                    })
                });
                
                if (response.ok) {
                    completed++;
                }
            } catch (error) {
                console.error(`Failed to mark episode ${episode.episode_number}:`, error);
            }
        }
        
        this.showNotification(`Marked ${completed}/${totalEpisodes} episodes as watched`, 'success');
        
        // Reload page to update UI
        setTimeout(() => {
            window.location.reload();
        }, 1500);
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    watchMark.initializeWatchedCards();
});

// Make globally accessible
window.watchMark = watchMark;
