// Hero Banner functionality
let currentBackdropIndex = 0;
let backdropUrls = [];
let heroSeries = [];

// Preload images cache
const preloadedImages = new Map();

// Preload backdrop images for faster transitions
function preloadBackdropImages() {
    if (!backdropUrls || backdropUrls.length === 0) return;
    backdropUrls.forEach((url, index) => {
        const img = new Image();
        img.src = url;
        preloadedImages.set(url, img);
    });
}

// Initialize hero banner data
function initializeHeroBannerData(backdrops, series) {
    backdropUrls = backdrops || [];
    heroSeries = series || [];
    
    // Preload images on page load
    if (backdropUrls && backdropUrls.length > 0) {
        preloadBackdropImages();
    }

    // Change background AND hero content every 8 seconds
    if (backdropUrls && backdropUrls.length > 1 && heroSeries && heroSeries.length > 1) {
        setInterval(() => {
            currentBackdropIndex = (currentBackdropIndex + 1) % Math.min(backdropUrls.length, heroSeries.length);
            updateHeroContent(currentBackdropIndex);
        }, 8000);
    }
}

// Update hero banner content to match the current featured series
function updateHeroContent(index) {
    const heroBanner = document.querySelector('.hero-banner');
    const heroInfo = document.querySelector('.hero-info');
    const series = heroSeries[index];
    
    if (!heroBanner || !series || !heroInfo) return;
    
    // Add fade-out effect
    heroInfo.style.opacity = '0';
    heroInfo.style.transition = 'opacity 0.3s ease-in-out';
    
    // Wait for fade-out to complete before updating content
    setTimeout(() => {
        // Update background with preloaded image for instant display
        if (backdropUrls[index]) {
            const imageUrl = backdropUrls[index];
            const preloadedImg = preloadedImages.get(imageUrl);
            
            // Check if image is already loaded
            if (preloadedImg && preloadedImg.complete) {
                // Image is ready, apply immediately
                heroBanner.style.backgroundImage = `url('${imageUrl}')`;
                heroBanner.style.backgroundSize = 'cover';
                heroBanner.style.backgroundPosition = 'center';
            } else {
                // Fallback: set image and wait for it to load
                heroBanner.style.backgroundImage = `url('${imageUrl}')`;
                heroBanner.style.backgroundSize = 'cover';
                heroBanner.style.backgroundPosition = 'center';
            }
        }
        
        // Update maturity rating badge
        const maturityBadge = heroBanner.querySelector('.hero-maturity-badge span');
        if (maturityBadge) {
            maturityBadge.textContent = series.rating || 'TV-MA';
        }
        
        // Update hidden data attributes for buttons
        const heroCard = heroBanner.querySelector('[data-hero="true"]');
        if (heroCard) {
            heroCard.dataset.type = 'series';
            heroCard.dataset.id = series.imdb_id;
            heroCard.dataset.tmdbId = series.tmdb_id;
        }
        
        // Update title
        const heroTitle = heroBanner.querySelector('.hero-title');
        if (heroTitle) {
            heroTitle.textContent = series.title;
        }
        
        // Update badges (NEW, TOP 10, etc)
        const badgeTop10 = heroBanner.querySelector('.badge-top10');
        if (badgeTop10) {
            const position = (index + 1);
            badgeTop10.textContent = `#${position} in TV Shows Today`;
        }
        
        // Update match score and metadata
        const matchScore = heroBanner.querySelector('.hero-match');
        if (matchScore) {
            // Generate random match score between 85-99 for variety
            const score = 85 + Math.floor(Math.random() * 15);
            matchScore.textContent = `${score}% Match`;
        }
        
        const heroYear = heroBanner.querySelector('.hero-year');
        if (heroYear) {
            heroYear.textContent = series.year || '2024';
        }
        
        const heroRatingBadge = heroBanner.querySelector('.hero-rating-badge');
        if (heroRatingBadge) {
            heroRatingBadge.textContent = series.rating || 'TV-MA';
        }
        
        const heroSeasons = heroBanner.querySelector('.hero-seasons');
        if (heroSeasons) {
            const seasons = series.number_of_seasons || '3';
            heroSeasons.textContent = `${seasons} Season${seasons !== 1 ? 's' : ''}`;
        }
        
        // Update overview
        const heroOverview = heroBanner.querySelector('.hero-overview');
        if (heroOverview) {
            const overview = series.overview || 'Unlimited movies, TV shows, and more.';
            heroOverview.textContent = overview.length > 180 ? overview.substring(0, 180) + '...' : overview;
        }
        
        // Update expanded info if it exists
        const expandedInfo = heroBanner.querySelector('.hero-expanded-info');
        if (expandedInfo) {
            const fullSynopsis = expandedInfo.querySelector('.hero-synopsis-full p');
            if (fullSynopsis) {
                fullSynopsis.textContent = series.overview || 'Full description of the show goes here with all the details about plot, characters, and what makes it worth watching.';
            }
            
            const genresValue = expandedInfo.querySelector('.detail-item:nth-child(2) .detail-value');
            if (genresValue && series.genres) {
                genresValue.textContent = series.genres.join(', ');
            }
        }
        
        // Re-initialize hero banner buttons with new data
        reinitializeHeroButtons();
        
        // Preload next image for even smoother transition
        const nextIndex = (index + 1) % Math.min(backdropUrls.length, heroSeries.length);
        if (backdropUrls[nextIndex] && !preloadedImages.has(backdropUrls[nextIndex])) {
            const nextImg = new Image();
            nextImg.src = backdropUrls[nextIndex];
            preloadedImages.set(backdropUrls[nextIndex], nextImg);
        }
        
        // Fade content back in
        heroInfo.style.opacity = '1';
    }, 300); // Match this with the fade-out duration
}

// Reinitialize hero buttons after content update
async function reinitializeHeroButtons() {
    const heroPlayBtn = document.getElementById('heroPlayBtn');
    const heroAddBtn = document.getElementById('heroAddBtn');
    const heroLikeBtn = document.getElementById('heroLikeBtn');
    const heroCard = document.querySelector('[data-hero="true"]');
    
    if (!heroCard) return;
    
    const type = heroCard.dataset.type;
    const id = heroCard.dataset.id;
    const tmdbId = heroCard.dataset.tmdbId;
    const title = document.querySelector('.hero-title')?.textContent;
    
    if (!title) return;
    
    // Remove old event listeners by cloning and replacing
    if (heroPlayBtn && heroPlayBtn.parentNode) {
        const newPlayBtn = heroPlayBtn.cloneNode(true);
        heroPlayBtn.parentNode.replaceChild(newPlayBtn, heroPlayBtn);
        newPlayBtn.addEventListener('click', function() {
            if (typeof homeflixApp !== 'undefined') {
                homeflixApp.playTitle(type, id);
            } else {
                window.location.href = `/watch/${type}/${id}`;
            }
        });
    }
    
    if (heroAddBtn && heroAddBtn.parentNode) {
        // Reset button to default state first
        heroAddBtn.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" fill="currentColor"/></svg>';
        heroAddBtn.dataset.added = 'false';
        heroAddBtn.title = 'Add to My List';
        heroAddBtn.style.backgroundColor = '';
        
        const newAddBtn = heroAddBtn.cloneNode(true);
        heroAddBtn.parentNode.replaceChild(newAddBtn, heroAddBtn);
        newAddBtn.addEventListener('click', function() {
            if (typeof homeflixApp !== 'undefined') {
                homeflixApp.toggleMyList(type, id, tmdbId, title, newAddBtn);
            }
        });
        
        // Check if this item is in My List and update button state
        try {
            const response = await fetch('/api/my-list');
            const data = await response.json();
            if (data.success && data.items) {
                const isInList = data.items.some(item => (item.id || item.imdb_id) === id);
                if (isInList) {
                    newAddBtn.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z" fill="currentColor"/></svg>';
                    newAddBtn.dataset.added = 'true';
                    newAddBtn.title = 'Remove from My List';
                }
            }
        } catch (error) {
            console.error('Failed to check My List status:', error);
        }
    }
    
    if (heroLikeBtn && heroLikeBtn.parentNode) {
        // Reset button to default state first
        heroLikeBtn.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z" fill="currentColor"/></svg>';
        heroLikeBtn.dataset.liked = 'false';
        heroLikeBtn.title = 'Rate';
        heroLikeBtn.style.backgroundColor = '';
        
        const newLikeBtn = heroLikeBtn.cloneNode(true);
        heroLikeBtn.parentNode.replaceChild(newLikeBtn, heroLikeBtn);
        newLikeBtn.addEventListener('click', function() {
            if (typeof homeflixApp !== 'undefined') {
                homeflixApp.toggleLike(type, id, title, newLikeBtn);
            }
        });
    }
}

// Netflix-style Hero Banner functionality
function initializeHeroBanner() {
    const heroBanner = document.querySelector('.hero-banner');
    const moreInfoBtn = document.getElementById('moreInfoBtn');
    const heroPlayBtn = document.getElementById('heroPlayBtn');
    const heroAddBtn = document.getElementById('heroAddBtn');
    const heroLikeBtn = document.getElementById('heroLikeBtn');
    const heroCard = document.querySelector('[data-hero="true"]');
    
    // More Info button - Toggle expanded view
    if (moreInfoBtn) {
        moreInfoBtn.addEventListener('click', function() {
            const isExpanded = heroBanner.classList.contains('expanded');
            
            if (isExpanded) {
                heroBanner.classList.remove('expanded');
                const moreInfoText = moreInfoBtn.querySelector('#moreInfoText');
                if (moreInfoText) moreInfoText.textContent = 'More Info';
                // Scroll to top smoothly
                window.scrollTo({ top: 0, behavior: 'smooth' });
            } else {
                heroBanner.classList.add('expanded');
                const moreInfoText = moreInfoBtn.querySelector('#moreInfoText');
                if (moreInfoText) moreInfoText.textContent = 'Less Info';
            }
        });
    }
    
    // Play button
    if (heroPlayBtn && heroCard) {
        heroPlayBtn.addEventListener('click', function() {
            const type = heroCard.dataset.type;
            const id = heroCard.dataset.id;
            if (typeof homeflixApp !== 'undefined') {
                homeflixApp.playTitle(type, id);
            } else {
                window.location.href = `/watch/${type}/${id}`;
            }
        });
    }
    
    // Add to My List button
    if (heroAddBtn && heroCard) {
        heroAddBtn.addEventListener('click', function() {
            const type = heroCard.dataset.type;
            const id = heroCard.dataset.id;
            const tmdbId = heroCard.dataset.tmdbId;
            const title = document.querySelector('.hero-title').textContent;
            
            if (typeof homeflixApp !== 'undefined') {
                homeflixApp.toggleMyList(type, id, tmdbId, title, heroAddBtn);
            }
        });
    }
    
    // Like button
    if (heroLikeBtn && heroCard) {
        heroLikeBtn.addEventListener('click', function() {
            const type = heroCard.dataset.type;
            const id = heroCard.dataset.id;
            const title = document.querySelector('.hero-title').textContent;
            
            if (typeof homeflixApp !== 'undefined') {
                homeflixApp.toggleLike(type, id, title, heroLikeBtn);
            }
        });
    }
    
    // Auto-collapse on scroll down
    let lastScrollTop = 0;
    window.addEventListener('scroll', function() {
        let scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        if (scrollTop > 300 && scrollTop > lastScrollTop && heroBanner.classList.contains('expanded')) {
            heroBanner.classList.remove('expanded');
            if (moreInfoBtn) {
                const moreInfoText = moreInfoBtn.querySelector('#moreInfoText');
                if (moreInfoText) moreInfoText.textContent = 'More Info';
            }
        }
        
        lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
    });
}

// Initialize hero banner navigation arrows
function initializeHeroBannerNavigation() {
    const heroPrevBtn = document.getElementById('heroPrevBtn');
    const heroNextBtn = document.getElementById('heroNextBtn');
    
    if (!heroPrevBtn || !heroNextBtn) {
        return;
    }
    
    // Check if we have enough data for navigation
    if (!backdropUrls || !heroSeries || backdropUrls.length <= 1 || heroSeries.length <= 1) {
        heroPrevBtn.style.display = 'none';
        heroNextBtn.style.display = 'none';
        return;
    }
    
    // Update button states based on current index
    const updateNavButtons = function() {
        const maxIndex = Math.min(backdropUrls.length, heroSeries.length) - 1;

        // Update prev button
        if (currentBackdropIndex === 0) {
            heroPrevBtn.disabled = true;
            heroPrevBtn.style.opacity = '0.3';
            heroPrevBtn.style.cursor = 'not-allowed';
        } else {
            heroPrevBtn.disabled = false;
            heroPrevBtn.style.opacity = '';
            heroPrevBtn.style.cursor = 'pointer';
        }
        
        // Update next button
        if (currentBackdropIndex === maxIndex) {
            heroNextBtn.disabled = true;
            heroNextBtn.style.opacity = '0.3';
            heroNextBtn.style.cursor = 'not-allowed';
        } else {
            heroNextBtn.disabled = false;
            heroNextBtn.style.opacity = '';
            heroNextBtn.style.cursor = 'pointer';
        }
    };
    
    // Navigate to previous hero
    heroPrevBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        if (currentBackdropIndex > 0 && !heroPrevBtn.disabled) {
            // Add flash effect
            heroPrevBtn.classList.add('flash');
            setTimeout(() => heroPrevBtn.classList.remove('flash'), 500);
            
            currentBackdropIndex--;
            updateHeroContent(currentBackdropIndex);
            updateNavButtons();
        }
    });
    
    // Navigate to next hero
    heroNextBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        const maxIndex = Math.min(backdropUrls.length, heroSeries.length) - 1;
     
        if (currentBackdropIndex < maxIndex && !heroNextBtn.disabled) {
            // Add flash effect
            heroNextBtn.classList.add('flash');
            setTimeout(() => heroNextBtn.classList.remove('flash'), 500);
            
            currentBackdropIndex++;
            updateHeroContent(currentBackdropIndex);
            updateNavButtons();
        }
    });
    
    // Initial button state
    updateNavButtons();
    
    // Also update buttons after auto-rotation
    const originalUpdateHeroContent = window.updateHeroContent;
    window.updateHeroContent = function(index) {
        originalUpdateHeroContent(index);
        updateNavButtons();
    };
}

// Toggle hero expanded synopsis
function toggleHeroExpanded() {
    const synopsis = document.getElementById('heroSynopsis');
    const showMoreBtn = document.getElementById('heroShowMoreBtn');
    const showMoreText = document.getElementById('heroShowMoreText');
    
    if (synopsis.classList.contains('expanded')) {
        synopsis.classList.remove('expanded');
        showMoreText.textContent = 'Show More';
    } else {
        synopsis.classList.add('expanded');
        showMoreText.textContent = 'Show Less';
    }
}

// Initialize hero watch button
function initializeHeroWatchButton() {
    const heroWatchBtn = document.getElementById('heroWatchBtn');
    const heroCard = document.querySelector('[data-hero="true"]');
    
    if (heroWatchBtn && heroCard) {
        heroWatchBtn.addEventListener('click', function() {
            const type = heroCard.dataset.type;
            const id = heroCard.dataset.id;
            if (type === 'series') {
                window.location.href = `/series/${id}`;
            } else {
                window.location.href = `/watch/${type}/${id}`;
            }
        });
    }
}

// More Info button functionality
function showMoreInfo() {
    const heroBanner = document.querySelector('.hero-banner');
    const moreInfoBtn = document.getElementById('moreInfoBtn');
    const moreInfoIcon = document.getElementById('moreInfoIcon');
    const moreInfoText = document.getElementById('moreInfoText');
    const isExpanded = heroBanner.classList.contains('expanded');
    
    if (isExpanded) {
        heroBanner.classList.remove('expanded');
        moreInfoText.textContent = 'More Info';
        moreInfoIcon.innerHTML = '<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z" fill="currentColor"/>';
    } else {
        heroBanner.classList.add('expanded');
        moreInfoText.textContent = 'Less Info';
        moreInfoIcon.innerHTML = '<path d="M7 14l5-5 5 5z" fill="currentColor"/>';
    }
}
