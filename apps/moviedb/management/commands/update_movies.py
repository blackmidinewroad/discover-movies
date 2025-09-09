import logging
from datetime import date

from django.core.management.base import BaseCommand, CommandError

from apps.moviedb import models
from apps.moviedb.integrations.tmdb.api import asyncTMDB
from apps.moviedb.integrations.tmdb.id_exports import IDExport
from apps.services.utils import GENDERS, STATUS_MAP, runtime

logger = logging.getLogger('moviedb')


class Command(BaseCommand):
    help = 'Update movie table'

    def add_arguments(self, parser):
        parser.add_argument(
            'operation',
            type=str,
            choices=['update_changed', 'daily_export', 'add_top_rated', 'specific_ids'],
            help='Operation to perform: update_changed, daily_export, add_top_rated or specific_ids',
        )

        parser.add_argument(
            '--ids',
            type=int,
            default=None,
            nargs='*',
            help='TMDB IDs of movies to add (required for specific_ids operation).',
        )

        parser.add_argument(
            '--date',
            type=str,
            default=None,
            help='Date of the export file in "MM_DD_YYYY" format (only works with daily_export operation).',
        )

        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help=(
                'Changes made in the past N days (only works with update_changed operation).'
                'By default changes will be fetched for the past 24 hours.'
            ),
        )

        parser.add_argument(
            '--batch_size',
            type=int,
            default=100,
            help='Number of movies to fetch per batch. Defaults to 100.',
        )

        parser.add_argument(
            '--language',
            type=str,
            default='en-US',
            help='Locale (ISO 639-1-ISO 3166-1) code (e.g. en-US, fr-CA, de-DE). Defaults to "en-US".',
        )

        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of movies updated/created.',
        )

        parser.add_argument(
            '--sort_by_popularity',
            action='store_true',
            default=False,
            help='Sort IDs by popularity (only works with daily_export).',
        )

    @runtime
    def handle(self, *args, **options):
        operation = options['operation']
        ids = options['ids']
        published_date = options['date']
        days = options['days']
        batch_size = options['batch_size']
        language = options['language']
        limit = options['limit']
        sort_by_popularity = options['sort_by_popularity']

        is_update = operation == 'update_changed'

        tmdb = asyncTMDB()

        match operation:
            case 'update_changed':
                movie_ids, earliest_date = tmdb.fetch_changed_ids('movie', days=days)

                # Get movie IDs that were last updated before the changes earliest date
                movie_ids = list(
                    models.Movie.objects.filter(
                        last_update__lt=earliest_date,
                        tmdb_id__in=movie_ids,
                        removed_from_tmdb=False,
                    ).values_list('tmdb_id', flat=True)
                )
            case 'daily_export':
                existing_ids = set(models.Movie.objects.only('tmdb_id').values_list('tmdb_id', flat=True))
                movie_ids = IDExport().fetch_ids('movie', published_date=published_date, sort_by_popularity=sort_by_popularity)
                if movie_ids is None:
                    return
            case 'add_top_rated':
                existing_ids = set(models.Movie.objects.only('tmdb_id').values_list('tmdb_id', flat=True))
                movie_ids = tmdb.fetch_top_rated_movie_ids(last_page=500)
            case 'specific_ids':
                if ids is None:
                    raise CommandError('Must provide --ids using specific_ids operation')
                existing_ids = set(models.Movie.objects.filter(tmdb_id__in=ids).values_list('tmdb_id', flat=True))
                movie_ids = ids
            case _:
                raise CommandError("Invalid operation. Choose from 'update_changed', 'daily_export', 'add_top_rated', 'specific_ids'")

        if not is_update:
            movie_ids = [id for id in movie_ids if id not in existing_ids]

        if limit is not None:
            movie_ids = movie_ids[:limit]

        logger.info('Starting to fetch %s movies...', len(movie_ids))

        movies, not_fetched_movie_ids = tmdb.fetch_movies_by_id(
            movie_ids,
            batch_size=batch_size,
            language=language,
            append_to_response=['credits'],
        )

        # Existing countreis/languages/genres in db
        self.countries = {c.code for c in models.Country.objects.all()}
        languages = {l.code for l in models.Language.objects.all()}
        genres = {g.tmdb_id for g in models.Genre.objects.all()}

        # Create missing people, companies and collections
        credits = []
        companies = []
        collections = []
        for movie_data in movies:
            credits_data = movie_data.get('credits', {})
            credits.extend(credits_data.get('cast', []) + credits_data.get('crew', []))
            companies.extend(movie_data.get('production_companies', []))
            collection = movie_data.get('belongs_to_collection', {})
            if collection:
                collections.append(collection)

        n_created_people, not_fetched_person_ids = self.create_missing_people(tmdb, credits, batch_size=batch_size)
        n_created_companies, n_created_countries = self.create_missing_companies(companies)
        n_created_collections = self.create_missing_collections(collections)

        # Counters for newly created objects
        created_counter = {
            'people': n_created_people,
            'companies': n_created_companies,
            'collections': n_created_collections,
            'countries': n_created_countries,
            'languages': 0,
            'genres': 0,
        }

        # Keep track of new slugs to create unique slugs
        new_slugs = set()

        # Skipped movies counter
        skipped = 0

        # Fields to update in movie table
        update_fields = [
            'title',
            'imdb_id',
            'release_date',
            'original_title',
            'original_language',
            'overview',
            'tagline',
            'collection',
            'poster_path',
            'backdrop_path',
            'status',
            'budget',
            'revenue',
            'runtime',
            'documentary',
            'tv_movie',
            'short',
            'last_update',
            'tmdb_popularity',
        ]

        # Add fields that should be set only when entry is created
        if not is_update:
            update_fields.extend(['slug', 'created_at', 'adult'])

        # Links to update many to many fields
        genre_links = []
        spoken_languages_links = []
        origin_country_links = []
        prod_countries_links = []
        prod_companies_links = []
        cast_relations = []
        crew_relations = []

        # Store movie IDs and objects for bulk_create {movie_id: movie_obj}
        movie_map = {}

        logger.info('Starting to process movies...')

        for movie_data in movies:
            # If couldn't create needed people from the movie - skip movie
            credits = movie_data.get('credits', {})
            cast_data = credits.get('cast', [])
            crew_data = credits.get('crew', [])
            cast_ids = {cast['id'] for cast in cast_data}
            crew_ids = {crew['id'] for crew in crew_data}
            credit_ids = cast_ids | crew_ids
            if not_fetched_person_ids and not credit_ids.isdisjoint(not_fetched_person_ids):
                logger.warning("Skipped «%s» because couldn't create all needed people.", movie_data['title'])
                skipped += 1
                continue

            origin_language_code = movie_data.get('original_language', '')
            if origin_language_code and origin_language_code not in languages:
                models.Language.objects.create(code=origin_language_code, name='unknown')
                languages.add(origin_language_code)
                created_counter['languages'] += 1

            collection = movie_data.get('belongs_to_collection', {})
            collection_id = collection['id'] if collection else None

            release_date = None
            if movie_data.get('release_date'):
                try:
                    release_date = date.fromisoformat(movie_data.get('release_date'))
                except ValueError:
                    pass

            movie_id = movie_data['id']

            movie = models.Movie(
                tmdb_id=movie_id,
                title=movie_data['title'],
                imdb_id=movie_data.get('imdb_id') or '',
                release_date=release_date,
                original_title=movie_data.get('original_title') or '',
                original_language_id=origin_language_code or None,
                overview=movie_data.get('overview') or '',
                tagline=movie_data.get('tagline') or '',
                collection_id=collection_id,
                poster_path=movie_data.get('poster_path') or '',
                backdrop_path=movie_data.get('backdrop_path') or '',
                status=STATUS_MAP[movie_data.get('status', '')],
                budget=movie_data.get('budget', 0),
                revenue=movie_data.get('revenue', 0),
                runtime=movie_data.get('runtime', 0),
                tmdb_popularity=movie_data.get('popularity', 0),
                adult=movie_data.get('adult', False),
            )

            # Create links for many to many fields
            # Genres
            genre_ids = []
            for genre_data in movie_data.get('genres', []):
                genre_id = genre_data['id']
                genre_ids.append(genre_id)
                if genre_id not in genres:
                    models.Genre.objects.create(tmdb_id=genre_id, name=genre_data['name'])
                    genres.add(genre_id)
                    created_counter['genres'] += 1

                genre_links.append(models.Movie.genres.through(movie_id=movie_id, genre_id=genre_id))

            # Spoken languages
            for spoken_language_data in movie_data.get('spoken_languages', []):
                spoken_language_code = spoken_language_data['iso_639_1']
                if spoken_language_code not in languages:
                    models.Language.objects.create(code=spoken_language_code, name=spoken_language_data['english_name'])
                    languages.add(spoken_language_code)
                    created_counter['languages'] += 1

                spoken_languages_links.append(models.Movie.spoken_languages.through(movie_id=movie_id, language_id=spoken_language_code))

            # Origin countries
            for origin_country_code in movie_data.get('origin_country', []):
                if origin_country_code not in self.countries:
                    models.Country.objects.create(code=origin_country_code, name='unknown')
                    self.countries.add(origin_country_code)
                    created_counter['countries'] += 1

                origin_country_links.append(models.Movie.origin_country.through(movie_id=movie_id, country_id=origin_country_code))

            # Production countries
            for prod_country in movie_data.get('production_countries', []):
                prod_country_code = prod_country['iso_3166_1']
                if prod_country_code not in self.countries:
                    models.Country.objects.create(code=prod_country_code, name=prod_country['name'])
                    self.countries.add(prod_country_code)
                    created_counter['countries'] += 1

                prod_countries_links.append(models.Movie.production_countries.through(movie_id=movie_id, country_id=prod_country_code))

            # Production companies
            company_ids = {company['id'] for company in movie_data.get('production_companies', [])}
            for prod_company_id in company_ids:
                prod_companies_links.append(
                    models.Movie.production_companies.through(movie_id=movie_id, productioncompany_id=prod_company_id)
                )

            # Cast
            for cast_member in cast_data:
                cast_relations.append(
                    models.MovieCast(
                        movie_id=movie_id,
                        person_id=cast_member['id'],
                        character=cast_member.get('character') or '',
                        order=cast_member.get('order', 0),
                    )
                )

            # Crew
            for crew_member in crew_data:
                crew_relations.append(
                    models.MovieCrew(
                        movie_id=movie_id,
                        person_id=crew_member['id'],
                        department=crew_member.get('department') or '',
                        job=crew_member.get('job') or '',
                    )
                )

            # Create new slug if not updating changes
            if not is_update:
                movie.set_slug(new_slugs)
                new_slugs.add(movie.slug)

            movie.categorize(genre_ids)
            movie.update_last_modified()
            movie_map[movie_id] = movie

        models.Movie.objects.bulk_create(
            tuple(movie_map.values()),
            update_conflicts=True,
            update_fields=update_fields,
            unique_fields=('tmdb_id',),
        )

        # IDs of created movies
        created_movie_ids = set(movie_map)

        # Delete existing links
        models.Movie.genres.through.objects.filter(movie_id__in=created_movie_ids).delete()
        models.Movie.spoken_languages.through.objects.filter(movie_id__in=created_movie_ids).delete()
        models.Movie.origin_country.through.objects.filter(movie_id__in=created_movie_ids).delete()
        models.Movie.production_countries.through.objects.filter(movie_id__in=created_movie_ids).delete()
        models.Movie.production_companies.through.objects.filter(movie_id__in=created_movie_ids).delete()
        models.MovieCast.objects.filter(movie_id__in=created_movie_ids).delete()
        models.MovieCrew.objects.filter(movie_id__in=created_movie_ids).delete()

        # Create new relations in bulk
        models.Movie.genres.through.objects.bulk_create(genre_links, ignore_conflicts=True)
        models.Movie.spoken_languages.through.objects.bulk_create(spoken_languages_links, ignore_conflicts=True)
        models.Movie.origin_country.through.objects.bulk_create(origin_country_links, ignore_conflicts=True)
        models.Movie.production_countries.through.objects.bulk_create(prod_countries_links, ignore_conflicts=True)
        models.Movie.production_companies.through.objects.bulk_create(prod_companies_links, ignore_conflicts=True)
        models.MovieCast.objects.bulk_create(cast_relations, ignore_conflicts=True)
        models.MovieCrew.objects.bulk_create(crew_relations, ignore_conflicts=True)

        # Update removed_from_tmdb field
        removed_ids = [id for id in not_fetched_movie_ids if id]
        missing_movie_ids = [id for id in not_fetched_movie_ids if not id]
        movies_to_remove = models.Movie.objects.filter(tmdb_id__in=removed_ids)
        removed_objs = []

        for removed_movie in movies_to_remove:
            removed_movie.removed_from_tmdb = True
            removed_objs.append(removed_movie)

        models.Movie.objects.bulk_update(removed_objs, fields=['removed_from_tmdb'])

        logger.info('Movies processed: %s (skipped: %s).', len(movies), skipped)
        if removed_objs:
            logger.info('Updated removed: %s.', len(removed_objs))
        for obj_type, counter in created_counter.items():
            if counter:
                logger.info('Created %s: %s.', obj_type, counter)
        if missing_movie_ids:
            logger.warning("Couldn't update/create: %s.", len(missing_movie_ids))

    def create_missing_people(self, tmdb_instance: asyncTMDB, credits: list[dict], batch_size: int) -> tuple[int, list[int] | None]:
        """Add to db missing people from credits so all movies can have full cast and crew.

        Args:
            tmdb_instance (asyncTMDB): instance of the async TMDB API wrapper.
            credits (list[dict]): list of credits from TMDB from wich to take people.
            batch_size (int): number of people to fetch per batch.

        Returns:
            tuple[int, list[int] | None]: number of created people and list of IDs of people that couldn't be created
                (or None if people were created).
        """

        person_ids = [credit_member['id'] for credit_member in credits]
        existing_ids = set(models.Person.objects.filter(tmdb_id__in=person_ids).values_list('tmdb_id', flat=True))
        missing_ids = {id for id in person_ids if id not in existing_ids}

        if not missing_ids:
            logger.info('There are no missing people.')
            return 0, None

        logger.info('Starting to process %s missing people...', len(missing_ids))

        people, not_fetched = tmdb_instance.fetch_people_by_id(missing_ids, batch_size=batch_size)
        person_objs = []
        new_slugs = set()

        for person_data in people:
            birthday = deathday = None
            try:
                if person_data.get('birthday'):
                    birthday = date.fromisoformat(person_data.get('birthday'))
                if person_data.get('deathday'):
                    deathday = date.fromisoformat(person_data.get('deathday'))
            except ValueError:
                pass

            person = models.Person(
                tmdb_id=person_data['id'],
                name=person_data['name'],
                imdb_id=person_data.get('imdb_id') or '',
                known_for_department=person_data.get('known_for_department') or '',
                biography=person_data.get('biography') or '',
                place_of_birth=person_data.get('place_of_birth') or '',
                gender=GENDERS[person_data.get('gender', 0)],
                birthday=birthday,
                deathday=deathday,
                profile_path=person_data.get('profile_path') or '',
                tmdb_popularity=person_data.get('popularity', 0),
                adult=person_data.get('adult', False),
            )
            person.set_slug(new_slugs)
            new_slugs.add(person.slug)
            person.update_last_modified()
            person_objs.append(person)

        models.Person.objects.bulk_create(
            person_objs,
            update_conflicts=True,
            update_fields=(
                'name',
                'slug',
                'imdb_id',
                'known_for_department',
                'biography',
                'place_of_birth',
                'gender',
                'birthday',
                'deathday',
                'profile_path',
                'tmdb_popularity',
                'last_update',
                'adult',
            ),
            unique_fields=('tmdb_id',),
        )

        return len(people), not_fetched

    def create_missing_companies(self, companies: list[dict]) -> tuple[int, int]:
        """Create missing production companies so all movies can have full company lists.

        Args:
            companies (list[dict]): list of companies to create.

        Returns:
            tuple[int, int]: number of created companies and number of created countries (that were needed to ceate companies).
        """

        # Get rid of duplicates
        unique_companies = {company_data['id']: company_data for company_data in companies}

        existing_ids = set(
            models.ProductionCompany.objects.filter(tmdb_id__in=set(unique_companies.keys())).values_list('tmdb_id', flat=True)
        )
        missing_companies = [company for id, company in unique_companies.items() if id not in existing_ids]

        if not missing_companies:
            return 0, 0

        company_objs = []
        new_slugs = set()
        n_created_countries = 0

        for company_data in missing_companies:
            origin_country_code = company_data.get('origin_country')
            if origin_country_code and origin_country_code not in self.countries:
                models.Country.objects.create(code=origin_country_code, name='unknown')
                self.countries.add(origin_country_code)
                n_created_countries += 1

            company = models.ProductionCompany(
                tmdb_id=company_data['id'],
                name=company_data['name'],
                logo_path=company_data.get('logo_path') or '',
                origin_country_id=origin_country_code or None,
            )
            company.set_slug(new_slugs)
            company_objs.append(company)
            new_slugs.add(company.slug)

        models.ProductionCompany.objects.bulk_create(
            company_objs,
            update_conflicts=True,
            update_fields=('name', 'slug', 'logo_path', 'origin_country'),
            unique_fields=('tmdb_id',),
        )

        return len(missing_companies), n_created_countries

    def create_missing_collections(self, collections: list[dict]) -> int:
        """Create missing collections so all movies can have valid collections.

        Args:
            collections (list[dict]): list of collections to create.

        Returns:
            int: number of created collections.
        """

        # Get rid of duplicates
        unique_collections = {collection_data['id']: collection_data for collection_data in collections}

        existing_ids = set(models.Collection.objects.filter(tmdb_id__in=set(unique_collections.keys())).values_list('tmdb_id', flat=True))
        missing_collections = [collection for id, collection in unique_collections.items() if id not in existing_ids]

        if not missing_collections:
            return 0

        collection_objs = []
        new_slugs = set()

        for collection_data in missing_collections:
            collection = models.Collection(
                tmdb_id=collection_data['id'],
                name=collection_data['name'],
                overview='',
                poster_path=collection_data.get('poster_path') or '',
                backdrop_path=collection_data.get('backdrop_path') or '',
            )
            collection.set_slug(new_slugs)
            collection_objs.append(collection)
            new_slugs.add(collection.slug)

        models.Collection.objects.bulk_create(
            collection_objs,
            update_conflicts=True,
            update_fields=('name', 'slug', 'poster_path', 'backdrop_path'),
            unique_fields=('tmdb_id',),
        )

        return len(missing_collections)
