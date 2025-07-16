from django.views.generic import DetailView, ListView

from .models import Movie


class MovieListView(ListView):
    # model = Movie
    template_name = 'moviedb/movie_list.html'
    context_object_name = 'movies'
    paginate_by = 48
    queryset = Movie.objects.prefetch_related('directors')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Discover Movies'
        return context


class MovieDetailView(DetailView):
    model = Movie
    template_name = 'moviedb/movie_detail.html'
    context_object_name = 'movie'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'{self.object.title}{f" - {self.object.release_date.year}" if self.object.release_date else ""}'
        return context
