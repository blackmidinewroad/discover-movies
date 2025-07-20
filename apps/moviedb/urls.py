from django.urls import path

from .views import MovieDetailView, MovieListView, OtherView, PeopleListView, PersonDetailView

urlpatterns = [
    path('', MovieListView.as_view(), name='main'),
    path('movies/', MovieListView.as_view(), name='movies'),
    path('movies/by/<str:sort_by>', MovieListView.as_view(), name='movies_sort'),
    path('movies/by/<str:sort_by>/decade/<str:decade>', MovieListView.as_view(), name='movies_decade'),
    path('movies/by/<str:sort_by>/decade/<str:decade>/year/<int:year>', MovieListView.as_view(), name='movies_year'),
    path('movie/<slug:slug>/', MovieDetailView.as_view(), name='movie_detail'),
    path('other/', OtherView.as_view(), name='other'),
    path('movies-by-country/<slug:slug>', MovieListView.as_view(), name='movies_country'),
    path(
        'movies-by-country/<slug:slug>/by/<str:sort_by>/decade/<str:decade>/',
        MovieListView.as_view(),
        name='movies_decade_country',
    ),
    path(
        'movies-by-country/<slug:slug>/by/<str:sort_by>/decade/<str:decade>/year/<int:year>',
        MovieListView.as_view(),
        name='movies_year_country',
    ),
    path('movies-by-language/<slug:slug>', MovieListView.as_view(), name='movies_language'),
    path(
        'movies-by-language/<slug:slug>/by/<str:sort_by>/decade/<str:decade>/',
        MovieListView.as_view(),
        name='movies_decade_language',
    ),
    path(
        'movies-by-language/<slug:slug>/by/<str:sort_by>/decade/<str:decade>/year/<int:year>',
        MovieListView.as_view(),
        name='movies_year_language',
    ),
    path('people/', PeopleListView.as_view(), name='people'),
    path('people/by/<str:sort_by>', PeopleListView.as_view(), name='people_sort'),
    path('person/<slug:slug>/', PersonDetailView.as_view(), name='person_detail'),
]
