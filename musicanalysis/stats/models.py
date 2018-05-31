from django.db import models

# Create your models here.

class Tour():
    tour_name = models.CharField(max_length=200)


class Set():
