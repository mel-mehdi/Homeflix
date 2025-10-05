// UI Components and Interactions

// Netflix-style navbar scroll effect
window.addEventListener('scroll', function() {
    const navbar = document.getElementById('navbar');
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
});

// Search functionality
let searchVisible = false;

function toggleSearch() {
    const searchInput = document.getElementById('searchInput');
    const searchContainer = document.querySelector('.search-container');
    searchVisible = true;
    searchContainer.classList.add('active');
    searchInput.focus();
}

// Hide search when clicking outside
function hideSearchIfOutside(event) {
    const searchContainer = document.querySelector('.search-container');
    const searchToggle = document.querySelector('.search-toggle');
    const searchInput = document.getElementById('searchInput');
    if (
        searchContainer.classList.contains('active') &&
        !searchContainer.contains(event.target) &&
        !searchToggle.contains(event.target)
    ) {
        searchContainer.classList.remove('active');
        searchInput.blur();
        searchInput.value = '';
        searchVisible = false;
    }
}

document.addEventListener('click', hideSearchIfOutside);

// Close search when clicking outside
document.addEventListener('click', function(event) {
    const searchContainer = document.querySelector('.search-container');
    const searchInput = document.getElementById('searchInput');
    
    if (searchVisible && !searchContainer.contains(event.target)) {
        searchVisible = false;
        searchContainer.classList.remove('active');
        searchInput.blur();
        if (searchInput.value.trim() === '') {
            searchInput.value = '';
        }
    }
});

function filterContent() {
    const query = document.getElementById('searchInput').value.trim();
    if (query === '') {
        window.location.href = '/';
        return;
    }
    
    // Show loading state
    const searchButton = document.querySelector('.search-toggle');
    const originalHTML = searchButton.innerHTML;
    searchButton.innerHTML = '<div style="width: 16px; height: 16px; border: 2px solid #fff; border-top: 2px solid transparent; border-radius: 50%; animation: spin 1s linear infinite;"></div>';
    
    // Navigate to search results
    setTimeout(() => {
        window.location.href = `/search?q=${encodeURIComponent(query)}`;
    }, 500);
}

// Initialize search input enter key
function initializeSearch() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keyup', function(event) {
            if (event.key === 'Enter') {
                filterContent();
            }
        });
    }
}

// Initialize content sliders (for drag functionality)
function initializeHeroNavigation() {
    const continueWatchingSlider = document.getElementById('continue-watching-slider');
    const trendingMoviesSlider = document.getElementById('trending-movies-slider');
    const myListSlider = document.getElementById('my-list-slider');
    const moviesSlider = document.getElementById('movies-slider');
    const trendingSeriesSlider = document.getElementById('trending-series-slider');
    const seriesSlider = document.getElementById('series-slider');

    // Initialize sliders if they exist (no need for drag or arrow functionality)
    // The grid layout handles everything automatically
}

// Initialize slider functionality - simplified for grid layout
function initializeSlider(slider) {
    // Grid layout doesn't need slider initialization
    // All content is visible and scrollable vertically
}
