import logging

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity
from django.db.models import F, Q
from django.views.generic import DetailView, ListView

from apps.services.utils import GENRE_DICT, GenreIDs, get_base_query

from .forms import SearchForm
from .models import Collection, Country, Language, Movie, Person, ProductionCompany

logger = logging.getLogger('moviedb')


class MovieListView(ListView):
    template_name = 'moviedb/main.html'
    context_object_name = 'movies'
    form = SearchForm()
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

    FILTER_DICT = {
        'show_documentary': 'Show Documentary',
        'hide_documentary': 'Hide Documentary',
        'show_tv_movie': 'Show TV Movie',
        'hide_tv_movie': 'Hide TV Movie',
        'show_short': 'Show Short',
        'hide_short': 'Hide Short',
        'show_unreleased': 'Show Unreleased',
        'hide_unreleased': 'Hide Unreleased',
    }

    def get_queryset(self):
        # Filter by country/language/production company
        if self.filter_type:
            self.filter_obj = None
            self.slug = self.kwargs.get('slug', '')
            match self.filter_type:
                case 'country':
                    self.filter_obj = Country.objects.get(slug=self.slug)
                    queryset = self.filter_obj.movies_originating_from.all()
                case 'language':
                    self.filter_obj = Language.objects.get(slug=self.slug)
                    queryset = self.filter_obj.movies_as_original_language.all()
                case 'company':
                    self.filter_obj = ProductionCompany.objects.get(slug=self.slug)
                    queryset = self.filter_obj.movies.all()
        else:
            queryset = Movie.objects.all()

        queryset = queryset.filter(removed_from_tmdb=False)

        self.year = self.kwargs.get('year', 0)
        self.decade = 'any'
        self.sort_by = self.kwargs.get('sort_by', '-tmdb_popularity')

        # Search
        if 'query' in self.request.GET and self.request.GET.get('query'):
            self.form = SearchForm(self.request.GET)
            if self.form.is_valid():
                vector = SearchVector('title', weight='A') + SearchVector('original_title', weight='B')
                query = self.form.cleaned_data['query']
                search_query = SearchQuery(query)

                queryset = (
                    queryset.annotate(
                        similarity=TrigramSimilarity('title', query),
                        similarity_orig=TrigramSimilarity('original_title', query),
                        rank=SearchRank(vector, search_query),
                    )
                    .filter(Q(similarity__gt=0.2) | Q(similarity_orig__gt=0.2) | Q(rank__gt=0.2))
                    .order_by('-rank')
                )
        else:
            queryset = queryset.filter(adult=False)

            # Filter by year/decade
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
                        start_date = f'{decade_int}-01-01'
                        end_date = f'{decade_int + 9}-12-31'
                        queryset = queryset.filter(release_date__range=(start_date, end_date))
                    else:
                        self.decade = 'any'

            # Apply filters
            if 'filter' in self.request.session:
                if 'show_documentary' in self.request.session['filter']:
                    queryset = queryset.filter(genres__tmdb_id=GenreIDs.DOCUMENTARY)
                elif 'hide_documentary' in self.request.session['filter']:
                    queryset = queryset.exclude(genres__tmdb_id=GenreIDs.DOCUMENTARY)
                if 'show_tv_movie' in self.request.session['filter']:
                    queryset = queryset.filter(genres__tmdb_id=GenreIDs.TV_MOVIE)
                elif 'hide_tv_movie' in self.request.session['filter']:
                    queryset = queryset.exclude(genres__tmdb_id=GenreIDs.TV_MOVIE)
                if 'show_short' in self.request.session['filter']:
                    queryset = queryset.filter(short=True)
                elif 'hide_short' in self.request.session['filter']:
                    queryset = queryset.exclude(short=True)
                if 'show_unreleased' in self.request.session['filter']:
                    queryset = queryset.exclude(status=6)
                elif 'hide_unreleased' in self.request.session['filter']:
                    queryset = queryset.filter(status=6)

            # Filter genres
            if 'genres' in self.request.session and self.request.session['genres']:
                genre_ids = [GENRE_DICT[genre] for genre in self.request.session['genres']]
                for genre_id in genre_ids:
                    queryset = queryset.filter(genres__tmdb_id=genre_id)
                queryset = queryset.distinct()

            # Sort
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

        context['filter_dict'] = self.FILTER_DICT
        context['filtered'] = self.request.session.get('filter', [])

        context['genres_list'] = list(GENRE_DICT.keys())
        context['checked_genres'] = self.request.session.get('genres', [])

        context['decade_route_name'] = f'movies_decade'
        context['year_route_name'] = f'movies_year'

        if self.filter_type:
            context[self.filter_type] = self.filter_obj

            context['decade_route_name'] += f'_{self.filter_type}'
            context['year_route_name'] += f'_{self.filter_type}'

            context['slug'] = self.slug

        context['total_results'] = context['paginator'].count

        context['form'] = self.form

        context['base_query'] = self.base_query

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

        # Clear session
        if request.get_full_path() in ('/', '/movies/'):
            for key in ('filter', 'genres'):
                request.session.pop(key, None)

        # HTMX request
        if request.headers.get('HX-Request'):
            self.template_name = 'moviedb/movies/partials/content_grid.html'
            if 'filter' in request.GET:
                self.request.session['filter'] = [i for i in request.GET.getlist('filter') if i != '_empty']
            if 'genres' in request.GET:
                self.request.session['genres'] = [g for g in request.GET.getlist('genres') if g != '_empty']

        # Get base query for pagination
        self.base_query = get_base_query(request)

        return super().get(request, *args, **kwargs)


class PeopleListView(ListView):
    template_name = 'moviedb/main.html'
    context_object_name = 'people'
    form = SearchForm()
    paginate_by = 24

    VERBOSE_SORT_BY = {
        '-tmdb_popularity': 'Popularity ↓',
        'tmdb_popularity': 'Popularity ↑',
        '-cast_roles_count': 'Cast Roles ↓',
        '-crew_roles_count': 'Crew Roles ↓',
        '-combined_roles': 'Combined Roles ↓',
        'shuffle': 'Shuffle',
    }

    VERBOSE_DEPARTMENT = {
        'any': 'Any',
        'acting': 'Acting',
        'art': 'Art',
        'camera': 'Camera',
        'costume-make-up': 'Costume & Make-Up',
        'directing': 'Directing',
        'editing': 'Editing',
        'lighting': 'Lighting',
        'production': 'Production',
        'sound': 'Sound',
        'visual-effects': 'Visual Effects',
        'writing': 'Writing',
        'other': 'Other',
    }

    def get_queryset(self):
        queryset = Person.objects.filter(removed_from_tmdb=False)

        department = self.kwargs.get('department', 'any')
        if department != 'any' and department in self.VERBOSE_DEPARTMENT:
            if department == 'acting':
                queryset = queryset.filter(known_for_department__in=('Acting', 'Actors'))
            elif department == 'other':
                queryset = queryset.filter(known_for_department__in=('', 'Creator', 'Crew'))
            else:
                queryset = queryset.filter(known_for_department=self.VERBOSE_DEPARTMENT[department])

        # Search
        if 'query' in self.request.GET and self.request.GET.get('query'):
            self.form = SearchForm(self.request.GET)
            if self.form.is_valid():
                query = self.form.cleaned_data['query']

                queryset = queryset.annotate(similarity=TrigramSimilarity('name', query)).filter(similarity__gt=0.3).order_by('-similarity')
        else:
            queryset = queryset.filter(adult=False)
            sort_by = self.kwargs.get('sort_by', '-tmdb_popularity')
            sort_by_field = sort_by[1:] if sort_by.startswith('-') else sort_by
            match sort_by_field:
                case 'combined_roles':
                    queryset = queryset.annotate(combines_roles=F('cast_roles_count') + F('crew_roles_count')).order_by('-combines_roles')
                case 'shuffle':
                    queryset = queryset.order_by('?')
                case _:
                    if sort_by in self.VERBOSE_SORT_BY:
                        queryset = queryset.order_by(sort_by)
                    else:
                        queryset = queryset.order_by('-tmdb_popularity')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'People'
        context['list_type'] = 'people'

        context['sort_by'] = self.kwargs.get('sort_by', '-tmdb_popularity')
        context['verbose_sort_by'] = self.VERBOSE_SORT_BY.get(context['sort_by'], 'Popularity ↓')
        context['sort_by_dict'] = self.VERBOSE_SORT_BY

        context['department'] = self.kwargs.get('department', 'any')
        context['verbose_department'] = self.VERBOSE_DEPARTMENT.get(context['department'], 'Any')
        context['department_dict'] = self.VERBOSE_DEPARTMENT

        context['total_results'] = context['paginator'].count

        context['form'] = self.form

        context['base_query'] = self.base_query

        return context

    def get(self, request, *args, **kwargs):
        # Get base query for pagination
        self.base_query = get_base_query(request)

        return super().get(request, *args, **kwargs)


class MovieDetailView(DetailView):
    model = Movie
    template_name = 'moviedb/movies/movie_detail.html'
    context_object_name = 'movie'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'{self.object.title}{f" - {self.object.release_date.year}" if self.object.release_date else ""}'
        context['directors'] = self.object.directors.all()
        return context


class PersonDetailView(DetailView):
    model = Person
    template_name = 'moviedb/people/person_detail.html'
    context_object_name = 'person'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'{self.object.name}'
        return context


class CountryListViews(ListView):
    template_name = 'moviedb/other.html'
    context_object_name = 'countries'
    form = SearchForm()

    def get_queryset(self):
        queryset = Country.objects.exclude(name='unknown')

        # Search
        if 'query' in self.request.GET:
            self.template_name = 'moviedb/other/partials/content_grid.html'
            self.form = SearchForm(self.request.GET)

            if self.form.is_valid() and (query := self.form.cleaned_data['query']):
                queryset = queryset.annotate(similarity=TrigramSimilarity('name', query)).filter(similarity__gt=0.2).order_by('-similarity')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Countries'
        context['list_type'] = 'countries'
        context['total_results'] = self.object_list.count
        context['form'] = self.form
        return context

    def get(self, request, *args, **kwargs):
        # Clear session
        if request.get_full_path() == '/other/':
            for key in ('filter', 'genres'):
                request.session.pop(key, None)

        return super().get(request, *args, **kwargs)


class LanguageListViews(ListView):
    template_name = 'moviedb/other.html'
    context_object_name = 'languages'
    form = SearchForm()

    def get_queryset(self):
        queryset = Language.objects.all()

        # Search
        if 'query' in self.request.GET:
            self.template_name = 'moviedb/other/partials/content_grid.html'
            self.form = SearchForm(self.request.GET)

            if self.form.is_valid() and (query := self.form.cleaned_data['query']):
                queryset = queryset.annotate(similarity=TrigramSimilarity('name', query)).filter(similarity__gt=0.2).order_by('-similarity')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Languages'
        context['list_type'] = 'languages'
        context['total_results'] = self.object_list.count
        context['form'] = self.form
        return context


class CollectionsListView(ListView):
    template_name = 'moviedb/other.html'
    context_object_name = 'collections'
    form = SearchForm()
    paginate_by = 24

    def get_queryset(self):
        queryset = Collection.objects.filter(removed_from_tmdb=False)

        # Search
        if 'query' in self.request.GET and self.request.GET.get('query'):
            self.form = SearchForm(self.request.GET)
            if self.form.is_valid():
                vector = SearchVector('name', weight='A') + SearchVector('overview', weight='B')
                query = self.form.cleaned_data['query']
                search_query = SearchQuery(query)

                queryset = (
                    queryset.annotate(
                        similarity=TrigramSimilarity('name', query),
                        rank=SearchRank(vector, search_query),
                    )
                    .filter(Q(similarity__gt=0.2) | Q(rank__gt=0.2))
                    .order_by('-rank')
                )

        else:
            queryset = queryset.filter(adult=False, movies_released__gt=1).order_by('-avg_popularity')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Collections'
        context['list_type'] = 'collections'
        context['total_results'] = context['paginator'].count
        context['form'] = self.form
        context['base_query'] = self.base_query
        return context

    def get(self, request, *args, **kwargs):
        # Get base query for pagination
        self.base_query = get_base_query(request)

        return super().get(request, *args, **kwargs)


class CollectionDetailView(DetailView):
    model = Collection
    template_name = 'moviedb/other/collection_detail.html'
    context_object_name = 'collection'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'{self.object.name}'
        context['movies'] = self.object.movies.filter(removed_from_tmdb=False).order_by('release_date')
        context['total_movies'] = context['movies'].count()
        return context


class CompanyListView(ListView):
    template_name = 'moviedb/other.html'
    context_object_name = 'companies'
    form = SearchForm()
    paginate_by = 90

    VERBOSE_SORT_BY = {
        '-movie_count': 'Number of movies ↓',
        'shuffle': 'Shuffle',
    }

    def get_queryset(self):
        queryset = ProductionCompany.objects.filter(removed_from_tmdb=False)

        self.sort_by = self.kwargs.get('sort_by', '-movie_count')

        # Search
        if 'query' in self.request.GET and self.request.GET.get('query'):
            self.form = SearchForm(self.request.GET)
            if self.form.is_valid():
                query = self.form.cleaned_data['query']

                queryset = queryset.annotate(similarity=TrigramSimilarity('name', query)).filter(similarity__gt=0.2).order_by('-similarity')
        else:
            sort_by_field = self.sort_by[1:] if self.sort_by.startswith('-') else self.sort_by
            match sort_by_field:
                case 'movie_count':
                    queryset = queryset.order_by(self.sort_by)
                case 'shuffle':
                    queryset = queryset.order_by('?')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Production Companies'
        context['list_type'] = 'companies'

        context['sort_by'] = self.sort_by
        context['verbose_sort_by'] = self.VERBOSE_SORT_BY.get(self.sort_by, 'Number of movies ↓')
        context['sort_by_dict'] = self.VERBOSE_SORT_BY

        context['form'] = self.form

        context['total_results'] = context['paginator'].count

        context['base_query'] = self.base_query

        return context

    def get(self, request, *args, **kwargs):
        # Get base query for pagination
        self.base_query = get_base_query(request)

        return super().get(request, *args, **kwargs)
