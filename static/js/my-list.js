// My List Functionality

// Navigation functionality for detail pages
function filterByType(type) {
    window.location.href = '/?filter=' + type;
}

function showNewPopular() {
    window.location.href = '/?view=new-popular';
}

// Initialize My List button states
async function initializeMyListButtons() {
    try {
        const response = await fetch('/api/my-list');
        const data = await response.json();
        
        if (data.success && data.items) {
            const myListIds = new Set(data.items.map(item => item.id || item.imdb_id));
            
            // Update all add buttons in title cards
            document.querySelectorAll('.title-card').forEach(card => {
                const id = card.dataset.id;
                const addButton = card.querySelector('.title-card-add-button');
                
                if (addButton && myListIds.has(id)) {
                    addButton.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z" fill="currentColor"/></svg>';
                    addButton.dataset.added = 'true';
                    addButton.title = 'Remove from My List';
                }
            });
            
            // Also update hero button if it exists
            const heroAddBtn = document.getElementById('heroAddBtn');
            if (heroAddBtn) {
                const heroData = document.querySelector('[data-hero="true"]');
                if (heroData) {
                    const heroId = heroData.dataset.id;
                    if (myListIds.has(heroId)) {
                        heroAddBtn.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z" fill="currentColor"/></svg>';
                        heroAddBtn.dataset.added = 'true';
                        heroAddBtn.title = 'Remove from My List';
                    }
                }
            }
        }
    } catch (error) {
        console.error('Failed to initialize My List buttons:', error);
    }
}

function showMyList() {
    // Fetch My List items from API
    fetch('/api/my-list')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.items && data.items.length > 0) {
                openMyListModal(data.items);
            } else {
                // No items in My List
                if (typeof homeflixApp !== 'undefined') {
                    homeflixApp.showNotification('Your list is empty! Click the + button on any movie or show to add it to your list.', 'info');
                }
            }
        })
        .catch(error => {
            console.error('Error fetching My List:', error);
            if (typeof homeflixApp !== 'undefined') {
                homeflixApp.showNotification('Failed to load My List', 'error');
            }
        });
}

function openMyListModal(items) {
    // Limit to 5 items for preview
    const maxItems = 5;
    const previewItems = items.slice(0, maxItems);
    const hasMore = items.length > maxItems;
    
    // Create modal overlay
    const modal = document.createElement('div');
    modal.className = 'my-list-modal';
    modal.innerHTML = `
        <div class="my-list-modal-content">
            <div class="my-list-modal-header">
                <h2>My List</h2>
                <button class="my-list-modal-close" onclick="closeMyListModal()">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" fill="currentColor"/>
                    </svg>
                </button>
            </div>
            <div class="my-list-modal-body">
                <div class="my-list-grid">
                    ${previewItems.map(item => `
                        <div class="my-list-item" data-type="${item.type}" data-id="${item.id || item.imdb_id}" data-tmdb-id="${item.tmdb_id}">
                            <div class="my-list-item-poster">
                                ${item.poster_url ? `<img src="${item.poster_url}" alt="${item.title}" loading="lazy">` : `<div class="placeholder-image"><span>${item.title.charAt(0)}</span></div>`}
                                <div class="my-list-item-overlay">
                                    <button class="btn btn-primary" onclick="homeflixApp.playTitle('${item.type}', '${item.id || item.imdb_id}')">
                                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M8 5v14l11-7z" fill="currentColor"/>
                                        </svg>
                                        Play
                                    </button>
                                    <button class="btn btn-icon" onclick="removeFromMyListModal('${item.type}', '${item.id || item.imdb_id}', '${item.title}')" title="Remove from My List">
                                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z" fill="currentColor"/>
                                        </svg>
                                    </button>
                                </div>
                            </div>
                            <div class="my-list-item-info">
                                <h3>${item.title}</h3>
                                <p class="my-list-item-type">${item.type === 'movie' ? 'Movie' : 'TV Show'}</p>
                            </div>
                        </div>
                    `).join('')}
                </div>
                ${hasMore ? `
                    <div class="my-list-show-more">
                        <button onclick="goToMyListPage()">
                            Show More (${items.length - maxItems} more items)
                        </button>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add animation
    setTimeout(() => {
        modal.classList.add('active');
    }, 10);
    
    // Close on outside click
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeMyListModal();
        }
    });
}

function closeMyListModal() {
    const modal = document.querySelector('.my-list-modal');
    if (modal) {
        modal.classList.remove('active');
        setTimeout(() => {
            modal.remove();
        }, 300);
    }
}

function goToMyListPage() {
    closeMyListModal();
    // Scroll to the My List section on the homepage
    const myListSection = document.querySelector('#my-list-slider');
    if (myListSection) {
        const section = myListSection.closest('.content-row');
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
        if (typeof homeflixApp !== 'undefined') {
            homeflixApp.showNotification('Showing your full list below', 'info');
        }
    } else {
        // If there's no My List section visible, reload to show it
        if (typeof homeflixApp !== 'undefined') {
            homeflixApp.showNotification('Loading your full list...', 'info');
        }
        setTimeout(() => {
            window.location.href = '/#my-list';
        }, 500);
    }
}

function removeFromMyListModal(type, id, title) {
    fetch('/api/my-list', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            action: 'remove',
            type: type,
            id: id,
            title: title
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (typeof homeflixApp !== 'undefined') {
                homeflixApp.showNotification(`Removed "${title}" from My List`, 'info');
            }
            
            // Remove the item from modal
            const itemElement = document.querySelector(`.my-list-item[data-id="${id}"]`);
            if (itemElement) {
                itemElement.style.animation = 'fadeOut 0.3s ease';
                setTimeout(() => {
                    itemElement.remove();
                    
                    // Check if modal is now empty
                    const remainingItems = document.querySelectorAll('.my-list-item');
                    if (remainingItems.length === 0) {
                        closeMyListModal();
                        if (typeof homeflixApp !== 'undefined') {
                            homeflixApp.showNotification('Your list is now empty', 'info');
                        }
                    }
                }, 300);
            }
        }
    })
    .catch(error => {
        if (typeof homeflixApp !== 'undefined') {
            homeflixApp.showNotification('Failed to remove from My List', 'error');
        }
    });
}

// Add to My List functionality for detail pages
async function addToMyList(type, id, tmdbId, title, button) {
    try {
        const isAdded = button.getAttribute('data-added') === 'true';
        const action = isAdded ? 'remove' : 'add';
        
        const response = await fetch('/api/my-list', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                action: action,
                type: type,
                id: id,
                tmdb_id: tmdbId,
                title: title
            })
        });

        if (response.ok) {
            if (action === 'add') {
                button.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z" fill="currentColor"/></svg> My List';
                button.setAttribute('data-added', 'true');
            } else {
                button.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" fill="currentColor"/></svg> My List';
                button.setAttribute('data-added', 'false');
            }
        }
    } catch (error) {
        console.error('Failed to update My List:', error);
    }
}

// Initialize My List buttons on detail pages
function initializeDetailPageButtons() {
    console.log('Initializing detail page My List buttons...');
    const myListButtons = document.querySelectorAll('.btn-add-list[data-type]');
    console.log('Found buttons:', myListButtons.length);
    
    myListButtons.forEach((button, index) => {
        console.log(`Setting up button ${index}:`, {
            type: button.getAttribute('data-type'),
            id: button.getAttribute('data-id'),
            title: button.getAttribute('data-title')
        });
        
        // Remove any existing click listeners by cloning
        const newButton = button.cloneNode(true);
        button.parentNode.replaceChild(newButton, button);
        
        // Add new click listener
        newButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            console.log('My List button clicked!');
            
            const type = this.getAttribute('data-type');
            const id = this.getAttribute('data-id');
            const tmdbId = this.getAttribute('data-tmdb-id');
            const title = this.getAttribute('data-title');
            
            console.log('Adding to list:', { type, id, tmdbId, title });
            
            addToMyList(type, id, tmdbId, title, this);
        });
    });
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDetailPageButtons);
} else {
    initializeDetailPageButtons();
}
