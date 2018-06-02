from django.contrib import admin
from .models import Tour, Set, Song, Concert, Venue, Artist, SetlistFMStatus

# Register your models here.
class SongAdmin(admin.ModelAdmin):
    model = Song
    search_fields = ('song_name', 'orig_artist__name',)

class ConcertAdmin(admin.ModelAdmin):
    model = Concert
    filter_horizontal = ('sets', 'encores')
    search_fields = ['artist__name',]

class SetAdmin(admin.ModelAdmin):
    model = Set
    filter_horizontal = ('songs',)

admin.site.register(Tour)
admin.site.register(Set, SetAdmin)
admin.site.register(Song, SongAdmin)
admin.site.register(Concert, ConcertAdmin)
admin.site.register(Venue)
admin.site.register(Artist)
admin.site.register(SetlistFMStatus)