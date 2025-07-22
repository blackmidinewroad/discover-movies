from django.urls import path

from .views import (
    CollectionDetailView,
    CollectionsListView,
    CompanyDetailView,
    CompanyListView,
    CountryListViews,
    LanguageListViews,
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
    path('other/', CountryListViews.as_view(), name='other'),
    path('countries/', CountryListViews.as_view(), name='countries'),
    path('languages/', LanguageListViews.as_view(), name='languages'),
    path('collections/', CollectionsListView.as_view(), name='collections'),
    path('collection/<slug:slug>/', CollectionDetailView.as_view(), name='collection_detail'),
    path('preduction-companies/', CompanyListView.as_view(), name='companies'),
    path('preduction-companies/by/<str:sort_by>', CompanyListView.as_view(), name='companies_sort'),
    path('production-company/<slug:slug>/', CompanyDetailView.as_view(), name='company_detail'),
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
    path('people/', PeopleListView.as_view(), name='people'),
    path('people/by/<str:sort_by>/', PeopleListView.as_view(), name='people_sort'),
    path('person/<slug:slug>/', PersonDetailView.as_view(), name='person_detail'),
]
