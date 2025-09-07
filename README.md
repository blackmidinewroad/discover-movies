# Discover Movies
Discover Movies is a Django-based web application for exploring movies and related to movies data powered by [TMDB](https://www.themoviedb.org/) (The Movie Database). It syncs TMDB data into a PostgreSQL database and provides filtering, sorting, and search capabilities through a simple web interface.


## Technologies Used
- **Backend**: Django, Redis.
- **Database**: PostgreSQL.
- **Frontend**: Django Templates, Bootstrap, HTMX, minimal JavaScript.


## Features
- **Movies Page**: Displays a grid of movie posters with many filtering options (e.g. genre, decade) and dorting options (e.g. popularity, release date).
- **People Page**: Lists individuals involved in movies (e.g., actors, directors) with filters for department (e.g., writing, sound) and sorting by popularity or number of roles.
- **Other Page**: Showcases countries, languages, production companies, and collections.
- **Detail Pages**:
  - **Movie Detail**: Displays movie details, such as genres, production companies, cast, crew, etc.
  - **Person Detail**: Shows biography and cust/crew roles.
- **Search**: Each page includes a search feature powered by PostgreSQL's trigram similarity for fuzzy matching.
- **Data Synchronization**: Uses TMDB API to fetch and update all relevant movie data.
- **Custom Management Commands**: Uses several custom Django management commands to sync and update database content.


## Installation
1. **Clone the Repository**:
   ```shell
   git clone https://github.com/blackmidinewroad/discover-movies.git
   cd discover-movies
   ```

2. **Install Dependencies**
   - Using pipenv:

      ```shell
      pipenv install
      ```
   - Using pip:
   
      ```shell
      pip install -r requirements.txt
      ```

3. **Install Redis**

   This project uses Redis as the cache backend. You can install it from the official [Redis installation guide](https://redis.io/docs/latest/operate/oss_and_stack/install/install-stack/).

   After installation, make sure Redis is running.

4. **Create Database**

   1. Download [PostgreSQL](https://www.postgresql.org/download/) if you don't have it yet.
   2. In **SQL Shell (psql)** create new user.
   3. Create database with the name `moviedb` and give ownership to the created user.
   

5. **Set Up Environment Variables**

   Create a `.env` file in the project root with the following:
   ```env
    SECRET_KEY='your-secret-key'
    DB_NAME='moviedb'
    DB_USER='your-db-user'
    DB_PASSWORD='your-db-password'
    DB_HOST='your-db-host'
    DB_PORT='your-db-port'
    ALLOWED_HOSTS='localhost,127.0.0.1'
    TMDB_ACCESS_TOKEN='your-tmdb-access-token'
    CACHES_BACKEND='caches-backend'
    CACHES_LOCATION='caches-location'
   ```

   - Generate a secure `SECRET_KEY` using:
   ```shell
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
   - Replace `your-tmdb-access-token` with your actual access token. If you don't have it yet, sign up at [TMDB](https://www.themoviedb.org/), then go to [API settings](https://www.themoviedb.org/settings/api) to register for an API access. After API registration you will have `API Read Access Token` in your profile settings.
   - Reaplce `caches-backend` and `caches-location` with your cache configuration (e.g. `CACHES_BACKEND='django.core.cache.backends.redis.RedisCache'`, `CACHES_LOCATION='redis://127.0.0.1:6379'`).

6. **Database Setup**:
   ```shell
   python manage.py migrate
   ```

   Populate database with initial data by running `load_initial_data.ps1` script:
   ```shell
    .\load_initial_data.ps1
   ```


## Usage
1. **Run the Server**:
   ```shell
   python manage.py runserver
   ```

2. **Open the Website**:

    Discover Movies should now be available at http://localhost:8000.


## Custom Management Commands
The project includes several custom management commands to manage data:
- **`update_movies`**: Updates the _movie_ table with operations like `daily_export` (fetches new movies), `update_changed` (updates changed movies), `add_top_rated` (fetches top-rated movies), and `specific_ids` (processes specific TMDB IDs).
- **`update_people`**: Updates the _person_ table with operations like `daily_export` (fetches new people), `update_changed` (updates people with change data), `specific_ids` (processes specific TMDB IDs), and `roles_count` (updates roles count for each person in the database).
- **`update_companies`**: Manages _production company_ data.
- **`update_collections`**: Handles _collection_ data.
- **`update_countries`**, **`update_languages`**, **`update_genres`**: Populate static data for _countries_, _languages_, and _genres_.
- **`update_removed`**: Marks removed entities in the database.
- **`update_popularity`**: Updates popularity metrics for _movies_ and _people_.

Full list of commands with all available arguments is in the [commands](apps/moviedb//management/commands/) directory.


## Data Fetching
All the data is fetched from TMDB using **TMDB API**. Data synchronization is handled via:
- **TMDB API Wrappers**:
  - `TMDB`: Synchronous wrapper for fetching movie related data.
  - `asyncTMDB`: Asynchronous wrapper for batch fetching movie related data, with rate limiting and retry logic for robustness.
- **ID Exports**: Downloads and processes TMDB's daily ID export files to identify new or changed records.
- **PowerShell Scripts**:
  - `sync_db.ps1`: Runs a sequence of management commands to update all the tables in the database.
  - `load_initial_data.ps1`: Loads initial data (countries, languages, genres, and 1000 most popular movies) for testing.