from django.urls import path

from movies.api.v1.admin import views

urlpatterns = [
    path('movies/', views.MoviesListApi.as_view()),
    path('movies/<uuid:pk>/', views.MoviesDetailApi.as_view()),
]
