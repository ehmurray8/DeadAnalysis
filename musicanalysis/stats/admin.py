from django.contrib import admin
from .models import Tour, Set, Song, Concert, Venue, Artist

# Register your models here.

class ConcertAdmin(admin.ModelAdmin):
    model = Concert
    filter_horizontal = ('sets', 'encores')

class SetAdmin(admin.ModelAdmin):
    model = Set
    filter_horizontal = ('songs',)

admin.site.register(Tour)
admin.site.register(Set, SetAdmin)
admin.site.register(Song)
admin.site.register(Concert, ConcertAdmin)
admin.site.register(Venue)
admin.site.register(Artist)