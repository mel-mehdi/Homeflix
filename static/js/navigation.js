// Navigation functionality

// Mobile menu toggle
function toggleMobileMenu() {
    const mobileMenu = document.getElementById('mobileNavMenu');
    const menuToggle = document.getElementById('mobileMenuToggle');
    
    if (mobileMenu) {
        mobileMenu.classList.toggle('active');
        
        // Update icon
        const isActive = mobileMenu.classList.contains('active');
        menuToggle.innerHTML = isActive 
            ? '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" fill="currentColor"/></svg>'
            : '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z" fill="currentColor"/></svg>';
    }
}

// Close mobile menu when clicking outside
document.addEventListener('click', function(event) {
    const mobileMenu = document.getElementById('mobileNavMenu');
    const menuToggle = document.getElementById('mobileMenuToggle');
    
    if (mobileMenu && menuToggle) {
        if (!mobileMenu.contains(event.target) && !menuToggle.contains(event.target)) {
            if (mobileMenu.classList.contains('active')) {
                toggleMobileMenu();
            }
        }
    }
});

// Close mobile menu on scroll
let lastScrollTop = 0;
window.addEventListener('scroll', function() {
    const mobileMenu = document.getElementById('mobileNavMenu');
    if (mobileMenu && mobileMenu.classList.contains('active')) {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        if (Math.abs(scrollTop - lastScrollTop) > 50) {
            toggleMobileMenu();
        }
        lastScrollTop = scrollTop;
    }
});

function filterByType(type) {
    if (type === 'movie') {
        // Scroll to movies section
        const moviesSection = document.querySelector('#movies-slider').closest('.content-row');
        moviesSection.scrollIntoView({ behavior: 'smooth' });
        
        // Hide TV shows section temporarily
        const tvSection = document.querySelector('#series-slider').closest('.content-row');
        tvSection.style.display = 'none';
        setTimeout(() => {
            tvSection.style.display = 'block';
        }, 2000);
        
        // Update title
        const movieTitle = moviesSection.querySelector('.row-title');
        movieTitle.textContent = 'Movies';
        
    } else if (type === 'tv') {
        // Scroll to TV shows section
        const tvSection = document.querySelector('#series-slider').closest('.content-row');
        tvSection.scrollIntoView({ behavior: 'smooth' });
        
        // Hide movies section temporarily
        const moviesSection = document.querySelector('#movies-slider').closest('.content-row');
        moviesSection.style.display = 'none';
        setTimeout(() => {
            moviesSection.style.display = 'block';
        }, 2000);
        
        // Update title
        const tvTitle = tvSection.querySelector('.row-title');
        tvTitle.textContent = 'TV Shows';
    }
}

function showNewPopular() {
    // Show all content and highlight as "New & Popular"
    const allSections = document.querySelectorAll('.content-row');
    allSections.forEach(section => {
        section.style.display = 'block';
        const title = section.querySelector('.row-title');
        if (title.textContent.includes('Movies')) {
            title.textContent = 'New & Popular Movies';
        } else if (title.textContent.includes('TV')) {
            title.textContent = 'New & Popular TV Shows';
        }
    });
    
    // Scroll to top of content
    document.querySelector('.content-row').scrollIntoView({ behavior: 'smooth' });
}
