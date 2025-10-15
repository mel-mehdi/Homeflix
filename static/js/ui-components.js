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
let searchTimeout = null;

function toggleSearch() {
    const searchInput = document.getElementById('searchInput');
    const searchContainer = document.querySelector('.search-container');
    
    if (!searchVisible) {
        searchVisible = true;
        searchContainer.classList.add('active');
        setTimeout(() => {
            searchInput.focus();
        }, 100);
    } else {
        // If search is visible and has content, perform search
        if (searchInput.value.trim()) {
            filterContent();
        } else {
            // If no content, close search and clear
            searchVisible = false;
            searchContainer.classList.remove('active');
            searchInput.value = '';
            searchInput.blur();
        }
    }
}

// Hide search when clicking outside
function hideSearchIfOutside(event) {
    const searchContainer = document.querySelector('.search-container');
    const searchToggle = document.querySelector('.search-toggle');
    const searchInput = document.getElementById('searchInput');
    const suggestionsContainer = document.getElementById('searchSuggestions');
    
    if (
        searchVisible &&
        searchContainer.classList.contains('active') &&
        !searchContainer.contains(event.target)
    ) {
        // Close search and clear input when clicking outside
        searchContainer.classList.remove('active');
        searchInput.blur();
        searchInput.value = ''; // Clear the input text
        searchVisible = false;
        hideSearchSuggestions();
    }
    
    // Also hide suggestions if clicking outside search container
    if (suggestionsContainer && !searchContainer.contains(event.target)) {
        hideSearchSuggestions();
    }
}

document.addEventListener('click', hideSearchIfOutside);

// Close search on Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const searchContainer = document.querySelector('.search-container');
        const searchInput = document.getElementById('searchInput');
        
        if (searchVisible) {
            searchVisible = false;
            searchContainer.classList.remove('active');
            searchInput.blur();
            searchInput.value = '';
            hideSearchSuggestions();
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

// Initialize search input enter key and live suggestions
function initializeSearch() {
    const searchInput = document.getElementById('searchInput');
    const searchSuggestions = document.getElementById('searchSuggestions');
    
    if (!searchInput) {
        console.error('❌ searchInput element not found!');
        return;
    }
    
    if (!searchSuggestions) {
        console.error('❌ searchSuggestions element not found!');
        return;
    }
    
    // Attach keyup event
    searchInput.addEventListener('keyup', function(event) {
        if (event.key === 'Enter') {
            filterContent();
        } else if (event.key === 'Escape') {
            // Escape key handling is already in the global listener
            return;
        } else {
            // Trigger live search suggestions
            handleSearchInput();
        }
    });
    
    // Also trigger on input event for better responsiveness
    searchInput.addEventListener('input', function(event) {
        handleSearchInput();
    });
}

// Handle search input and fetch suggestions
let searchDebounceTimer = null;
let currentSearchRequest = null;

function handleSearchInput() {
    const searchInput = document.getElementById('searchInput');
    const query = searchInput.value.trim();
    
    // Clear existing timer
    if (searchDebounceTimer) {
        clearTimeout(searchDebounceTimer);
    }
    
    // Cancel any ongoing request
    if (currentSearchRequest) {
        currentSearchRequest.abort();
    }
    
    // If query is empty, hide suggestions
    if (query === '' || query.length < 2) {
        hideSearchSuggestions();
        return;
    }
    
    // Debounce the search to avoid too many requests
    searchDebounceTimer = setTimeout(() => {
        fetchSearchSuggestions(query);
    }, 300); // Wait 300ms after user stops typing
}

// Fetch search suggestions from the backend
function fetchSearchSuggestions(query) {
    const suggestionsContainer = document.getElementById('searchSuggestions');
    
    
    if (!suggestionsContainer) {
        console.error('❌ Search suggestions container not found');
        return;
    }
    
    // Create new AbortController for this request
    const controller = new AbortController();
    currentSearchRequest = controller;
    
    // Show loading state
    suggestionsContainer.innerHTML = '<div class="suggestion-item loading">Searching...</div>';
    suggestionsContainer.classList.add('show');
    
    const apiUrl = `/api/search_suggestions?q=${encodeURIComponent(query)}`;
    
    fetch(apiUrl, {
        signal: controller.signal
    })
    .then(response => {
        return response.json();
    })
    .then(data => {
        displaySearchSuggestions(data.results, query);
        currentSearchRequest = null;
    })
    .catch(error => {
        if (error.name !== 'AbortError') {
            console.error('❌ Error fetching suggestions:', error);
            suggestionsContainer.innerHTML = '<div class="suggestion-item error">Error loading suggestions</div>';
        }
        currentSearchRequest = null;
    });
}

// Display search suggestions in the dropdown
function displaySearchSuggestions(results, query) {
    const suggestionsContainer = document.getElementById('searchSuggestions');
    
    if (!suggestionsContainer) {
        console.error('❌ Search suggestions container not found');
        return;
    }
    
    if (!results || results.length === 0) {
        suggestionsContainer.innerHTML = '<div class="suggestion-item no-results">No results found</div>';
        suggestionsContainer.classList.add('show');
        return;
    }
    
    // Clear existing content
    suggestionsContainer.innerHTML = '';
    
    // Add each suggestion
    results.forEach((item, index) => {
        
        const suggestionItem = document.createElement('div');
        suggestionItem.className = 'suggestion-item';
        
        // Create icon based on type
        const icon = item.type === 'movie' 
            ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M19 4H5a2 2 0 00-2 2v12a2 2 0 002 2h14a2 2 0 002-2V6a2 2 0 00-2-2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M7 2v4M17 2v4M2 10h20" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
            : '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M20 7h-5M20 17h-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><rect x="2" y="3" width="12" height="18" rx="2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
        
        // Highlight matching text
        const title = highlightMatch(item.title, query);
        const year = item.year ? `<span class="suggestion-year">(${item.year})</span>` : '';
        
        suggestionItem.innerHTML = `
            <span class="suggestion-icon">${icon}</span>
            <span class="suggestion-title">${title} ${year}</span>
            <span class="suggestion-type">${item.type}</span>
        `;
        
        // Add click handler
        suggestionItem.addEventListener('click', () => {
            navigateToItem(item);
        });
        
        suggestionsContainer.appendChild(suggestionItem);
    });
    
    suggestionsContainer.classList.add('show');
}

// Highlight matching text in the title
function highlightMatch(text, query) {
    const regex = new RegExp(`(${escapeRegex(query)})`, 'gi');
    return text.replace(regex, '<strong>$1</strong>');
}

// Escape special regex characters
function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Navigate to the selected item
function navigateToItem(item) {
    if (item.type === 'movie') {
        window.location.href = `/movie/${item.id || item.imdb_id}`;
    } else if (item.type === 'series') {
        window.location.href = `/series/${item.id || item.imdb_id}`;
    }
}

// Hide search suggestions
function hideSearchSuggestions() {
    const suggestionsContainer = document.getElementById('searchSuggestions');
    if (suggestionsContainer) {
        suggestionsContainer.classList.remove('show');
        suggestionsContainer.innerHTML = '';
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
