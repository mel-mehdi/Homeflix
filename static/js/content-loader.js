// Content Loading and Pagination

let moviePage = 1;
let seriesPage = 1;
let searchQuery = '';

// Initialize pagination data
function initializePaginationData(movie_page, series_page, search_query) {
    moviePage = movie_page;
    seriesPage = series_page;
    searchQuery = search_query || '';
}

// Load more movies
function loadMoreMovies() {
    const button = document.querySelector('#movies-slider').parentElement.querySelector('.load-more-button');
    button.disabled = true;
    button.textContent = 'Loading...';
    moviePage++;
    const url = searchQuery ? `/search_more_movies/${encodeURIComponent(searchQuery)}/${moviePage}` : `/load_more_movies/${moviePage}`;
    
    fetch(url)
        .then(response => response.json())
        .then((data) => {
            if (data.movies && data.movies.length > 0) {
                const slider = document.getElementById('movies-slider');
                data.movies.forEach(movie => {
                    const card = createTitleCard(movie, 'movie');
                    slider.appendChild(card);
                });
            } else {
                button.style.display = 'none';
            }
            button.disabled = false;
            button.textContent = searchQuery ? 'Load More' : 'Load More Movies';
        })
        .catch(error => {
            console.error('Error loading more movies:', error);
            button.disabled = false;
            button.textContent = searchQuery ? 'Load More' : 'Load More Movies';
        });
}

// Load more series
function loadMoreSeries() {
    const button = document.querySelector('#series-slider').parentElement.querySelector('.load-more-button');
    button.disabled = true;
    button.textContent = 'Loading...';
    seriesPage++;
    const url = searchQuery ? `/search_more_series/${encodeURIComponent(searchQuery)}/${seriesPage}` : `/load_more_series/${seriesPage}`;
    
    fetch(url)
        .then(response => response.json())
        .then((data) => {
            if (data.series && data.series.length > 0) {
                const slider = document.getElementById('series-slider');
                data.series.forEach(show => {
                    const card = createTitleCard(show, 'series');
                    slider.appendChild(card);
                });
            } else {
                button.style.display = 'none';
            }
            button.disabled = false;
            button.textContent = searchQuery ? 'Load More' : 'Load More Shows';
        })
        .catch(error => {
            console.error('Error loading more series:', error);
            button.disabled = false;
            button.textContent = searchQuery ? 'Load More' : 'Load More Shows';
        });
}
