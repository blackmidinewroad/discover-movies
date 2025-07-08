from django.contrib import admin

from . import models


@admin.register(models.Country)
class CountryAdmin(admin.ModelAdmin):
    """Admin panel for country"""

    list_display = ('name', 'code')
    search_fields = ('name', 'code')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(models.Language)
class LanguageAdmin(admin.ModelAdmin):
    """Admin panel for language"""

    list_display = ('name', 'code')
    search_fields = ('name', 'code')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(models.Genre)
class GenreAdmin(admin.ModelAdmin):
    """Admin panel for genre"""

    list_display = ('name',)
    search_fields = ('name', 'tmdb_id')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(models.ProductionCompany)
class ProductionCompanyAdmin(admin.ModelAdmin):
    """Admin panel for production company"""

    list_display = ('name', 'origin_country')
    search_fields = ('name', 'tmdb_id')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']


@admin.register(models.Collection)
class CollectionAdmin(admin.ModelAdmin):
    """Admin panel for collection"""

    list_display = ('name',)
    search_fields = ('name', 'tmdb_id')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']


@admin.register(models.Movie)
class MovieAdmin(admin.ModelAdmin):
    """Admin panel for movie"""

    list_display = ('title', 'release_date')
    search_fields = ('title',)
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = [
        'genres',
        'spoken_languages',
        'origin_country',
        'production_companies',
        'production_countries',
        'original_language',
        'collection',
    ]


@admin.register(models.MovieEngagement)
class MovieEngagementAdmin(admin.ModelAdmin):
    """Admin panel for movie engagement"""

    list_display = ('movie', 'lb_rating')
    search_fields = ('movie',)
    ordering = ['movie']


@admin.register(models.Person)
class PersonAdmin(admin.ModelAdmin):
    """Admin panel for person"""

    list_display = ('name', 'known_for_department')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['-tmdb_popularity']


@admin.register(models.MovieCast)
class MovieCastAdmin(admin.ModelAdmin):
    """Admin panel for casts"""

    list_display = ('person', 'character', 'movie')
    search_fields = ('person', 'character', 'movie')
    ordering = ['order']


@admin.register(models.MovieCrew)
class MovieCrewAdmin(admin.ModelAdmin):
    """Admin panel for crews"""

    list_display = ('person', 'movie', 'department', 'job')
    search_fields = ('person', 'movie')
    ordering = ['person']
