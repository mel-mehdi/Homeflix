# Mark Series/Season as Watched - Feature Implementation

## Overview
Added comprehensive functionality to mark entire series or seasons as watched, making it easy for users to batch-update their watch status.

## Features Added

### 1. Database Layer (`db_service.py`)

Added new methods to `DatabaseService` class:

#### Season Operations
- **`mark_season_as_watched()`** - Mark all episodes in a season as watched
- **`unmark_season_as_watched()`** - Remove watched marks from all episodes in a season
- **`get_season_watch_status()`** - Get watched status for all episodes in a season

#### Series Operations  
- **`mark_series_as_watched()`** - Mark all episodes in all seasons as watched
- **`unmark_series_as_watched()`** - Remove watched marks from entire series
- **`get_series_watch_status()`** - Get watched status grouped by season

### 2. API Endpoints (`media_server.py`)

Added 6 new REST API endpoints:

#### Season Endpoints
- `POST /api/mark_season_watched` - Mark entire season as watched
- `POST /api/unmark_season_watched` - Unmark entire season
- `GET /api/season_watch_status/<media_id>/<season_number>` - Check season watch status

#### Series Endpoints
- `POST /api/mark_series_watched` - Mark entire series as watched
- `POST /api/unmark_series_watched` - Unmark entire series  
- `GET /api/series_watch_status/<media_id>` - Check series watch status

### 3. User Interface

#### Season Details Page (`season_details.html`)
- ✅ "Mark Season as Watched" button in header
- ✅ Button changes to "Unmark Season as Watched" when all episodes watched
- ✅ Visual feedback with color changes (green when watched)
- ✅ Automatically updates all episode watch marks
- ✅ Checks status on page load

#### Series Details Page (`series_details.html`)
- ✅ "Mark Series Watched" button in action buttons
- ✅ Button changes to "Unmark Series Watched" when fully watched
- ✅ Visual feedback with color changes
- ✅ Processes all seasons and episodes
- ✅ Checks status on page load

## API Usage Examples

### Mark Season as Watched
```javascript
POST /api/mark_season_watched
{
  "id": "tt0903747",           // IMDB ID
  "tmdb_id": 1396,             // TMDB ID
  "title": "Breaking Bad",
  "season_number": 1,
  "episode_count": 7
}
```

### Mark Entire Series as Watched
```javascript
POST /api/mark_series_watched
{
  "id": "tt0903747",
  "tmdb_id": 1396,
  "title": "Breaking Bad",
  "seasons": [
    {"season_number": 1, "episode_count": 7},
    {"season_number": 2, "episode_count": 13},
    {"season_number": 3, "episode_count": 13},
    ...
  ]
}
```

### Check Season Watch Status
```javascript
GET /api/season_watch_status/tt0903747/1

Response:
{
  "watched_episodes": [1, 2, 3, 5, 7],
  "watched_count": 5
}
```

### Check Series Watch Status
```javascript
GET /api/series_watch_status/tt0903747

Response:
{
  "watched_by_season": {
    "1": [1, 2, 3, 4, 5, 6, 7],
    "2": [1, 3, 5],
    "3": []
  },
  "total_watched": 10
}
```

## How It Works

### Season Marking
1. User clicks "Mark Season as Watched" button
2. JavaScript collects season data (IMDB ID, TMDB ID, season number, episode count)
3. Sends POST request to `/api/mark_season_watched`
4. Backend creates watched marks for each episode (1 to episode_count)
5. Button updates to show "Unmark Season as Watched" with green styling
6. All individual episode watch buttons update automatically

### Series Marking
1. User clicks "Mark Series Watched" button
2. JavaScript collects all seasons data from template
3. Sends POST request to `/api/mark_series_watched` with seasons array
4. Backend iterates through each season and marks all episodes
5. Button updates with visual feedback
6. Alert shown to confirm action

## Database Impact

### WatchedItems Table
```sql
-- Example records created when marking Season 1 with 7 episodes:
INSERT INTO watched_items (media_type, media_id, tmdb_id, title, season_number, episode_number)
VALUES 
  ('series', 'tt0903747', 1396, 'Breaking Bad - S1E1', 1, 1),
  ('series', 'tt0903747', 1396, 'Breaking Bad - S1E2', 1, 2),
  ...
  ('series', 'tt0903747', 1396, 'Breaking Bad - S1E7', 1, 7);
```

## User Experience

### Season Page
- Single click marks entire season
- Progress indicator while processing
- Button shows current state (marked/unmarked)
- Color feedback (gray = unwatched, green = watched)
- Individual episode marks update automatically

### Series Page
- Single click marks entire series (all seasons, all episodes)
- Confirmation alert after completion
- Button shows current state
- Color feedback
- Works with series of any length

## Performance Considerations

- **Batch operations**: Uses single transaction per season
- **Upserts**: Won't create duplicates if already watched
- **Efficient queries**: Uses composite indexes on watched_items table
- **Smart checks**: Only processes valid seasons (season_number > 0)
- **Error handling**: Rollback on failure, user-friendly error messages

## Future Enhancements

Possible improvements:
1. Progress bar for marking large series
2. Bulk operations from series list view
3. "Mark up to this episode" feature
4. Watched percentage display on season cards
5. Undo functionality
6. Analytics: most watched shows, completion rates

## Testing

To test the feature:
1. Navigate to a series details page
2. Click "Mark Series Watched" - all episodes marked
3. Navigate to season details page
4. Verify all episodes show as watched
5. Click "Unmark Season as Watched" on season page
6. Verify episode marks updated
7. Test with series having multiple seasons
8. Test with incomplete watch history

---

**Status**: ✅ Fully Implemented and Working
**Version**: 1.0
**Date**: October 15, 2025
