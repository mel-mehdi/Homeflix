// Title Card Interactions

function setupTitleCardInteractions() {
    // Use event delegation to handle clicks on dynamically added cards
    document.body.addEventListener('click', function(e) {
        // Find the closest title card
        const card = e.target.closest('.title-card');
        if (!card) return;

        // Play button click
        if (e.target.closest('.title-card-play-button')) {
            e.stopPropagation();
            const type = card.dataset.type;
            const id = card.dataset.id;
            if (type === 'series') {
                window.location.href = `/series/${id}`;
            } else if (type === 'movie') {
                window.location.href = `/movie/${id}`;
            } else {
                window.location.href = `/watch/${type}/${id}`;
            }
            return;
        }

        // Add to List button
        if (e.target.closest('.title-card-add-button')) {
            e.stopPropagation();
            const addButton = e.target.closest('.title-card-add-button');
            const title = card.dataset.title;
            addToMyList(title, addButton);
            return;
        }

        // Like button
        if (e.target.closest('.title-card-like-button')) {
            e.stopPropagation();
            const likeButton = e.target.closest('.title-card-like-button');
            const title = card.dataset.title;
            toggleLike(title, likeButton);
            return;
        }

        // More info button
        if (e.target.closest('.title-card-expand-button')) {
            e.stopPropagation();
            const title = card.dataset.title;
            const type = card.dataset.type;
            showTitleInfo(title, type);
            return;
        }

        // Card click (if not clicking any button)
        if (!e.target.closest('.title-card-play-button, .title-card-add-button, .title-card-like-button, .title-card-expand-button')) {
            const type = card.dataset.type;
            const id = card.dataset.id;
            if (type === 'series') {
                window.location.href = `/series/${id}`;
            } else if (type === 'movie') {
                window.location.href = `/movie/${id}`;
            }
        }
    });

    // Hover effects using event delegation
    document.body.addEventListener('mouseenter', function(e) {
        const card = e.target.closest('.title-card');
        if (card) {
            card.style.transform = 'scale(1.05)';
            card.style.zIndex = '10';
        }
    }, true);

    document.body.addEventListener('mouseleave', function(e) {
        const card = e.target.closest('.title-card');
        if (card) {
            card.style.transform = 'scale(1)';
            card.style.zIndex = '1';
        }
    }, true);
}

// Button functionality functions
async function addToMyList(...args) {
    let type, id, tmdbId, title, button;
    
    if (args.length === 2) {
        // Called from title card: addToMyList(title, button)
        [title, button] = args;
        const card = button.closest('.title-card');
        type = card.dataset.type;
        id = card.dataset.id;
        tmdbId = card.dataset.tmdbId;
    } else if (args.length === 5) {
        // Called from details page: addToMyList(type, id, tmdbId, title, button)
        [type, id, tmdbId, title, button] = args;
    } else {
        console.error('Invalid arguments for addToMyList');
        return;
    }
    
    // Toggle between add and remove
    const isAdded = button.dataset.added === 'true';
    
    try {
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

        const data = await response.json();
        
        if (data.success) {
            // Update UI
            if (isAdded) {
                button.innerHTML = `
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" fill="currentColor"/>
                    </svg>
                `;
                button.dataset.added = 'false';
                button.title = 'Add to My List';
                if (typeof homeflixApp !== 'undefined') {
                    homeflixApp.showNotification(`"${title}" removed from My List`, 'success');
                }
            } else {
                button.innerHTML = `
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z" fill="currentColor"/>
                    </svg>
                `;
                button.dataset.added = 'true';
                button.title = 'Remove from My List';
                if (typeof homeflixApp !== 'undefined') {
                    homeflixApp.showNotification(`"${title}" added to My List`, 'success');
                }
            }
        } else {
            throw new Error(data.message || 'Failed to update My List');
        }
    } catch (error) {
        console.error('Error updating My List:', error);
        if (typeof homeflixApp !== 'undefined') {
            homeflixApp.showNotification('Failed to update My List', 'error');
        }
    }
}

function toggleLike(title, button) {
    // Toggle between like and dislike
    const isLiked = button.dataset.liked === 'true';
    
    if (isLiked) {
        button.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z" fill="currentColor"/>
            </svg>
        `;
        button.dataset.liked = 'false';
        button.style.backgroundColor = 'rgba(42,42,42,0.6)';
        if (typeof homeflixApp !== 'undefined') {
            homeflixApp.showNotification(`You unliked "${title}"`, 'info');
        }
    } else {
        button.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M1 9h4v12H1V9zm22 11c0 1.1-.9 2-2 2h-6.31l.95 4.57.03.32c0 .41-.17.79-.44 1.06L14.17 23 7.59 16.41C7.22 16.05 7 15.55 7 15V5c0-1.1.9-2 2-2h9c.83 0 1.54.5 1.84 1.22l3.02 7.05c.09.23.14.47.14.73v2z" fill="currentColor"/>
            </svg>
        `;
        button.dataset.liked = 'true';
        button.style.backgroundColor = '#e50914';
        if (typeof homeflixApp !== 'undefined') {
            homeflixApp.showNotification(`You liked "${title}"`, 'success');
        }
    }
}

function showTitleInfo(title, type) {
    if (typeof homeflixApp !== 'undefined') {
        homeflixApp.showNotification(`More info feature for "${title}" is coming soon!`, 'info');
    }
}

// Create Netflix-style title card
function createTitleCard(item, type) {
    const card = document.createElement('div');
    card.className = 'title-card';
    card.dataset.title = item.title;
    card.dataset.type = type;
    card.dataset.id = item.imdb_id;
    card.dataset.tmdbId = item.tmdb_id;
    
    const quality = type === 'movie' ? item.quality : 'Series';
    const imageHtml = item.poster_url ? 
        `<img src="${item.poster_url}" alt="${item.title}" loading="lazy">` :
        `<div class="placeholder-image"><span>${item.title.charAt(0)}</span></div>`;
    
    card.innerHTML = `
        <div class="title-card-image">
            ${imageHtml}
        </div>
        <div class="title-card-metadata">
            <div class="metadata-top">
                <div class="title-card-play-button">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M8 5v14l11-7z" fill="currentColor"/>
                    </svg>
                </div>
                <div class="title-card-add-button">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" fill="currentColor"/>
                    </svg>
                </div>
                <div class="title-card-like-button">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z" fill="currentColor"/>
                    </svg>
                </div>
                <div class="title-card-expand-button">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M16.59 8.59L12 13.17 7.41 8.59 6 10l6 6 6-6z" fill="currentColor"/>
                    </svg>
                </div>
            </div>
            <div class="metadata-bottom">
                <div class="title-card-title">${item.title}</div>
                <div class="title-card-genres">
                    <span class="genre-tag">${quality}</span>
                </div>
            </div>
        </div>
    `;
    
    // Event listeners are now handled by netflix.js
    return card;
}
