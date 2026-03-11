"""
Admin configuration for TeamHub collaboration module.
Registers models for Django admin interface.
"""
from django.contrib import admin
from .models import CollaborationSpace, SpaceMember, SharedNote


@admin.register(CollaborationSpace)
class CollaborationSpaceAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'owner__username']


@admin.register(SpaceMember)
class SpaceMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'space', 'role', 'joined_at']
    list_filter = ['role']
    search_fields = ['user__username', 'space__name']


@admin.register(SharedNote)
class SharedNoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'space', 'author', 'updated_at']
    search_fields = ['title', 'author__username']
