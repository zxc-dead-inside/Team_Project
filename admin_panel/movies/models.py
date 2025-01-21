import uuid

from django.db import models
from django.core.validators import (
    MinValueValidator, MaxValueValidator)
from django.utils.translation import gettext_lazy as _


class TimeStampedCreateMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class TimeStampedUpdateMixin(models.Model):
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDMixin(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class Genre(UUIDMixin, TimeStampedCreateMixin,
            TimeStampedUpdateMixin):
    """
    Модель для таблицы с жанрами.
    """

    name = models.CharField(_('name'))
    description = models.TextField(_('description'), blank=True)

    class Meta:
        db_table = "content\".\"genre"
        verbose_name = _('genre')
        verbose_name_plural = _('genres')

    def __str__(self):
        return self.name


class Person(UUIDMixin, TimeStampedCreateMixin,
             TimeStampedUpdateMixin):
    """
    Таблица содержит людей принимающих участие в создании фильма
    или шоу.
    """

    full_name = models.TextField(_('name'))

    class Meta:
        db_table = 'content\".\"person'
        verbose_name = _('person')
        verbose_name_plural = _('people')

    def __str__(self):
        return self.full_name


class Filmwork(UUIDMixin, TimeStampedCreateMixin,
               TimeStampedUpdateMixin):
    """
    Модель для таблицы с фильмами и телевизионными шоу.
    """

    class Type(models.TextChoices):
        movie = 'movie', _('movie')
        tv_show = 'tv_show', _('tv_show')

    title = models.TextField(_('title'))
    description = models.TextField(_('description'), blank=True)
    creation_date = models.DateField(_('creation date'), blank=True)
    file_path = models.TextField(_('file path'), blank=True)
    rating = models.FloatField(
        _('rating'), blank=True, validators=[
            MinValueValidator(0),
            MaxValueValidator(10)
        ])
    type = models.CharField(
        _('type'), choices=Type.choices)
    genres = models.ManyToManyField(
        Genre, through='GenreFilmwork', verbose_name=_('genres'))
    people = models.ManyToManyField(
        Person, through='PersonFilmwork', verbose_name=_('people'))

    class Meta:
        db_table = 'content\".\"film_work'
        verbose_name = _('movie')
        verbose_name_plural = _('movies')

    def __str__(self):
        return self.title


class GenreFilmwork(UUIDMixin, TimeStampedCreateMixin):
    """
    Таблица для организации связи многие ко многим.
    """

    film_work = models.ForeignKey(
        'Filmwork', on_delete=models.CASCADE)
    genre = models.ForeignKey(
        'Genre', on_delete=models.CASCADE, verbose_name=_('genre'))

    class Meta:
        db_table = 'content\".\"genre_film_work'
        unique_together = (('film_work', 'genre'),)
        verbose_name = _('genre')
        verbose_name_plural = _('genres')


class PersonFilmwork(UUIDMixin, TimeStampedCreateMixin):
    """
    Таблица для организации связи многие ко многим.
    """

    film_work = models.ForeignKey(
        'Filmwork', on_delete=models.CASCADE)
    person = models.ForeignKey(
        'Person', on_delete=models.CASCADE, verbose_name=_('person'))
    role = models.TextField(_('role'))

    class Meta:
        db_table = 'content\".\"person_film_work'
        unique_together = (('film_work', 'person', 'role'),)
        verbose_name = _('person')
        verbose_name_plural = _('people')
