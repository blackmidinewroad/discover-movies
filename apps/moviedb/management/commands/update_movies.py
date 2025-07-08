from datetime import date

from django.core.management.base import BaseCommand

from apps.moviedb import models
from apps.moviedb.integrations.tmdb.api import asyncTMDB
from apps.moviedb.integrations.tmdb.id_exports import IDExport


class Command(BaseCommand):
    help = 'Update movie table'
    language_cache = {}

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            default=None,
            help='Date of the export file in "DD_MM_YYYY" format.',
        )

        parser.add_argument(
            '--batch_size',
            type=int,
            default=100,
            help='Number of movies to fetch per batch.',
        )

        parser.add_argument(
            '--specific_ids',
            type=int,
            default=None,
            nargs='*',
            help='Update specific movies.',
        )

        parser.add_argument(
            '--create',
            action='store_true',
            default=False,
            help='Only create new movies.',
        )

        parser.add_argument(
            '--language',
            type=str,
            default='en-US',
            help='Locale (ISO 639-1-ISO 3166-1) code (e.g. en-UD, fr-CA, de_DE). Defaults to "en-US".',
        )

        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of movies added.',
        )

        parser.add_argument(
            '--sort_by_popularity',
            action='store_true',
            default=False,
            help='Sort IDs by popularity if possible.',
        )

        parser.add_argument(
            '--top_rated',
            action='store_true',
            default=False,
            help='Fetch top rated movies on TMDB.',
        )

    def handle(self, *args, **kwargs):
        specific_ids = kwargs['specific_ids']
        batch_size = kwargs['batch_size']
        language = kwargs['language']
        limit = kwargs['limit']
        sort_by_popularity = ['sort_by_popularity']

        if kwargs['top_rated']:
            movie_ids = asyncTMDB().fetch_top_rated_movie_ids(last_page=500)
        else:
            if specific_ids is None:
                published_date = kwargs['date']
                id_export = IDExport()
                movie_ids = id_export.fetch_ids('movie', published_date=published_date, sort_by_popularity=sort_by_popularity)
            else:
                movie_ids = specific_ids

        if kwargs['create']:
            existing_ids = set(models.Movie.objects.all().values_list('tmdb_id', flat=True))
            movie_ids = [id for id in movie_ids if id not in existing_ids]

        movies, not_fetched_movie_ids = asyncTMDB().batch_fetch_movies_by_id(
            movie_ids[:limit],
            batch_size=batch_size,
            language=language,
            append_to_response=['credits'],
        )

        existing_genres = set(models.Genre.objects.all().values_list('tmdb_id', flat=True))
        existing_languages = set(models.Language.objects.all().values_list('code', flat=True))
        existing_countries = set(models.Country.objects.all().values_list('code', flat=True))

        n_created_companies, not_fetched_company_ids = self.create_missing_companies(movies)

        count_created = count_updated = skipped = total_created_persons = 0

        for movie in movies:
            # Create missing persons before
            cast = movie['credits']['cast']
            crew = movie['credits']['crew']

            n_created_persons, is_missing_persons = self.create_missing_persons(cast + crew)

            total_created_persons += n_created_persons

            # If couldn't create all people from the movie - skip movie
            if is_missing_persons:
                self.stdout.write(self.style.WARNING(f"Skipped «{movie['title']}» because couldn't create all people"))
                skipped += 1
                continue

            # If couldn't create needed production companies - skip movie
            company_ids = [company['id'] for company in movie['production_companies']]
            if not_fetched_company_ids and (set(not_fetched_company_ids) & set(company_ids)):
                self.stdout.write(self.style.WARNING(f"Skipped «{movie['title']}» because couldn't create all companies"))
                skipped += 1
                continue

            language = None
            if movie['original_language']:
                language, created = self.get_or_create_language(movie['original_language'])
                if created:
                    existing_languages.add(movie['original_language'])

            collection = None
            if movie['belongs_to_collection']:
                collection, _ = models.Collection.objects.get_or_create(
                    tmdb_id=movie['belongs_to_collection']['id'],
                    defaults={'name': movie['belongs_to_collection']['name']},
                )

            movie_obj, created = models.Movie.objects.update_or_create(
                tmdb_id=movie['id'],
                defaults={
                    'title': movie['title'],
                    'imdb_id': movie['imdb_id'] or '',
                    'release_date': date.fromisoformat(movie['release_date']) if movie['release_date'] else None,
                    'original_title': movie['original_title'] or '',
                    'original_language': language,
                    'overview': movie['overview'] or '',
                    'tagline': movie['tagline'] or '',
                    'collection': collection,
                    'poster_path': movie['poster_path'] or '',
                    'backdrop_path': movie['backdrop_path'] or '',
                    'status': movie['status'] or '',
                    'budget': movie['budget'],
                    'revenue': movie['revenue'],
                    'runtime': movie['runtime'],
                },
            )

            # Update many to many fields
            # Genres
            genre_ids = []
            for genre in movie['genres']:
                if genre['id'] not in existing_genres:
                    models.Genre.objects.create(tmdb_id=genre['id'], name=genre['name'])
                    existing_genres.add(genre['id'])

                genre_ids.append(genre['id'])

            movie_obj.genres.set(genre_ids)

            # Spoken languages
            spoken_language_codes = []
            for spoken_language in movie['spoken_languages']:
                if spoken_language['iso_639_1'] not in existing_languages:
                    models.Language.objects.create(code=spoken_language['iso_639_1'], name=spoken_language['english_name'])
                    existing_languages.add(spoken_language['iso_639_1'])

                spoken_language_codes.append(spoken_language['iso_639_1'])

            movie_obj.spoken_languages.set(spoken_language_codes)

            # Origin countries
            origin_country_codes = []
            for origin_country_code in movie['origin_country']:
                if origin_country_code not in existing_countries:
                    models.Country.objects.create(code=origin_country_code, name='unknown')
                    existing_countries.add(origin_country_code)

                origin_country_codes.append(origin_country_code)

            movie_obj.origin_country.set(origin_country_codes)

            # Production companies
            movie_obj.production_companies.set(company_ids)

            # Production countries
            prod_countries_codes = []
            for prod_country in movie['production_countries']:
                if prod_country['iso_3166_1'] not in existing_countries:
                    models.Country.objects.create(code=prod_country['iso_3166_1'], name=prod_country['name'])
                    existing_countries.add(prod_country['iso_3166_1'])

                prod_countries_codes.append(prod_country['iso_3166_1'])

            movie_obj.production_countries.set(prod_countries_codes)

            # Update cast
            models.MovieCast.objects.filter(movie=movie_obj).delete()

            for cast_member in cast:
                person = models.Person.objects.get(tmdb_id=cast_member['id'])
                models.MovieCast.objects.create(
                    movie=movie_obj,
                    person=person,
                    character=cast_member['character'] or '',
                    order=cast_member['order'],
                )

            # Update crew
            models.MovieCrew.objects.filter(movie=movie_obj).delete()

            for crew_member in crew:
                person = models.Person.objects.get(tmdb_id=crew_member['id'])
                models.MovieCrew.objects.create(
                    movie=movie_obj,
                    person=person,
                    department=crew_member['department'] or '',
                    job=crew_member['job'] or '',
                )

            if created:
                count_created += 1
            else:
                count_updated += 1

        self.stdout.write(
            self.style.SUCCESS(f'Movies proccessed: {len(movies)} (created: {count_created}, updated: {count_updated}, skipped: {skipped})')
        )
        self.stdout.write(self.style.SUCCESS(f'Created persons: {total_created_persons}'))
        self.stdout.write(self.style.SUCCESS(f'Created companies: {n_created_companies}'))
        if not_fetched_movie_ids:
            self.stdout.write(
                self.style.WARNING(
                    f"Couldn't update/create: {len(not_fetched_movie_ids)} (IDs: {', '.join(map(str, not_fetched_movie_ids))})"
                )
            )

    def get_or_create_language(self, code: str, name: str = 'unknown') -> tuple[str, bool]:
        created = False
        if code not in self.language_cache:
            self.language_cache[code], created = models.Language.objects.get_or_create(code=code, defaults={'name': name})
        return self.language_cache[code], created

    def create_missing_companies(self, movies: list[dict]) -> tuple[int, list[int] | None]:
        company_ids = {company['id'] for movie in movies for company in movie['production_companies']}
        existing_ids = set(models.ProductionCompany.objects.filter(tmdb_id__in=company_ids).values_list('tmdb_id', flat=True))
        missing_ids = {id for id in company_ids if id not in existing_ids}

        if not missing_ids:
            return 0, None

        companies, not_fetched = asyncTMDB().batch_fetch_companies_by_id(missing_ids)

        for company in companies:
            country = None
            if company['origin_country']:
                country, _ = models.Country.objects.get_or_create(code=company['origin_country'], defaults={'name': 'unknown'})

            models.ProductionCompany.objects.update_or_create(
                tmdb_id=company['id'],
                defaults={
                    'name': company['name'],
                    'logo_path': company['logo_path'] or '',
                    'origin_country': country,
                },
            )

        return len(companies), not_fetched

    def create_missing_persons(self, credits: list[dict]) -> tuple[int, bool]:
        GENDERS = {0: '', 1: 'F', 2: 'M', 3: 'NB'}

        cast_ids = [cast_member['id'] for cast_member in credits]
        existing_ids = set(models.Person.objects.filter(tmdb_id__in=cast_ids).values_list('tmdb_id', flat=True))
        missing_ids = {id for id in cast_ids if id not in existing_ids}

        if not missing_ids:
            return 0, False

        persons, not_fetched = asyncTMDB().batch_fetch_persons_by_id(missing_ids)

        for person in persons:
            models.Person.objects.update_or_create(
                tmdb_id=person['id'],
                defaults={
                    'name': person['name'],
                    'imdb_id': person['imdb_id'] or '',
                    'known_for_department': person['known_for_department'] or '',
                    'biography': person['biography'] or '',
                    'place_of_birth': person['place_of_birth'] or '',
                    'gender': GENDERS[person['gender']],
                    'birthday': date.fromisoformat(person['birthday']) if person['birthday'] else None,
                    'deathday': date.fromisoformat(person['deathday']) if person['deathday'] else None,
                    'profile_path': person['profile_path'] or '',
                    'tmdb_popularity': person['popularity'],
                },
            )

        return len(persons), bool(not_fetched)
