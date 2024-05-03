from django.db import models
from datetime import datetime
from django.contrib.auth.models import User

# Create your models here.

# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    date_of_birth = models.DateField(default=datetime.now)
    created_time = models.DateTimeField(auto_now_add=True)




class Past_Searches(models.Model):
    search_id = models.AutoField(primary_key=True)
    user_id = models.IntegerField()
    player_first_name = models.CharField(max_length=30)
    player_last_name = models.CharField(max_length=30)
    postion = models.CharField(max_length=30)
    rank = models.IntegerField()
    projected_points = models.SmallIntegerField()

