"""
Collaboration models for TeamHub application.
Defines: CollaborationSpace, SpaceMember, SharedNote
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.utils import timezone


class CollaborationSpace(models.Model):
    """
    Represents a team collaboration workspace.
    Each space has an owner (creator) and can have multiple members.
    """
    STATUS_ACTIVE = 'active'
    STATUS_ARCHIVED = 'archived'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_ARCHIVED, 'Archived'),
    ]

    # Space name with length validation
    name = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(3)],
        help_text="Space name (3-100 characters)"
    )
    # Description field with length constraints
    description = models.TextField(
        blank=True,
        validators=[MaxLengthValidator(500)],
        help_text="Optional description (max 500 characters)"
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_spaces'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} (owned by {self.owner.username})"

    def is_member(self, user):
        """Check if a user is a member (or owner) of this space."""
        if self.owner == user:
            return True
        return self.members.filter(user=user).exists()

    def get_user_role(self, user):
        """Return the role of the given user in this space."""
        if self.owner == user:
            return 'admin'
        member = self.members.filter(user=user).first()
        return member.role if member else None


class SpaceMember(models.Model):
    """
    Represents a user's membership in a CollaborationSpace with a role.
    Roles: admin, editor, viewer.
    """
    ROLE_ADMIN = 'admin'
    ROLE_EDITOR = 'editor'
    ROLE_VIEWER = 'viewer'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_EDITOR, 'Editor'),
        (ROLE_VIEWER, 'Viewer'),
    ]

    space = models.ForeignKey(
        CollaborationSpace,
        on_delete=models.CASCADE,
        related_name='members'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='space_memberships'
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=ROLE_VIEWER
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevent duplicate memberships
        unique_together = ('space', 'user')
        ordering = ['joined_at']

    def __str__(self):
        return f"{self.user.username} in {self.space.name} as {self.role}"


class SharedNote(models.Model):
    """
    A shared document/note within a CollaborationSpace.
    Supports full CRUD operations by authorised members.
    """
    space = models.ForeignKey(
        CollaborationSpace,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authored_notes'
    )
    title = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(3)],
        help_text="Note title (3-200 characters)"
    )
    content = models.TextField(
        validators=[MinLengthValidator(1)],
        help_text="Note content"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} in {self.space.name}"
