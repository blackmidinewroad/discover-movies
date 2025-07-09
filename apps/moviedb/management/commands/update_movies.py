from datetime import date

from django.core.management.base import BaseCommand

from apps.moviedb import models
from apps.moviedb.integrations.tmdb.api import asyncTMDB
from apps.moviedb.integrations.tmdb.id_exports import IDExport


class Command(BaseCommand):
    help = 'Update movie table'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            default=None,
            help='Date of the export file in "MM_DD_YYYY" format.',
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
        sort_by_popularity = kwargs['sort_by_popularity']

        # Existing countreis/languages/genres in db
        self.countries = {c.code for c in models.Country.objects.all()}
        languages = {l.code for l in models.Language.objects.all()}
        genres = {g.tmdb_id for g in models.Genre.objects.all()}

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
            existing_ids = set(models.Movie.objects.only('tmdb_id').values_list('tmdb_id', flat=True))
            movie_ids = [id for id in movie_ids if id not in existing_ids]

        movies, not_fetched_movie_ids = asyncTMDB().batch_fetch_movies_by_id(
            movie_ids[:limit],
            batch_size=batch_size,
            language=language,
            append_to_response=['credits'],
        )

        n_created_companies, not_fetched_company_ids = self.create_missing_companies(movies)

        # Keep track of new slugs to create unique slugs
        new_slugs = set()

        skipped = total_created_persons = 0

        # Links to update many to many fields
        genre_links = []
        spoken_languages_links = []
        origin_country_links = []
        prod_countries_links = []
        prod_companies_links = []
        cast_relations = []
        crew_relations = []
        directors_links = []

        # Store movie IDs and objects for bulk_create ({'movie_id': movie_obj})
        movie_map = {}

        for movie_data in movies:
            # Create missing persons
            n_created_persons, is_missing_persons = self.create_missing_persons(
                movie_data['credits']['cast'] + movie_data['credits']['crew']
            )

            total_created_persons += n_created_persons

            # If couldn't create all people from the movie - skip movie
            if is_missing_persons:
                self.stdout.write(self.style.WARNING(f"Skipped «{movie_data['title']}» because couldn't create all people"))
                skipped += 1
                continue

            # If couldn't create needed production companies - skip movie
            company_ids = [company['id'] for company in movie_data['production_companies']]
            if not_fetched_company_ids and (set(not_fetched_company_ids) & set(company_ids)):
                self.stdout.write(self.style.WARNING(f"Skipped «{movie_data['title']}» because couldn't create all companies"))
                skipped += 1
                continue

            origin_language_code = movie_data['original_language']
            if origin_language_code and origin_language_code not in languages:
                models.Language.objects.create(code=origin_language_code, name='unknown')
                languages.add(origin_language_code)

            collection = None
            if movie_data['belongs_to_collection']:
                collection, _ = models.Collection.objects.get_or_create(
                    tmdb_id=movie_data['belongs_to_collection']['id'],
                    defaults={'name': movie_data['belongs_to_collection']['name']},
                )

            movie_id = movie_data['id']

            movie = models.Movie(
                tmdb_id=movie_id,
                title=movie_data['title'],
                imdb_id=movie_data['imdb_id'] or '',
                release_date=date.fromisoformat(movie_data['release_date']) if movie_data['release_date'] else None,
                original_title=movie_data['original_title'] or '',
                original_language_id=origin_language_code or None,
                overview=movie_data['overview'] or '',
                tagline=movie_data['tagline'] or '',
                collection=collection,
                poster_path=movie_data['poster_path'] or '',
                backdrop_path=movie_data['backdrop_path'] or '',
                status=movie_data['status'] or '',
                budget=movie_data['budget'],
                revenue=movie_data['revenue'],
                runtime=movie_data['runtime'],
            )
            movie.set_slug(movie.title, new_slugs)
            movie.set_flags()
            new_slugs.add(movie.slug)

            movie_map[movie_id] = movie

            # Create links for many to many fields
            # Genres
            for genre_data in movie_data['genres']:
                genre_id = genre_data['id']
                if genre_id not in genres:
                    models.Genre.objects.create(tmdb_id=genre_id, name=genre_data['name'])
                    genres.add(genre_id)

                genre_links.append(models.Movie.genres.through(movie_id=movie_id, genre_id=genre_id))

            # Spoken languages
            for spoken_language_data in movie_data['spoken_languages']:
                spoken_language_code = spoken_language_data['iso_639_1']
                if spoken_language_code not in languages:
                    models.Language.objects.create(code=spoken_language_code, name=spoken_language_data['english_name'])
                    languages.add(spoken_language_code)

                spoken_languages_links.append(models.Movie.spoken_languages.through(movie_id=movie_id, language_id=spoken_language_code))

            # Origin countries
            for origin_country_code in movie_data['origin_country']:
                if origin_country_code not in self.countries:
                    models.Country.objects.create(code=origin_country_code, name='unknown')
                    self.countries.add(origin_country_code)

                origin_country_links.append(models.Movie.origin_country.through(movie_id=movie_id, country_id=origin_country_code))

            # Production countries
            for prod_country in movie_data['production_countries']:
                prod_country_code = prod_country['iso_3166_1']
                if prod_country_code not in self.countries:
                    models.Country.objects.create(code=prod_country_code, name=prod_country['name'])
                    self.countries.add(prod_country_code)

                prod_countries_links.append(models.Movie.production_countries.through(movie_id=movie_id, country_id=prod_country_code))

            # Production companies
            for prod_company in movie_data['production_companies']:
                prod_companies_links.append(
                    models.Movie.production_companies.through(movie_id=movie_id, productioncompany_id=prod_company['id'])
                )

            # Cast
            for cast_member in movie_data['credits']['cast']:
                cast_relations.append(
                    models.MovieCast(
                        movie_id=movie_id,
                        person_id=cast_member['id'],
                        character=cast_member['character'] or '',
                        order=cast_member['order'],
                    )
                )

            # Crew and directors
            for crew_member in movie_data['credits']['crew']:
                if crew_member['job'] == 'Director':
                    directors_links.append(models.Movie.directors.through(movie_id=movie_id, person_id=crew_member['id']))

                crew_relations.append(
                    models.MovieCrew(
                        movie_id=movie_id,
                        person_id=crew_member['id'],
                        department=crew_member['department'] or '',
                        job=crew_member['job'] or '',
                    )
                )

        models.Movie.objects.bulk_create(
            tuple(movie_map.values()),
            update_conflicts=True,
            update_fields=(
                'title',
                'slug',
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
            ),
            unique_fields=('tmdb_id',),
        )

        # IDs of created movies
        movie_ids = set(movie_map)

        # Delete existing links
        models.Movie.genres.through.objects.filter(movie_id__in=movie_ids).delete()
        models.Movie.spoken_languages.through.objects.filter(movie_id__in=movie_ids).delete()
        models.Movie.origin_country.through.objects.filter(movie_id__in=movie_ids).delete()
        models.Movie.production_countries.through.objects.filter(movie_id__in=movie_ids).delete()
        models.Movie.production_companies.through.objects.filter(movie_id__in=movie_ids).delete()
        models.Movie.directors.through.objects.filter(movie_id__in=movie_ids).delete()
        models.MovieCast.objects.filter(movie_id__in=movie_ids).delete()
        models.MovieCrew.objects.filter(movie_id__in=movie_ids).delete()

        # Create new relations in bulk
        models.Movie.genres.through.objects.bulk_create(genre_links, ignore_conflicts=True)
        models.Movie.spoken_languages.through.objects.bulk_create(spoken_languages_links, ignore_conflicts=True)
        models.Movie.origin_country.through.objects.bulk_create(origin_country_links, ignore_conflicts=True)
        models.Movie.production_countries.through.objects.bulk_create(prod_countries_links, ignore_conflicts=True)
        models.Movie.production_companies.through.objects.bulk_create(prod_companies_links, ignore_conflicts=True)
        models.Movie.directors.through.objects.bulk_create(directors_links, ignore_conflicts=True)
        models.MovieCast.objects.bulk_create(cast_relations, ignore_conflicts=True)
        models.MovieCrew.objects.bulk_create(crew_relations, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(f'Movies processed: {len(movies)} (skipped: {skipped})'))
        self.stdout.write(self.style.SUCCESS(f'Created persons: {total_created_persons}'))
        self.stdout.write(self.style.SUCCESS(f'Created companies: {n_created_companies}'))
        if not_fetched_movie_ids:
            self.stdout.write(
                self.style.WARNING(
                    f"Couldn't update/create: {len(not_fetched_movie_ids)} (IDs: {', '.join(map(str, not_fetched_movie_ids))})"
                )
            )

    def create_missing_companies(self, movies: list[dict]) -> tuple[int, list[int] | None]:
        company_ids = {company['id'] for movie in movies for company in movie['production_companies']}
        existing_ids = set(models.ProductionCompany.objects.filter(tmdb_id__in=company_ids).values_list('tmdb_id', flat=True))
        missing_ids = {id for id in company_ids if id not in existing_ids}

        if not missing_ids:
            return 0, None

        companies, not_fetched = asyncTMDB().batch_fetch_companies_by_id(missing_ids)
        company_objs = []
        new_slugs = set()

        for company_data in companies:
            origin_country_code = company_data['origin_country']
            if origin_country_code and origin_country_code not in self.countries:
                models.Country.objects.create(code=origin_country_code, name='unknown')
                self.countries.add(origin_country_code)

            company = models.ProductionCompany(
                tmdb_id=company_data['id'],
                name=company_data['name'],
                logo_path=company_data['logo_path'] or '',
                origin_country_id=origin_country_code or None,
            )
            company.set_slug(company.name, new_slugs)
            company_objs.append(company)
            new_slugs.add(company.slug)

        models.ProductionCompany.objects.bulk_create(
            company_objs,
            update_conflicts=True,
            update_fields=('name', 'slug', 'logo_path', 'origin_country'),
            unique_fields=('tmdb_id',),
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
        person_objs = []
        new_slugs = set()

        for person_data in persons:
            person = models.Person(
                tmdb_id=person_data['id'],
                name=person_data['name'],
                imdb_id=person_data['imdb_id'] or '',
                known_for_department=person_data['known_for_department'] or '',
                biography=person_data['biography'] or '',
                place_of_birth=person_data['place_of_birth'] or '',
                gender=GENDERS[person_data['gender']],
                birthday=date.fromisoformat(person_data['birthday']) if person_data['birthday'] else None,
                deathday=date.fromisoformat(person_data['deathday']) if person_data['deathday'] else None,
                profile_path=person_data['profile_path'] or '',
                tmdb_popularity=person_data['popularity'],
            )
            person.set_slug(person.name, new_slugs)
            person_objs.append(person)
            new_slugs.add(person.slug)

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
            ),
            unique_fields=('tmdb_id',),
        )

        return len(persons), bool(not_fetched)
