from django.contrib import admin
from .models import PlayerSearchHistory, UserProfile

class PlayerSearchHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'player_name', 'position', 'team', 'search_timestamp']
    list_filter = ['user', 'position', 'team']
    search_fields = ['user__username', 'first_name', 'last_name', 'team']

    def player_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    player_name.short_description = 'Player Name'

admin.site.register(PlayerSearchHistory, PlayerSearchHistoryAdmin)



class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'first_name', 'last_name', 'date_of_birth', 'created_time']
    search_fields = ['user__username', 'first_name', 'last_name']
    list_filter = ['user__is_staff', 'user__is_superuser']

admin.site.register(UserProfile, UserProfileAdmin)
