// Main initialization script

// Initialize all components on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeHeroBanner();
    // initializeHeroBannerNavigation(); // This is now called from initializeHeroBannerData() after data is loaded
    setupTitleCardInteractions();
    initializeHeroWatchButton();
    initializeHeroNavigation();
    initializeSearch();
    
    // Wait a bit for hero banner to be fully set up, then initialize button states
    setTimeout(() => {
        initializeMyListButtons();
    }, 100);
});
