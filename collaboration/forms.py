"""
Forms for TeamHub collaboration module.
All forms include server-side input validation.
"""
import re
from django import forms
from django.contrib.auth.models import User
from .models import CollaborationSpace, SpaceMember, SharedNote


class SpaceCreateForm(forms.ModelForm):
    """
    Form for creating a new collaboration space.
    Validates name (alphanumeric + spaces) and description length.
    """

    class Meta:
        model = CollaborationSpace
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter space name (min 3 characters)',
                'minlength': '3',
                'maxlength': '100',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Optional description (max 500 characters)',
                'rows': 3,
                'maxlength': '500',
            }),
        }

    def clean_name(self):
        """Validate that the space name contains only safe characters."""
        name = self.cleaned_data.get('name', '').strip()
        if len(name) < 3:
            raise forms.ValidationError("Space name must be at least 3 characters long.")
        if len(name) > 100:
            raise forms.ValidationError("Space name cannot exceed 100 characters.")
        # Allow alphanumeric characters, spaces, hyphens, and underscores only
        if not re.match(r'^[\w\s\-]+$', name):
            raise forms.ValidationError(
                "Space name may only contain letters, numbers, spaces, hyphens, and underscores."
            )
        return name

    def clean_description(self):
        """Validate description length."""
        description = self.cleaned_data.get('description', '').strip()
        if len(description) > 500:
            raise forms.ValidationError("Description cannot exceed 500 characters.")
        return description


class SpaceUpdateForm(SpaceCreateForm):
    """
    Form for updating an existing collaboration space.
    Adds ability to update status (archive/reactivate).
    """

    class Meta(SpaceCreateForm.Meta):
        fields = ['name', 'description', 'status']
        widgets = {
            **SpaceCreateForm.Meta.widgets,
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class AddMemberForm(forms.Form):
    """
    Form to add a user to a collaboration space with a specific role.
    Validates that the username exists and is not already a member.
    """
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username',
        })
    )
    role = forms.ChoiceField(
        choices=SpaceMember.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, space=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Store space for validation context
        self.space = space

    def clean_username(self):
        """Validate that the user exists and is not already a member."""
        username = self.cleaned_data.get('username', '').strip()
        if not username:
            raise forms.ValidationError("Username cannot be empty.")
        # Check if user exists
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError(f"No user found with username '{username}'.")
        # Check if user is already a member/owner
        if self.space:
            if self.space.owner == user:
                raise forms.ValidationError("This user is the owner of this space.")
            if self.space.members.filter(user=user).exists():
                raise forms.ValidationError("This user is already a member of this space.")
        return username


class UpdateMemberRoleForm(forms.ModelForm):
    """
    Form to update a space member's role.
    """
    class Meta:
        model = SpaceMember
        fields = ['role']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
        }


class SharedNoteForm(forms.ModelForm):
    """
    Form for creating and editing shared notes.
    Validates title and content fields.
    """

    class Meta:
        model = SharedNote
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Note title (min 3 characters)',
                'minlength': '3',
                'maxlength': '200',
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Write your note here...',
                'rows': 8,
            }),
        }

    def clean_title(self):
        """Validate note title."""
        title = self.cleaned_data.get('title', '').strip()
        if len(title) < 3:
            raise forms.ValidationError("Note title must be at least 3 characters.")
        if len(title) > 200:
            raise forms.ValidationError("Note title cannot exceed 200 characters.")
        return title

    def clean_content(self):
        """Validate note content is not empty."""
        content = self.cleaned_data.get('content', '').strip()
        if not content:
            raise forms.ValidationError("Note content cannot be empty.")
        return content
