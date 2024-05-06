from django.db import models
from datetime import datetime
from django.contrib.auth.models import User

# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    date_of_birth = models.DateField(default=datetime.now)
    created_time = models.DateTimeField(auto_now_add=True)




class PlayerSearchHistory(models.Model):
    #Note THis is how we know who is the current user/Search history belongs too
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    player_id = models.IntegerField()  # ID of the player
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    position = models.CharField(max_length=10)
    height = models.CharField(max_length=10)
    weight = models.IntegerField()
    jersey_number = models.IntegerField()
    college = models.CharField(max_length=100)
    country = models.CharField(max_length=50)
    draft_year = models.IntegerField(null=True, blank=True)
    draft_round = models.IntegerField(null=True, blank=True)
    draft_number = models.IntegerField(null=True, blank=True)
    team = models.CharField(max_length=100)
    search_timestamp = models.DateTimeField(auto_now_add=True)  # Timestamp of the search

    def __str__(self):
        return f"{self.user.username} searched for {self.first_name} {self.last_name} - {self.team}"
