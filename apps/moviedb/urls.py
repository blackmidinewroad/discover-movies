from django.urls import path

from .views import MovieDetailView, MovieListView, PeopleListView, PersonDetailView

urlpatterns = [
    path('', MovieListView.as_view(), name='main'),
    path('movies/', MovieListView.as_view(), name='movie_list'),
    path('movies/by/<str:sort_by>', MovieListView.as_view(), name='movie_list_by'),
    path('people/', PeopleListView.as_view(), name='people_list'),
    path('movie/<slug:slug>/', MovieDetailView.as_view(), name='movie_detail'),
    path('person/<slug:slug>/', PersonDetailView.as_view(), name='person_detail'),
]
