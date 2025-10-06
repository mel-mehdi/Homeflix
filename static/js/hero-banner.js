// Hero Banner functionality
let currentBackdropIndex = 0;
let backdropUrls = [];
let heroSeries = [];
let autoRotationInterval = null; // Store the interval ID

// Preload images cache
const preloadedImages = new Map();
let allImagesPreloaded = false;

// Preload backdrop images for faster transitions
function preloadBackdropImages() {
    if (!backdropUrls || backdropUrls.length === 0) return;
    
    console.log(`Starting to preload ${backdropUrls.length} backdrop images...`);
    let loadedCount = 0;
    
    backdropUrls.forEach((url, index) => {
        const img = new Image();
        
        img.onload = () => {
            loadedCount++;
            console.log(`Preloaded image ${loadedCount}/${backdropUrls.length}: ${url}`);
            preloadedImages.set(url, img);
            
            if (loadedCount === backdropUrls.length) {
                allImagesPreloaded = true;
                console.log('✅ All hero banner images preloaded successfully!');
            }
        };
        
        img.onerror = () => {
            console.error(`Failed to preload image: ${url}`);
            loadedCount++;
        };
        
        // Start loading
        img.src = url;
    });
}

// Initialize hero banner data
function initializeHeroBannerData(backdrops, series) {
    console.log('Initializing hero banner data...');
    console.log('Backdrops:', backdrops);
    console.log('Series:', series);
    
    backdropUrls = backdrops || [];
    heroSeries = series || [];
    
    console.log(`Initialized with ${backdropUrls.length} backdrops and ${heroSeries.length} series`);
    
    // Preload images on page load
    if (backdropUrls && backdropUrls.length > 0) {
        preloadBackdropImages();
    }

    // Initialize navigation arrows now that data is loaded
    initializeHeroBannerNavigation();

    // Start auto-rotation
    startAutoRotation();
}

// Start or restart auto-rotation
function startAutoRotation() {
    // Clear existing interval if any
    if (autoRotationInterval) {
        clearInterval(autoRotationInterval);
        console.log('Cleared existing auto-rotation interval');
    }
    
    // Only start if we have enough data
    if (backdropUrls && backdropUrls.length > 1 && heroSeries && heroSeries.length > 1) {
        console.log('Starting auto-rotation interval (8 seconds)');
        autoRotationInterval = setInterval(() => {
            currentBackdropIndex = (currentBackdropIndex + 1) % Math.min(backdropUrls.length, heroSeries.length);
            console.log(`Auto-rotating to index: ${currentBackdropIndex}`);
            updateHeroContent(currentBackdropIndex);
            // Update navigation button states after auto-rotation
            updateHeroNavigationButtons();
        }, 8000);
    }
}

// Update hero banner content to match the current featured series
function updateHeroContent(index) {
    console.log(`updateHeroContent called with index: ${index}`);
    console.log(`Total backdrops: ${backdropUrls.length}, Total series: ${heroSeries.length}`);
    
    const heroBanner = document.querySelector('.hero-banner');
    const heroInfo = document.querySelector('.hero-info');
    const series = heroSeries[index];
    
    if (!heroBanner) {
        console.error('Hero banner element not found');
        return;
    }
    
    if (!series) {
        console.error(`Series not found at index ${index}`);
        return;
    }
    
    if (!heroInfo) {
        console.error('Hero info element not found');
        return;
    }
    
    console.log(`Updating hero content to series: ${series.title}`);
    
    // Update background FIRST before fading out content
    if (backdropUrls[index]) {
        const imageUrl = backdropUrls[index];
        console.log(`Setting background image to: ${imageUrl}`);
        const preloadedImg = preloadedImages.get(imageUrl);
        
        // Check if image is preloaded and ready
        if (preloadedImg && preloadedImg.complete && preloadedImg.naturalHeight !== 0) {
            console.log('✅ Using preloaded image - instant display');
            // Apply immediately with smooth transition
            heroBanner.style.transition = 'background-image 0.5s ease-in-out';
            heroBanner.style.backgroundImage = `url('${imageUrl}')`;
            heroBanner.style.backgroundSize = 'cover';
            heroBanner.style.backgroundPosition = 'center';
        } else {
            console.log('⚠️ Image not fully preloaded yet, applying anyway');
            heroBanner.style.transition = 'background-image 0.5s ease-in-out';
            heroBanner.style.backgroundImage = `url('${imageUrl}')`;
            heroBanner.style.backgroundSize = 'cover';
            heroBanner.style.backgroundPosition = 'center';
        }
    } else {
        console.error(`No backdrop URL at index ${index}`);
    }
    
    // Add fade-out effect to content
    heroInfo.style.opacity = '0';
    heroInfo.style.transition = 'opacity 0.3s ease-in-out';
    
    // Wait for fade-out to complete before updating content
    setTimeout(() => {
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
        
        // Preload adjacent images for even smoother navigation
        const maxIndex = Math.min(backdropUrls.length, heroSeries.length);
        const nextIndex = (index + 1) % maxIndex;
        const prevIndex = (index - 1 + maxIndex) % maxIndex;
        
        // Preload next image
        if (backdropUrls[nextIndex] && !preloadedImages.has(backdropUrls[nextIndex])) {
            console.log(`Preloading next image at index ${nextIndex}`);
            const nextImg = new Image();
            nextImg.onload = () => {
                preloadedImages.set(backdropUrls[nextIndex], nextImg);
                console.log(`✅ Next image preloaded: ${backdropUrls[nextIndex]}`);
            };
            nextImg.src = backdropUrls[nextIndex];
        }
        
        // Preload previous image
        if (backdropUrls[prevIndex] && !preloadedImages.has(backdropUrls[prevIndex])) {
            console.log(`Preloading previous image at index ${prevIndex}`);
            const prevImg = new Image();
            prevImg.onload = () => {
                preloadedImages.set(backdropUrls[prevIndex], prevImg);
                console.log(`✅ Previous image preloaded: ${backdropUrls[prevIndex]}`);
            };
            prevImg.src = backdropUrls[prevIndex];
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
            
            if (typeof homeflixApp !== 'undefined' && homeflixApp.toggleMyList) {
                homeflixApp.toggleMyList(type, id, tmdbId, title, heroAddBtn);
            } else {
                console.error('homeflixApp.toggleMyList is not available');
            }
        });
    }
    
    // Like button
    if (heroLikeBtn && heroCard) {
        heroLikeBtn.addEventListener('click', function() {
            const type = heroCard.dataset.type;
            const id = heroCard.dataset.id;
            const title = document.querySelector('.hero-title').textContent;
            
            if (typeof homeflixApp !== 'undefined' && homeflixApp.toggleLike) {
                homeflixApp.toggleLike(type, id, title, heroLikeBtn);
            } else {
                console.error('homeflixApp.toggleLike is not available');
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
        console.log('Hero navigation buttons not found');
        return;
    }
    
    // Check if we have enough data for navigation
    if (!backdropUrls || !heroSeries || backdropUrls.length <= 1 || heroSeries.length <= 1) {
        console.log('Not enough hero data for navigation - buttons will remain hidden');
        // Don't set visibility or display, let CSS opacity handle it
        // Just add inactive class so they can't be clicked
        heroPrevBtn.classList.add('inactive');
        heroNextBtn.classList.add('inactive');
        heroPrevBtn.setAttribute('aria-disabled', 'true');
        heroNextBtn.setAttribute('aria-disabled', 'true');
        return;
    }
    
    console.log(`Hero navigation initialized with ${backdropUrls.length} backdrops and ${heroSeries.length} series`);
    
    // Navigate to previous hero
    heroPrevBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        console.log(`Prev button clicked. Current index: ${currentBackdropIndex}`);
        
        // Check if we can navigate (don't use disabled property)
        if (currentBackdropIndex > 0 && !heroPrevBtn.classList.contains('inactive')) {
            // Add flash effect
            heroPrevBtn.classList.add('flash');
            setTimeout(() => heroPrevBtn.classList.remove('flash'), 500);
            
            currentBackdropIndex--;
            console.log(`Navigating to previous. New index: ${currentBackdropIndex}`);
            updateHeroContent(currentBackdropIndex);
            updateHeroNavigationButtons();
            
            // Restart auto-rotation timer
            startAutoRotation();
        }
    });
    
    // Navigate to next hero
    heroNextBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        const maxIndex = Math.min(backdropUrls.length, heroSeries.length) - 1;
        
        console.log(`Next button clicked. Current index: ${currentBackdropIndex}, Max index: ${maxIndex}`);
     
        // Check if we can navigate (don't use disabled property)
        if (currentBackdropIndex < maxIndex && !heroNextBtn.classList.contains('inactive')) {
            // Add flash effect
            heroNextBtn.classList.add('flash');
            setTimeout(() => heroNextBtn.classList.remove('flash'), 500);
            
            currentBackdropIndex++;
            console.log(`Navigating to next. New index: ${currentBackdropIndex}`);
            updateHeroContent(currentBackdropIndex);
            updateHeroNavigationButtons();
            
            // Restart auto-rotation timer
            startAutoRotation();
        }
    });
    
    // Initial button state
    updateHeroNavigationButtons();
}

// Update hero navigation button states (global function)
function updateHeroNavigationButtons() {
    const heroPrevBtn = document.getElementById('heroPrevBtn');
    const heroNextBtn = document.getElementById('heroNextBtn');
    
    if (!heroPrevBtn || !heroNextBtn) {
        return;
    }
    
    const maxIndex = Math.min(backdropUrls.length, heroSeries.length) - 1;
    
    console.log(`Updating nav buttons: currentIndex=${currentBackdropIndex}, maxIndex=${maxIndex}`);

    // Update prev button - use CSS class instead of disabled attribute
    if (currentBackdropIndex === 0) {
        heroPrevBtn.classList.add('inactive');
        heroPrevBtn.setAttribute('aria-disabled', 'true');
    } else {
        heroPrevBtn.classList.remove('inactive');
        heroPrevBtn.setAttribute('aria-disabled', 'false');
    }
    
    // Update next button - use CSS class instead of disabled attribute
    if (currentBackdropIndex === maxIndex) {
        heroNextBtn.classList.add('inactive');
        heroNextBtn.setAttribute('aria-disabled', 'true');
    } else {
        heroNextBtn.classList.remove('inactive');
        heroNextBtn.setAttribute('aria-disabled', 'false');
    }
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
