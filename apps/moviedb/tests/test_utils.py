from uuid import UUID

from django.test import RequestFactory, TestCase
from django.utils import timezone

from apps.moviedb.models import Country, Movie, MovieCrew, Person
from apps.services.utils import get_base_query, get_crew_map, unique_slugify


class UniqueSlugifyTests(TestCase):
    """Tests for the unique_slugify function."""

    def test_normal_slug_generation(self):
        country = Country(code='CA', name='Canada')
        slug = unique_slugify(country, 'Canada')
        self.assertEqual(slug, 'canada')

    def test_duplicate_slug(self):
        Country.objects.create(code='US', name='United States')
        country2 = Country(code='UK', name='United States')
        slug = unique_slugify(country2, 'United States')
        self.assertEqual(slug, 'united-states-1')

    def test_multiple_duplicate_slugs(self):
        Country.objects.create(code='US', name='United States')
        Country.objects.create(code='UK', name='United States')
        country3 = Country(code='FR', name='United States')
        slug = unique_slugify(country3, 'United States')
        self.assertEqual(slug, 'united-states-2')

    def test_special_characters(self):
        country = Country(code='FR', name='France & Germany')
        slug = unique_slugify(country, 'France & Germany')
        self.assertEqual(slug, 'france-germany')

    def test_non_ascii_characters(self):
        country = Country(code='RU', name='Россия')
        slug = unique_slugify(country, 'Россия')
        self.assertEqual(slug, 'rossiia')

    def test_empty_value(self):
        country = Country(code='XX', name='')
        slug = unique_slugify(country, '')
        try:
            UUID(slug)
            is_uuid = True
        except ValueError:
            is_uuid = False
        self.assertTrue(is_uuid)
        self.assertEqual(len(slug), 36)

    def test_long_string(self):
        long_name = 'A' * 100
        country = Country(code='XX', name=long_name)
        slug = unique_slugify(country, long_name)
        self.assertEqual(slug, 'a' * 56)

    def test_cur_bulk_slugs(self):
        country = Country(code='CA', name='Canada')
        slug = unique_slugify(country, 'Canada', cur_bulk_slugs={'canada'})
        self.assertEqual(slug, 'canada-1')


class GetBaseQueryTests(TestCase):
    """Tests for the get_base_query function."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_get_base_query_with_query(self):
        request = self.factory.get('/?query=star+wars&sort=popularity')
        base_query = get_base_query(request)
        self.assertEqual(base_query, 'query=star+wars')

    def test_get_base_query_without_query(self):
        request = self.factory.get('/?sort=popularity')
        base_query = get_base_query(request)
        self.assertEqual(base_query, '')

    def test_get_base_query_empty(self):
        request = self.factory.get('/')
        base_query = get_base_query(request)
        self.assertEqual(base_query, '')

    def test_get_base_query_special_characters(self):
        request = self.factory.get('/?query=star+wars%21')
        base_query = get_base_query(request)
        self.assertEqual(base_query, 'query=star+wars%21')


class GetCrewMapTests(TestCase):
    """Tests for the get_crew_map function."""

    def setUp(self):
        self.movie = Movie.objects.create(
            tmdb_id=1, title='Test Movie', release_date=timezone.now().date(), tmdb_popularity=50.0, runtime=120
        )
        self.person = Person.objects.create(tmdb_id=1, name='John Doe')
        self.crew_dicts = [
            {'id': 1, 'obj': MovieCrew(movie=self.movie, person=self.person, department='Directing', job='Director')},
            {'id': 2, 'obj': MovieCrew(movie=self.movie, person=self.person, department='Writing', job='Screenplay')},
            {'id': 3, 'obj': MovieCrew(movie=self.movie, person=self.person, department='Production', job='Producer')},
        ]

    def test_get_crew_map_basic(self):
        crew_map = get_crew_map(self.crew_dicts)
        self.assertIn('Director', crew_map)
        self.assertIn(1, crew_map['Director']['objs'])
        self.assertIn('Writer', crew_map)
        self.assertIn(2, crew_map['Writer']['objs'])
        self.assertIn('Producer', crew_map)
        self.assertIn(3, crew_map['Producer']['objs'])

    def test_get_crew_map_empty_input(self):
        crew_map = get_crew_map([])
        for job, job_map in crew_map.items():
            self.assertEqual(job_map['objs'], {})

    def test_get_crew_map_unknown_job(self):
        crew_dicts = [{'id': 1, 'obj': MovieCrew(movie=self.movie, person=self.person, department='Unknown', job='UnknownJob')}]
        crew_map = get_crew_map(crew_dicts)
        for job, job_map in crew_map.items():
            self.assertEqual(job_map['objs'], {})

    def test_get_crew_map_alias_handling(self):
        crew_dicts = [
            {'id': 1, 'obj': MovieCrew(movie=self.movie, person=self.person, department='Writing', job='Co-Writer')},
            {'id': 2, 'obj': MovieCrew(movie=self.movie, person=self.person, department='Production', job='Co-Producer')},
        ]
        crew_map = get_crew_map(crew_dicts)
        self.assertIn(1, crew_map['Writer']['objs'])
        self.assertIn(2, crew_map['Producer']['objs'])

    def test_get_crew_map_multiple_jobs_same_person(self):
        crew_dicts = [
            {'id': 1, 'obj': MovieCrew(movie=self.movie, person=self.person, department='Directing', job='Director')},
            {'id': 1, 'obj': MovieCrew(movie=self.movie, person=self.person, department='Writing', job='Screenplay')},
        ]
        crew_map = get_crew_map(crew_dicts)
        self.assertIn(1, crew_map['Director']['objs'])
        self.assertIn(1, crew_map['Writer']['objs'])
