from django.urls import path

from . import views

app_name = 'stats'
urlpatterns = [
    path('', views.index, name='index'),
    path('status/', views.status, name='status'),
    path('<str:artist>/initial/', views.initial, name='initial'),
    path('<str:artist>/', views.artist, name='artist'),
    path('<str:artist>/locations', views.venue_locations, name='venue_locations')
]