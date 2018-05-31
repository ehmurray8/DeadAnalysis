from django.db import models
import datetime

# Create your models here.

class Tour(models.Model):
    tour_name = models.CharField(max_length=200)

    def __str__(self):
        return self.tour_name


class Set(models.Model):
    pass

class Song(models.Model):
    song_name = models.CharField(max_length=200)
    artist = models.CharField(max_length=200)
    orig_artist = models.CharField(max_length=200)
    sets = models.ManyToManyField(Set)

    def is_cover(self):
        return self.artist != self.orig_artist

    def __str__(self):
        return self.song_name

class Concert(models.Model):
    date = models.DateField()
    tour = models.ForeignKey(Tour, on_delete=models.SET_NULL, null=True)
    sets = models.ManyToManyField(Set)
    encores = models.ManyToManyField(Song)

    def __str__(self):
        return "{} Show".format(self.date)


class Venue(models.Model):
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    state = models.CharField(max_length=200)
    state_code = models.CharField(max_length=25)
    country = models.CharField(max_length=200)
    country_code = models.CharField(max_length=25)
    latitude = models.FloatField()
    longitude = models.FloatField()
    fips = models.CharField(max_length=10)
    concert = models.ForeignKey(Concert, on_delete=models.CASCADE)

    def __str__(self):
        try:
            int(self.clean_fields().get('state_code'))
            return "{}, {}, {}".format(self.name, self.city, self.country)
        except ValueError:
            return "{}, {}, {}".format(self.name, self.city, self.state)
