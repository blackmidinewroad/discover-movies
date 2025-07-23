import logging

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity
from django.db.models import Avg, BooleanField, Case, Count, F, Q, When
from django.views.generic import DetailView, ListView

from apps.services.utils import GenreIDs

from .forms import SearchForm
from .models import Collection, Country, Language, Movie, Person, ProductionCompany

logger = logging.getLogger('moviedb')


class MovieListView(ListView):
    template_name = 'moviedb/main.html'
    context_object_name = 'movies'
    paginate_by = 24

    VERBOSE_SORT_BY = {
        '-tmdb_popularity': 'Popularity ↓',
        'tmdb_popularity': 'Popularity ↑',
        '-release_date': 'Realease date ↓',
        'release_date': 'Realease date ↑',
        '-budget': 'Budget ↓',
        'budget': 'Budget ↑',
        '-revenue': 'Revenue ↓',
        'revenue': 'Revenue ↑',
        '-runtime': 'Runtime ↓',
        'runtime': 'Runtime ↑',
        'shuffle': 'Shuffle',
    }

    INCLUDE_DICT = {
        'documentary': 'Documentary',
        'tv_movie': 'TV Movie',
        'short': 'Short',
        'unreleased': 'Unreleased',
    }

    GENRE_DICT = {
        'Action': GenreIDs.ACTION,
        'Adventure': GenreIDs.ADVENTURE,
        'Animation': GenreIDs.ANIMATION,
        'Comedy': GenreIDs.COMEDY,
        'Crime': GenreIDs.CRIME,
        'Drama': GenreIDs.DRAMA,
        'Family': GenreIDs.FAMILY,
        'Fantasy': GenreIDs.FANTASY,
        'History': GenreIDs.HISTORY,
        'Horror': GenreIDs.HORROR,
        'Music': GenreIDs.MUSIC,
        'Mystery': GenreIDs.MYSTERY,
        'Romance': GenreIDs.ROMANCE,
        'Science Fiction': GenreIDs.SCIENCE_FICTION,
        'Thriller': GenreIDs.THRILLER,
        'War': GenreIDs.WAR,
        'Western': GenreIDs.WESTERN,
    }

    def get_queryset(self):
        queryset = Movie.objects.filter(adult=False)

        # Filter by country/language/production company
        if self.filter_type:
            self.filter_obj = None
            self.slug = self.kwargs.get('slug', '')
            match self.filter_type:
                case 'country':
                    queryset = queryset.filter(origin_country__slug=self.slug)
                    self.filter_obj = Country.objects.get(slug=self.slug)
                case 'language':
                    queryset = queryset.filter(original_language__slug=self.slug)
                    self.filter_obj = Language.objects.get(slug=self.slug)
                case 'company':
                    queryset = queryset.filter(production_companies__slug=self.slug)
                    self.filter_obj = ProductionCompany.objects.get(slug=self.slug)

        # Filter by year/decade
        self.year = self.kwargs.get('year', 0)
        if 1880 <= self.year <= 2030:
            queryset = queryset.filter(release_date__year=self.year)
            self.decade = f'{self.year // 10}0s'
        else:
            self.decade = self.kwargs.get('decade', 'any')
            if self.decade != 'any':
                try:
                    decade_int = int(self.decade[:-1])
                except ValueError:
                    decade_int = 0

                if 1880 <= decade_int <= 2020 and decade_int % 10 == 0:
                    queryset = queryset.filter(release_date__year__in=(year for year in range(decade_int, decade_int + 10)))
                else:
                    self.decade = 'any'

        # Filter includes
        if 'include' in self.request.session:
            if 'documentary' not in self.request.session['include']:
                queryset = queryset.exclude(genres__tmdb_id=GenreIDs.DOCUMENTARY)
            if 'tv_movie' not in self.request.session['include']:
                queryset = queryset.exclude(genres__tmdb_id=GenreIDs.TV_MOVIE)
            if 'short' not in self.request.session['include']:
                queryset = queryset.exclude(short=True)
            if 'unreleased' not in self.request.session['include']:
                queryset = queryset.filter(status=6)  # Only include released - status 6

        # Filter genres
        if 'genres' in self.request.session:
            if self.request.session['genres']:
                genre_ids = [self.GENRE_DICT[genre] for genre in self.request.session['genres']]
                queryset = (
                    queryset.filter(genres__tmdb_id__in=genre_ids)
                    .annotate(matching_genre_count=Count('genres', filter=Q(genres__tmdb_id__in=genre_ids), distinct=True))
                    .filter(matching_genre_count=len(genre_ids))
                )

        # Sort
        self.sort_by = self.kwargs.get('sort_by', '-tmdb_popularity')
        sort_by_field = self.sort_by[1:] if self.sort_by.startswith('-') else self.sort_by
        match sort_by_field:
            case 'tmdb_popularity':
                queryset = queryset.order_by(self.sort_by)
            case 'release_date':
                queryset = queryset.exclude(release_date=None).order_by(self.sort_by)
            case 'budget':
                queryset = queryset.exclude(budget=0).order_by(self.sort_by)
            case 'revenue':
                queryset = queryset.exclude(revenue=0).order_by(self.sort_by)
            case 'runtime':
                queryset = queryset.exclude(runtime=0).order_by(self.sort_by)
            case 'shuffle':
                queryset = queryset.order_by('?')
            case _:
                queryset = queryset.order_by('-tmdb_popularity')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.filter_type:
            context['title'] = self.filter_obj.name
        else:
            context['title'] = 'Discover Movies'

        context['list_type'] = 'movies'

        context['sort_by'] = self.sort_by
        context['verbose_sort_by'] = self.VERBOSE_SORT_BY.get(self.sort_by, 'Popularity ↓')
        context['sort_by_dict'] = self.VERBOSE_SORT_BY

        context['year'] = self.year
        context['decade'] = self.decade

        # For createing years dropdown
        if self.decade != 'any':
            decade_int = int(self.decade[:-1])
            context['years_list'] = list(range(decade_int + 9, decade_int - 1, -1))

        # For createing decade dropdown
        context['decade_list'] = [f'{decade}s' for decade in range(2020, 1879, -10)]

        context['include_dict'] = self.INCLUDE_DICT
        context['included'] = self.request.session.get('include', list(self.INCLUDE_DICT.keys()))

        context['genres_list'] = list(self.GENRE_DICT.keys())
        context['checked_genres'] = self.request.session.get('genres', [])

        context['decade_route_name'] = f'movies_decade'
        context['year_route_name'] = f'movies_year'

        if self.filter_type:
            context[self.filter_type] = self.filter_obj

            context['decade_route_name'] += f'_{self.filter_type}'
            context['year_route_name'] += f'_{self.filter_type}'

            context['slug'] = self.slug

        context['total_results'] = context['paginator'].count

        return context

    def get(self, request, *args, **kwargs):
        route_name = request.resolver_match.view_name

        if 'country' in route_name:
            self.filter_type = 'country'
        elif 'language' in route_name:
            self.filter_type = 'language'
        elif 'company' in route_name:
            self.filter_type = 'company'
        else:
            self.filter_type = ''

        # Clean session on root page reload
        if route_name in ('main', 'movies'):
            for key in ('include', 'genres'):
                request.session.pop(key, None)

        # HTMX request
        if request.headers.get('HX-Request'):
            self.template_name = 'moviedb/partials/content_grid.html'
            if 'include' in request.GET:
                self.request.session['include'] = [i for i in request.GET.getlist('include') if i != '_empty']
            if 'genres' in request.GET:
                self.request.session['genres'] = [g for g in request.GET.getlist('genres') if g != '_empty']

        return super().get(request, *args, **kwargs)


class PeopleListView(ListView):
    template_name = 'moviedb/main.html'
    context_object_name = 'people'
    paginate_by = 24

    VERBOSE_SORT_BY = {
        '-tmdb_popularity': 'Popularity ↓',
        'tmdb_popularity': 'Popularity ↑',
        'shuffle': 'Shuffle',
    }

    def get_queryset(self):
        queryset = Person.objects.filter(adult=False)

        sort_by = self.kwargs.get('sort_by', '-tmdb_popularity')
        sort_by_field = sort_by[1:] if sort_by.startswith('-') else sort_by
        match sort_by_field:
            case 'tmdb_popularity':
                queryset = queryset.order_by(sort_by)
            case 'shuffle':
                queryset = queryset.order_by('?')
            case _:
                queryset = queryset.order_by('-tmdb_popularity')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'People'
        context['list_type'] = 'people'

        context['sort_by'] = self.kwargs.get('sort_by', '-tmdb_popularity')
        context['verbose_sort_by'] = self.VERBOSE_SORT_BY.get(context['sort_by'], 'Popularity ↓')
        context['sort_by_dict'] = self.VERBOSE_SORT_BY

        context['total_results'] = context['paginator'].count
        return context


class MovieDetailView(DetailView):
    model = Movie
    template_name = 'moviedb/movie_detail.html'
    context_object_name = 'movie'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'{self.object.title}{f" - {self.object.release_date.year}" if self.object.release_date else ""}'
        return context


class PersonDetailView(DetailView):
    model = Person
    template_name = 'moviedb/person_detail.html'
    context_object_name = 'person'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'{self.object.name}'
        return context


class CountryListViews(ListView):
    queryset = Country.objects.exclude(name='unknown')
    template_name = 'moviedb/other.html'
    context_object_name = 'countries'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Countries'
        context['list_type'] = 'countries'
        context['total_results'] = self.object_list.count
        return context


class LanguageListViews(ListView):
    model = Language
    template_name = 'moviedb/other.html'
    context_object_name = 'languages'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Languages'
        context['list_type'] = 'languages'
        context['total_results'] = self.object_list.count
        return context


class CollectionsListView(ListView):
    template_name = 'moviedb/other.html'
    context_object_name = 'collections'
    form = SearchForm()
    paginate_by = 24

    def get_queryset(self):
        # Search
        if 'query' in self.request.GET:
            self.form = SearchForm(self.request.GET)

            if self.form.is_valid():
                vector = SearchVector('name')
                query = self.form.cleaned_data['query']
                search_query = SearchQuery(query)

                # test search
                queryset = (
                    Collection.objects.annotate(
                        similarity=TrigramSimilarity('name', query),
                        search=vector,
                    )
                    .filter(search=search_query)
                    .order_by('-similarity')
                )

                # queryset = Collection.objects.filter(name__search=query)
                # queryset = Collection.objects.annotate(search=vector).filter(search=query)
                # queryset = Collection.objects.annotate(rank=SearchRank(vector, query)).filter(rank__gt=0).order_by('-rank')

                # self.template_name = 'moviedb/collections_list.html'
        else:
            # Order by average popularity of movies in the collection, if only one movie in collection was released
            # put it in the end, put empty collections last
            queryset = (
                Collection.objects.filter(adult=False)
                .exclude(movies=None)
                .annotate(
                    avg_popularity=Avg('movies__tmdb_popularity'),
                    n_released=Count('movies__status', filter=Q(movies__status=6)),
                    relesed_more_than_one=Case(
                        When(n_released__gt=1, then=True),
                        default=False,
                        output_field=BooleanField(),
                    ),
                )
                .order_by(F('relesed_more_than_one').desc(), F('avg_popularity').desc(nulls_last=True))
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Collections'
        context['list_type'] = 'collections'
        context['total_results'] = context['paginator'].count
        context['form'] = self.form
        return context


class CollectionDetailView(DetailView):
    model = Collection
    template_name = 'moviedb/collection_detail.html'
    context_object_name = 'collection'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'{self.object.name}'
        context['movies'] = self.object.movies.all().order_by('release_date')
        context['total_movies'] = context['movies'].count
        return context


class CompanyListView(ListView):
    template_name = 'moviedb/other.html'
    context_object_name = 'companies'
    paginate_by = 90

    VERBOSE_SORT_BY = {
        '-movie_count': 'Number of movies ↓',
        '-name': 'Name (A-Z)',
        'name': 'Name (Z-A)',
        'shuffle': 'Shuffle',
    }

    def get_queryset(self):
        queryset = ProductionCompany.objects.all()

        self.sort_by = self.kwargs.get('sort_by', '-movie_count')
        sort_by_field = self.sort_by[1:] if self.sort_by.startswith('-') else self.sort_by
        match sort_by_field:
            case 'movie_count':
                pass  # ordered by movie_count by default
            case 'name':
                queryset = queryset.order_by(self.sort_by)
            case 'shuffle':
                queryset = queryset.order_by('?')

        logger.info('%s', queryset.explain(analyze=True))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Production Companies'
        context['list_type'] = 'companies'

        context['sort_by'] = self.sort_by
        context['verbose_sort_by'] = self.VERBOSE_SORT_BY.get(self.sort_by, 'Number of movies ↓')
        context['sort_by_dict'] = self.VERBOSE_SORT_BY

        context['total_results'] = context['paginator'].count

        return context
