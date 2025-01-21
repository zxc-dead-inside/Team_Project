from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    Genre, GenreFilmwork, Filmwork, Person, PersonFilmwork)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    search_fields = ('genre',)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('full_name',)
    search_fields = ('full_name',)


class PersonFilmworkInline(admin.TabularInline):
    model = PersonFilmwork
    autocomplete_fields = ('person',)


class GenreFilmworkInline(admin.TabularInline):
    model = GenreFilmwork
    autocomplete_fields = ('genre',)


@admin.register(Filmwork)
class FilmworkAdmin(admin.ModelAdmin):
    inlines = (GenreFilmworkInline, PersonFilmworkInline)
    list_display = (
        'title', 'type', 'creation_date', 'rating', 'get_genres')
    list_filter = ('type', 'genres')
    search_fields = ('title', 'description', 'id')

    def get_queryset(self, request):
        queryset = super().get_queryset(
            request).prefetch_related('genres')
        return queryset

    def get_genres(self, obj):
        return ','.join([genre.name for genre in obj.genres.all()])

    get_genres.short_description = _('genres')
