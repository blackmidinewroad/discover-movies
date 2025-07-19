from django.db.models import Count, Q
from django.views.generic import DetailView, ListView

from apps.services.utils import GenreIDs

from .models import Movie, Person


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
        queryset = Movie.objects.filter(adult=False).prefetch_related('genres')

        # Filter by year/decade
        year = self.kwargs.get('year', 0)
        if 1880 <= year <= 2030:
            queryset = queryset.filter(release_date__year=year)
        else:
            decade = self.kwargs.get('decade', 'any')
            if decade != 'any':
                try:
                    decade_int = int(decade[:-1])
                except ValueError:
                    decade_int = 0

                if 1880 <= decade_int <= 2020 and decade_int % 10 == 0:
                    queryset = queryset.filter(release_date__year__in=(year for year in range(decade_int, decade_int + 10)))

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
        sort_by = self.kwargs.get('sort_by', '-tmdb_popularity')
        sort_by_field = sort_by[1:] if sort_by.startswith('-') else sort_by
        match sort_by_field:
            case 'tmdb_popularity':
                queryset = queryset.order_by(sort_by)
            case 'release_date':
                queryset = queryset.exclude(release_date=None).order_by(sort_by)
            case 'budget':
                queryset = queryset.exclude(budget=0).order_by(sort_by)
            case 'revenue':
                queryset = queryset.exclude(revenue=0).order_by(sort_by)
            case 'runtime':
                queryset = queryset.exclude(runtime=0).order_by(sort_by)
            case 'shuffle':
                queryset = queryset.order_by('?')
            case _:
                queryset = queryset.order_by('-tmdb_popularity')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Discover Movies'
        context['list_type'] = 'movies'

        context['sort_by'] = self.kwargs.get('sort_by', '-tmdb_popularity')
        context['verbose_sort_by'] = self.VERBOSE_SORT_BY.get(context['sort_by'], 'Popularity ↓')
        context['sort_by_dict'] = self.VERBOSE_SORT_BY

        context['year'] = self.kwargs.get('year', 0)

        if 1880 <= context['year'] <= 2030:
            context['decade'] = f'{context['year'] // 10}0s'
        else:
            context['decade'] = self.kwargs.get('decade', 'any')
            if context['decade'] != 'any':
                try:
                    decade_int = int(context['decade'][:-1])
                except ValueError:
                    decade_int = 0

                if not (1880 <= decade_int <= 2020) or decade_int % 10 != 0:
                    context['decade'] = 'any'

        # For createing years dropdown
        if context['decade'] != 'any':
            decade_int = int(context['decade'][:-1])
            context['years_list'] = list(range(decade_int + 9, decade_int - 1, -1))

        # For createing decade dropdown
        context['decade_list'] = [f'{decade}s' for decade in range(2020, 1879, -10)]

        context['include_dict'] = self.INCLUDE_DICT
        context['included'] = self.request.session.get('include', list(self.INCLUDE_DICT.keys()))

        context['genres_list'] = list(self.GENRE_DICT.keys())
        context['checked_genres'] = self.request.session.get('genres', [])

        context['total_results'] = context['paginator'].count

        return context

    def get(self, request, *args, **kwargs):
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
    template_name = 'moviedb/movie_detail.html'
    context_object_name = 'movie'
    queryset = Movie.objects.prefetch_related('directors')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'{self.object.title}{f" - {self.object.release_date.year}" if self.object.release_date else ""}'
        return context


class PersonDetailView(DetailView):
    template_name = 'moviedb/person_detail.html'
    context_object_name = 'person'
    queryset = Person.objects.prefetch_related('cast_roles', 'crew_roles')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'{self.object.name}'
        return context
