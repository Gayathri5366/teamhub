"""
Views for TeamHub collaboration module.
Implements full CRUD for spaces, members, and notes.
All views require authentication.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponseForbidden

from .models import CollaborationSpace, SpaceMember, SharedNote
from .forms import (
    SpaceCreateForm, SpaceUpdateForm,
    AddMemberForm, UpdateMemberRoleForm, SharedNoteForm
)


# ─── Collaboration Space CRUD ────────────────────────────────────────────────

@login_required
def space_list(request):
    """
    Display all active spaces where the current user is owner or member.
    Also shows archived spaces in a separate section.
    """
    user = request.user
    # Spaces where user is the owner
    owned_spaces = CollaborationSpace.objects.filter(owner=user)
    # Spaces where user is a member (not owner)
    member_spaces = CollaborationSpace.objects.filter(
        members__user=user
    ).exclude(owner=user)

    # Combine and separate by status
    all_active = (owned_spaces | member_spaces).filter(
        status=CollaborationSpace.STATUS_ACTIVE
    ).distinct().order_by('-created_at')

    all_archived = (owned_spaces | member_spaces).filter(
        status=CollaborationSpace.STATUS_ARCHIVED
    ).distinct().order_by('-updated_at')

    return render(request, 'collaboration/space_list.html', {
        'active_spaces': all_active,
        'archived_spaces': all_archived,
    })


@login_required
def space_create(request):
    """Create a new collaboration space. The current user becomes the owner."""
    if request.method == 'POST':
        form = SpaceCreateForm(request.POST)
        if form.is_valid():
            space = form.save(commit=False)
            space.owner = request.user
            space.save()
            messages.success(request, f'Space "{space.name}" created successfully!')
            return redirect('space_detail', pk=space.pk)
    else:
        form = SpaceCreateForm()
    return render(request, 'collaboration/space_form.html', {
        'form': form,
        'action': 'Create',
        'title': 'Create New Space',
    })


@login_required
def space_detail(request, pk):
    """View a collaboration space and its notes. Members-only access."""
    space = get_object_or_404(CollaborationSpace, pk=pk)

    # Check that the requesting user is a member or owner
    if not space.is_member(request.user):
        return HttpResponseForbidden("You are not a member of this space.")

    members = space.members.select_related('user').all()
    notes = space.notes.select_related('author').all()
    user_role = space.get_user_role(request.user)

    return render(request, 'collaboration/space_detail.html', {
        'space': space,
        'members': members,
        'notes': notes,
        'user_role': user_role,
        'is_owner': space.owner == request.user,
    })


@login_required
def space_edit(request, pk):
    """Edit an existing collaboration space. Owner-only access."""
    space = get_object_or_404(CollaborationSpace, pk=pk, owner=request.user)

    if request.method == 'POST':
        form = SpaceUpdateForm(request.POST, instance=space)
        if form.is_valid():
            form.save()
            messages.success(request, f'Space "{space.name}" updated successfully!')
            return redirect('space_detail', pk=space.pk)
    else:
        form = SpaceUpdateForm(instance=space)

    return render(request, 'collaboration/space_form.html', {
        'form': form,
        'action': 'Update',
        'title': f'Edit Space: {space.name}',
        'space': space,
    })


@login_required
def space_archive(request, pk):
    """Archive a collaboration space. Owner-only action via POST."""
    space = get_object_or_404(CollaborationSpace, pk=pk, owner=request.user)
    if request.method == 'POST':
        space.status = CollaborationSpace.STATUS_ARCHIVED
        space.save()
        messages.success(request, f'Space "{space.name}" has been archived.')
    return redirect('space_list')


@login_required
def space_delete(request, pk):
    """Permanently delete a collaboration space. Owner-only via POST."""
    space = get_object_or_404(CollaborationSpace, pk=pk, owner=request.user)
    if request.method == 'POST':
        name = space.name
        space.delete()
        messages.success(request, f'Space "{name}" has been permanently deleted.')
        return redirect('space_list')
    return render(request, 'collaboration/space_confirm_delete.html', {'space': space})


# ─── Member Management ────────────────────────────────────────────────────────

@login_required
def member_add(request, pk):
    """Add a new member to a space. Only the space owner can add members."""
    space = get_object_or_404(CollaborationSpace, pk=pk, owner=request.user)

    if request.method == 'POST':
        form = AddMemberForm(request.POST, space=space)
        if form.is_valid():
            username = form.cleaned_data['username']
            role = form.cleaned_data['role']
            user = User.objects.get(username=username)
            SpaceMember.objects.create(space=space, user=user, role=role)
            messages.success(request, f'User "{username}" added as {role}.')
            return redirect('space_detail', pk=space.pk)
    else:
        form = AddMemberForm(space=space)

    # Pass all users who can still be added (excludes owner + current members)
    existing_ids = list(space.members.values_list('user_id', flat=True))
    available_users = User.objects.exclude(
        pk__in=existing_ids
    ).exclude(pk=space.owner.pk).order_by('username')

    return render(request, 'collaboration/member_form.html', {
        'form': form,
        'space': space,
        'title': 'Add Member',
        'available_users': available_users,
    })


@login_required
def member_update_role(request, pk, member_pk):
    """Update a member's role. Only the space owner can change roles."""
    space = get_object_or_404(CollaborationSpace, pk=pk, owner=request.user)
    member = get_object_or_404(SpaceMember, pk=member_pk, space=space)

    if request.method == 'POST':
        form = UpdateMemberRoleForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Role updated for "{member.user.username}" to {member.get_role_display()}.'
            )
            return redirect('space_detail', pk=space.pk)
    else:
        form = UpdateMemberRoleForm(instance=member)

    return render(request, 'collaboration/member_form.html', {
        'form': form,
        'space': space,
        'member': member,
        'title': f'Update Role for {member.user.username}',
    })


@login_required
def member_remove(request, pk, member_pk):
    """Remove a member from a space. Owner-only via POST."""
    space = get_object_or_404(CollaborationSpace, pk=pk, owner=request.user)
    member = get_object_or_404(SpaceMember, pk=member_pk, space=space)

    if request.method == 'POST':
        username = member.user.username
        member.delete()
        messages.success(request, f'User "{username}" removed from the space.')
        return redirect('space_detail', pk=space.pk)

    return render(request, 'collaboration/member_confirm_remove.html', {
        'space': space,
        'member': member,
    })


# ─── Shared Notes CRUD ────────────────────────────────────────────────────────

@login_required
def note_create(request, space_pk):
    """Create a new note in a space. Admin and Editor roles can create notes."""
    space = get_object_or_404(CollaborationSpace, pk=space_pk)

    # Check membership and permissions
    if not space.is_member(request.user):
        return HttpResponseForbidden("You are not a member of this space.")

    role = space.get_user_role(request.user)
    if role not in ('admin', 'editor'):
        messages.error(request, "Only Admins and Editors can create notes.")
        return redirect('space_detail', pk=space_pk)

    if request.method == 'POST':
        form = SharedNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.space = space
            note.author = request.user
            note.save()
            messages.success(request, f'Note "{note.title}" created!')
            return redirect('space_detail', pk=space_pk)
    else:
        form = SharedNoteForm()

    return render(request, 'collaboration/note_form.html', {
        'form': form,
        'space': space,
        'action': 'Create',
        'title': 'Create New Note',
    })


@login_required
def note_edit(request, space_pk, note_pk):
    """Edit an existing note. Author or space Admin can edit."""
    space = get_object_or_404(CollaborationSpace, pk=space_pk)
    note = get_object_or_404(SharedNote, pk=note_pk, space=space)

    if not space.is_member(request.user):
        return HttpResponseForbidden("You are not a member of this space.")

    # Only the note author or space admin/owner can edit
    role = space.get_user_role(request.user)
    if note.author != request.user and role not in ('admin',):
        messages.error(request, "You can only edit your own notes.")
        return redirect('space_detail', pk=space_pk)

    if request.method == 'POST':
        form = SharedNoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            messages.success(request, f'Note "{note.title}" updated!')
            return redirect('space_detail', pk=space_pk)
    else:
        form = SharedNoteForm(instance=note)

    return render(request, 'collaboration/note_form.html', {
        'form': form,
        'space': space,
        'note': note,
        'action': 'Edit',
        'title': f'Edit Note: {note.title}',
    })


@login_required
def note_delete(request, space_pk, note_pk):
    """Delete a note. Author or space Admin can delete."""
    space = get_object_or_404(CollaborationSpace, pk=space_pk)
    note = get_object_or_404(SharedNote, pk=note_pk, space=space)

    if not space.is_member(request.user):
        return HttpResponseForbidden("You are not a member of this space.")

    role = space.get_user_role(request.user)
    if note.author != request.user and role not in ('admin',):
        messages.error(request, "You can only delete your own notes.")
        return redirect('space_detail', pk=space_pk)

    if request.method == 'POST':
        title = note.title
        note.delete()
        messages.success(request, f'Note "{title}" deleted.')
        return redirect('space_detail', pk=space_pk)

    return render(request, 'collaboration/note_confirm_delete.html', {
        'space': space,
        'note': note,
    })
