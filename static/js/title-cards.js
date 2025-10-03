// Title Card Interactions

function setupTitleCardInteractions() {
    const titleCards = document.querySelectorAll('.title-card');
    
    titleCards.forEach(card => {
        // Play button click
        const playButton = card.querySelector('.title-card-play-button');
        if (playButton) {
            playButton.addEventListener('click', function(e) {
                e.stopPropagation();
                const type = card.dataset.type;
                const id = card.dataset.id;
                // For series, go to details page, for movies play directly
                if (type === 'series') {
                    window.location.href = `/series/${id}`;
                } else {
                    window.location.href = `/watch/${type}/${id}`;
                }
            });
        }

        // Add to List button
        const addButton = card.querySelector('.title-card-add-button');
        if (addButton) {
            addButton.addEventListener('click', function(e) {
                e.stopPropagation();
                const title = card.dataset.title;
                addToMyList(title, addButton);
            });
        }

        // Like button
        const likeButton = card.querySelector('.title-card-like-button');
        if (likeButton) {
            likeButton.addEventListener('click', function(e) {
                e.stopPropagation();
                const title = card.dataset.title;
                toggleLike(title, likeButton);
            });
        }

        // More info button
        const expandButton = card.querySelector('.title-card-expand-button');
        if (expandButton) {
            expandButton.addEventListener('click', function(e) {
                e.stopPropagation();
                const title = card.dataset.title;
                const type = card.dataset.type;
                showTitleInfo(title, type);
            });
        }

        // Card click
        card.addEventListener('click', function() {
            const type = card.dataset.type;
            const id = card.dataset.id;
            // For series, go to details page first
            if (type === 'series') {
                window.location.href = `/series/${id}`;
            } else {
                window.location.href = `/watch/${type}/${id}`;
            }
        });

        // Hover effects
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05)';
            this.style.zIndex = '10';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
            this.style.zIndex = '1';
        });
    });
}

// Button functionality functions
function addToMyList(title, button) {
    // Toggle between add and remove
    const isAdded = button.dataset.added === 'true';
    
    if (isAdded) {
        button.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" fill="currentColor"/>
            </svg>
        `;
        button.dataset.added = 'false';
        button.style.backgroundColor = 'rgba(42,42,42,0.6)';
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
        button.style.backgroundColor = '#46d369';
        if (typeof homeflixApp !== 'undefined') {
            homeflixApp.showNotification(`"${title}" added to My List`, 'success');
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
