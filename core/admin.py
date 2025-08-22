from django.contrib import admin
from .models import GroupProfiles

@admin.register(GroupProfiles)
class GroupProfilesAdmin(admin.ModelAdmin):
    list_display = ('group', 'description')  # Fields to display in the list view
    search_fields = ('group__name', 'description')  # Enable search by group name and description