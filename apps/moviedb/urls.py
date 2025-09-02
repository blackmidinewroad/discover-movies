from django.urls import path

from .views import (
    CollectionDetailView,
    CollectionsListView,
    CompanyListView,
    CountryListView,
    LanguageListView,
    MovieDetailView,
    MovieListView,
    PeopleListView,
    PersonDetailView,
)

urlpatterns = [
    path('', MovieListView.as_view(), name='main'),
    path('movies/', MovieListView.as_view(), name='movies'),
    path('movies/by/<str:sort_by>', MovieListView.as_view(), name='movies_sort'),
    path('movies/by/<str:sort_by>/decade/<str:decade>', MovieListView.as_view(), name='movies_decade'),
    path('movies/by/<str:sort_by>/decade/<str:decade>/year/<int:year>', MovieListView.as_view(), name='movies_year'),
    path('movie/<slug:slug>/', MovieDetailView.as_view(), name='movie_detail'),
    path('other/', CountryListView.as_view(), name='other'),
    path('countries/', CountryListView.as_view(), name='countries'),
    path('languages/', LanguageListView.as_view(), name='languages'),
    path('collections/', CollectionsListView.as_view(), name='collections'),
    path('collection/<slug:slug>/', CollectionDetailView.as_view(), name='collection_detail'),
    path('production-companies/', CompanyListView.as_view(), name='companies'),
    path('production-companies/by/<str:sort_by>', CompanyListView.as_view(), name='companies_sort'),
    path('movies-by-country/<slug:slug>/', MovieListView.as_view(), name='movies_country'),
    path(
        'movies-by-country/<slug:slug>/by/<str:sort_by>/decade/<str:decade>/',
        MovieListView.as_view(),
        name='movies_decade_country',
    ),
    path(
        'movies-by-country/<slug:slug>/by/<str:sort_by>/decade/<str:decade>/year/<int:year>/',
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
        'movies-by-language/<slug:slug>/by/<str:sort_by>/decade/<str:decade>/year/<int:year>/',
        MovieListView.as_view(),
        name='movies_year_language',
    ),
    path('production-company/<slug:slug>/', MovieListView.as_view(), name='movies_company'),
    path(
        'production-company/<slug:slug>/by/<str:sort_by>/decade/<str:decade>/',
        MovieListView.as_view(),
        name='movies_decade_company',
    ),
    path(
        'production-company/<slug:slug>/by/<str:sort_by>/decade/<str:decade>/year/<int:year>/',
        MovieListView.as_view(),
        name='movies_year_company',
    ),
    path('genre/<slug:slug>/', MovieListView.as_view(), name='movies_genre'),
    path(
        'genre/<slug:slug>/by/<str:sort_by>/decade/<str:decade>/',
        MovieListView.as_view(),
        name='movies_decade_genre',
    ),
    path(
        'genre/<slug:slug>/by/<str:sort_by>/decade/<str:decade>/year/<int:year>/',
        MovieListView.as_view(),
        name='movies_year_genre',
    ),
    path('people/', PeopleListView.as_view(), name='people'),
    path('people/by/<str:sort_by>/', PeopleListView.as_view(), name='people_sort'),
    path('people/department/<str:department>/by/<str:sort_by>/', PeopleListView.as_view(), name='people_department_sort'),
    path('person/<slug:slug>/', PersonDetailView.as_view(), name='person_detail'),
    path('person/<slug:slug>/<str:job>', PersonDetailView.as_view(), name='person_job'),
    path('person/<slug:slug>/<str:job>/by/<str:sort_by>', PersonDetailView.as_view(), name='person_sort'),
]
