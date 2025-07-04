from django.contrib import admin

from .models import Genre, Movie, ProductionCompany


@admin.register(Genre)
class CategoryAdmin(admin.ModelAdmin):
    """Admin panel for genre"""

    pass


@admin.register(ProductionCompany)
class CategoryAdmin(admin.ModelAdmin):
    """Admin panel for production company"""

    pass


@admin.register(Movie)
class CategoryAdmin(admin.ModelAdmin):
    """Admin panel for movie"""

    pass
