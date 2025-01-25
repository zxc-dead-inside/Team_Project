from django.urls import include, path

urlpatterns = [
    path('admin/', include('movies.api.v1.admin.urls')),
]
