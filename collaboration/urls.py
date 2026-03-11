"""
URL patterns for TeamHub collaboration module.
"""
from django.urls import path
from . import views

urlpatterns = [
    # ── Spaces ──────────────────────────────────────────────────────────────
    path('', views.space_list, name='space_list'),
    path('create/', views.space_create, name='space_create'),
    path('<int:pk>/', views.space_detail, name='space_detail'),
    path('<int:pk>/edit/', views.space_edit, name='space_edit'),
    path('<int:pk>/archive/', views.space_archive, name='space_archive'),
    path('<int:pk>/delete/', views.space_delete, name='space_delete'),

    # ── Members ──────────────────────────────────────────────────────────────
    path('<int:pk>/members/add/', views.member_add, name='member_add'),
    path('<int:pk>/members/<int:member_pk>/role/', views.member_update_role, name='member_update_role'),
    path('<int:pk>/members/<int:member_pk>/remove/', views.member_remove, name='member_remove'),

    # ── Notes ────────────────────────────────────────────────────────────────
    path('<int:space_pk>/notes/create/', views.note_create, name='note_create'),
    path('<int:space_pk>/notes/<int:note_pk>/edit/', views.note_edit, name='note_edit'),
    path('<int:space_pk>/notes/<int:note_pk>/delete/', views.note_delete, name='note_delete'),
]
