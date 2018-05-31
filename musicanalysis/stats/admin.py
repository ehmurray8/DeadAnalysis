from django.contrib import admin
from .models import Tour, Set, Song, Concert, Venue

# Register your models here.
admin.site.register(Tour)
admin.site.register(Set)
admin.site.register(Song)
admin.site.register(Concert)
admin.site.register(Venue)
