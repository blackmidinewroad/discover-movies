from django.contrib import admin

from .models import Country, Genre, Language, Movie, ProductionCompany


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    """Admin panel for genre"""

    list_display = ['name']


@admin.register(ProductionCompany)
class ProductionCompanyAdmin(admin.ModelAdmin):
    """Admin panel for production company"""

    list_display = ['name', 'origin_country']


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    """Admin panel for movie"""

    list_display = ['name', 'code']


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    """Admin panel for movie"""

    list_display = ['name', 'code']


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    """Admin panel for movie"""

    list_display = ['title', 'slug', 'release_date']
