from django.contrib import admin
from django.db.models import F

from . import models


@admin.register(models.Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(models.Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(models.Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'tmdb_id')
    search_fields = ('name', 'tmdb_id')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(models.ProductionCompany)
class ProductionCompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'origin_country', 'tmdb_id')
    search_fields = ('name', 'tmdb_id')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']


@admin.register(models.Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'tmdb_id')
    search_fields = ('name', 'tmdb_id')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']


@admin.register(models.Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'known_for_department')
    search_fields = ('name', 'tmdb_id')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['-last_update', '-tmdb_popularity']


@admin.register(models.Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'release_date')
    search_fields = ('title', 'directors__name', 'tmdb_id')
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = [
        'genres',
        'spoken_languages',
        'origin_country',
        'production_companies',
        'production_countries',
        'original_language',
        'collection',
        'directors',
    ]
    ordering = ['-status', F('release_date').desc(nulls_last=True)]

    def get_directors(self, obj):
        return ", ".join(d.name for d in obj.directors.all())

    get_directors.short_description = 'Directed by'


@admin.register(models.MovieEngagement)
class MovieEngagementAdmin(admin.ModelAdmin):
    list_display = ('movie', 'lb_rating')
    search_fields = ('movie__name',)
    ordering = ['movie']


@admin.register(models.MovieCast)
class MovieCastAdmin(admin.ModelAdmin):
    list_display = ('person', 'character', 'movie')
    search_fields = ('person__name', 'character', 'movie__title')
    autocomplete_fields = ['movie', 'person']
    ordering = ['order']


@admin.register(models.MovieCrew)
class MovieCrewAdmin(admin.ModelAdmin):
    list_display = ('person', 'movie', 'department', 'job')
    search_fields = ('person__name', 'movie__title')
    autocomplete_fields = ['movie', 'person']
    ordering = ['person']
