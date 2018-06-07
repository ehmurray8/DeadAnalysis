from django.urls import path

from . import views

app_name = 'stats'
urlpatterns = [
    path('', views.index, name='index'),
    path('status/', views.status, name='status'),
    path('<str:artist>/initial/', views.initial, name='initial'),
    path('<str:artist>/', views.artist, name='artist'),
    path('<str:artist>/venue-locations', views.venue_locations, name='venue_locations'),
    path('<str:artist>/typical-concert', views.typical_concert, name='typical_concert'),
    path('<str:artist>/locations', views.locations, name='locations'),
    path('<str:artist>/songs', views.songs, name='songs'),
    path('<str:artist>/covers', views.covers, name='covers'),
    path('<str:artist>/tours', views.tours, name='tours'),
    path('<str:artist>/venues', views.venues, name='venues'),
    path('<str:artist>/songs_by', views.songs_by, name='songs_by')
]