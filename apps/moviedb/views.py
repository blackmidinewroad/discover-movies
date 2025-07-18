from django.db.models import F
from django.views.generic import DetailView, ListView

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
    }

    def get_queryset(self):
        queryset = Movie.objects.filter(adult=False)

        sort_by = self.kwargs.get('sort_by', '-tmdb_popularity')
        field = sort_by[1:] if sort_by.startswith('-') else sort_by

        match field:
            case 'tmdb_popularity':
                queryset = queryset.order_by(sort_by)
            case 'release_date':
                if sort_by.startswith('-'):
                    queryset = queryset.order_by(F(field).desc(nulls_last=True))
                else:
                    queryset = queryset.order_by(F(field).asc(nulls_last=True))
            case 'budget':
                queryset = queryset.exclude(budget=0).order_by(sort_by)
            case 'revenue':
                queryset = queryset.exclude(revenue=0).order_by(sort_by)
            case 'runtime':
                queryset = queryset.exclude(runtime=0).order_by(sort_by)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Discover Movies'
        context['list_type'] = 'movies'
        context['sort_by'] = self.kwargs.get('sort_by', '-tmdb_popularity')
        context['verbose_sort_by'] = self.VERBOSE_SORT_BY[context['sort_by']]
        return context


class PeopleListView(ListView):
    template_name = 'moviedb/main.html'
    context_object_name = 'people'
    paginate_by = 24
    queryset = Person.objects.filter(adult=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'People'
        context['list_type'] = 'people'
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
