from django.db import models


# Create your models here.
class Artist(models.Model):
    name = models.CharField(max_length=200)
    mbid = models.CharField(max_length=200, null=True)

    def __str__(self):
        return self.name


class SetlistFMStatus(models.Model):
    finished = models.BooleanField(default=False)
    started = models.DateTimeField(auto_now_add=True, blank=True)
    published = models.DateTimeField(null=True)
    current_page = models.IntegerField(default=0)
    final_page = models.IntegerField(default=1)
    exists = models.BooleanField(default=True)
    alerted = models.BooleanField(default=False)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return "{} - Finished Downloading({})".format(self.artist.name, self.finished)


class Song(models.Model):
    song_name = models.CharField(max_length=200)
    orig_artist = models.ForeignKey(Artist, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.song_name


class Set(models.Model):
    songs = models.ManyToManyField(Song)

    def __str__(self):
        return ", ".join([str(song) for song in self.songs.all()])


class Venue(models.Model):
    name = models.CharField(max_length=200, unique=True)
    city = models.CharField(max_length=200, null=True)
    state = models.CharField(max_length=200, null=True)
    state_code = models.CharField(max_length=25, null=True)
    country = models.CharField(max_length=200)
    country_code = models.CharField(max_length=25)
    latitude = models.FloatField()
    longitude = models.FloatField()
    fips = models.CharField(max_length=10)

    def __str__(self):
        try:
            int(self.state_code)
            return "{}, {}, {}".format(self.name, self.city, self.country)
        except ValueError:
            return "{}, {}, {}".format(self.name, self.city, self.state)


class Tour(models.Model):
    tour_name = models.CharField(max_length=200)

    def __str__(self):
        return self.tour_name


class Concert(models.Model):
    date = models.DateField()
    sets = models.ManyToManyField(Set)
    encores = models.ManyToManyField(Song)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, null=True)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, null=True)
    tour = models.ForeignKey(Tour, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return "{} Show".format(self.date)
