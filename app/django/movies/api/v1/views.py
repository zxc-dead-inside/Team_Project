from django.http import HttpResponse, JsonResponse, Http404
from django.views import View
from django.contrib.postgres.aggregates import ArrayAgg
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q, Value
from django.db.models.functions import Coalesce
from django.views.generic.list import BaseListView
from django.views.generic.detail import BaseDetailView
from movies.models import FilmWork


def api(request):
    return HttpResponse("My best API")


class MoviesListApiTestPage(View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        # Получение и обработка данных
        return JsonResponse({})


class MoviesApiMixin:
    model = FilmWork
    http_method_names = ["get"]
    paginate_by = 50

    def get_queryset(self):
        return self.model.objects.all()

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context, safe=False)


class MoviesListApi(MoviesApiMixin, BaseListView):
    def get_context_data(self, *, object_list=None, **kwargs):
        queryset = object_list or self.get_queryset()

        paginator = Paginator(queryset, self.paginate_by)

        page_number = self.request.GET.get("page", 1)
        if page_number == "last":
            page_number = paginator.num_pages

        try:
            page_number = int(page_number)
            page = paginator.page(page_number)
        except (ValueError, EmptyPage):
            page = paginator.page(paginator.num_pages)

        results = (
            page.object_list.prefetch_related("genres", "persons")
            .values("id", "title", "description", "creation_date", "rating", "type")
            .annotate(
                genres=Coalesce(ArrayAgg("genres__name", distinct=True), Value([])),
                actors=Coalesce(
                    ArrayAgg(
                        "persons__full_name",
                        filter=Q(personfilmwork__role="actor"),
                        distinct=True,
                    ),
                    Value([]),
                ),
                directors=Coalesce(
                    ArrayAgg(
                        "persons__full_name",
                        filter=Q(personfilmwork__role="director"),
                        distinct=True,
                    ),
                    Value([]),
                ),
                writers=Coalesce(
                    ArrayAgg(
                        "persons__full_name",
                        filter=Q(personfilmwork__role="writer"),
                        distinct=True,
                    ),
                    Value([]),
                ),
            )
        )

        context = {
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "prev": page.previous_page_number() if page.has_previous() else None,
            "next": page.next_page_number() if page.has_next() else None,
            "results": list(results),
        }
        return context


class MoviesDetailApi(MoviesApiMixin, BaseDetailView):
    def get_object(self):
        id = self.kwargs.get("pk")
        try:
            return (
                self.model.objects.prefetch_related("genres", "persons")
                .annotate(
                    genres_names=Coalesce(
                        ArrayAgg("genres__name", distinct=True), Value([])
                    ),
                    actors_names=Coalesce(
                        ArrayAgg(
                            "persons__full_name",
                            filter=Q(personfilmwork__role="actor"),
                            distinct=True,
                        ),
                        Value([]),
                    ),
                    directors_names=Coalesce(
                        ArrayAgg(
                            "persons__full_name",
                            filter=Q(personfilmwork__role="director"),
                            distinct=True,
                        ),
                        Value([]),
                    ),
                    writers_names=Coalesce(
                        ArrayAgg(
                            "persons__full_name",
                            filter=Q(personfilmwork__role="writer"),
                            distinct=True,
                        ),
                        Value([]),
                    ),
                )
                .get(id=id)
            )
        except self.model.DoesNotExist:
            raise Http404("Filmwork not found")

    def get_context_data(self, **kwargs):
        obj = self.get_object()
        context = {
            "id": str(obj.id),
            "title": obj.title,
            "description": obj.description,
            "creation_date": obj.creation_date,
            "rating": float(obj.rating) if obj.rating else None,
            "type": obj.type,
            "genres": obj.genres_names,
            "actors": obj.actors_names,
            "directors": obj.directors_names,
            "writers": obj.writers_names,
        }
        return context
