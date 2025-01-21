from django.http import HttpResponse
from django.http import JsonResponse
from django.views import View


def api(request):
    return HttpResponse("My best API")



class MoviesListApi(View):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        # Получение и обработка данных
        return JsonResponse({})