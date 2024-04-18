from django.db import models
from datetime import datetime

# Create your models here.

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    user_first_name = models.CharField(max_length=30)
    user_last_name = models.CharField(max_length=30)
    date_of_birth = models.DateField(db_default=datetime.now())

class Past_Searches(models.Model):
    search_id = models.AutoField(primary_key=True)
    user_id = models.IntegerField()
    player_first_name = models.CharField(max_length=30)
    player_last_name = models.CharField(max_length=30)
    postion = models.CharField(max_length=30)
    rank = models.IntegerField()
    projected_points = models.SmallIntegerField()

