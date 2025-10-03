// Navigation functionality

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
