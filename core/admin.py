from django.contrib import admin
from .models import GroupProfiles

from django.contrib import admin
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.html import format_html


@admin.register(GroupProfiles)
class GroupProfilesAdmin(admin.ModelAdmin):
    list_display = ('group', 'description')  # Fields to display in the list view
    search_fields = ('group__name', 'description')  # Enable search by group name and description

