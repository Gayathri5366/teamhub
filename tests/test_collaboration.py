"""
Tests for TeamHub collaboration application.
Covers models, forms, and views for CI/CD pipeline validation.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from collaboration.models import CollaborationSpace, SpaceMember, SharedNote
from collaboration.forms import SpaceCreateForm, AddMemberForm, SharedNoteForm


class CollaborationSpaceModelTest(TestCase):
    """Tests for the CollaborationSpace model."""

    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='testpass123')
        self.member_user = User.objects.create_user(username='member', password='testpass123')
        self.space = CollaborationSpace.objects.create(
            name='Test Space',
            description='A test collaboration space',
            owner=self.owner
        )

    def test_space_creation(self):
        """Test that a space is created with correct defaults."""
        self.assertEqual(self.space.name, 'Test Space')
        self.assertEqual(self.space.status, CollaborationSpace.STATUS_ACTIVE)
        self.assertEqual(self.space.owner, self.owner)

    def test_is_member_owner(self):
        """Owner should always be considered a member."""
        self.assertTrue(self.space.is_member(self.owner))

    def test_is_member_added(self):
        """A user added as a SpaceMember should be detected as a member."""
        SpaceMember.objects.create(space=self.space, user=self.member_user, role='editor')
        self.assertTrue(self.space.is_member(self.member_user))

    def test_is_not_member(self):
        """A user not added should not be a member."""
        stranger = User.objects.create_user(username='stranger', password='testpass123')
        self.assertFalse(self.space.is_member(stranger))

    def test_get_user_role_owner(self):
        """Owner's role should return 'admin'."""
        self.assertEqual(self.space.get_user_role(self.owner), 'admin')

    def test_get_user_role_member(self):
        """SpaceMember role should be correctly returned."""
        SpaceMember.objects.create(space=self.space, user=self.member_user, role='viewer')
        self.assertEqual(self.space.get_user_role(self.member_user), 'viewer')

    def test_space_str(self):
        """String representation should include name and owner."""
        self.assertIn('Test Space', str(self.space))
        self.assertIn('owner', str(self.space))


class SharedNoteModelTest(TestCase):
    """Tests for the SharedNote model."""

    def setUp(self):
        self.user = User.objects.create_user(username='noteuser', password='testpass123')
        self.space = CollaborationSpace.objects.create(name='Note Space', owner=self.user)

    def test_note_creation(self):
        """Test creating a note and checking its fields."""
        note = SharedNote.objects.create(
            space=self.space,
            author=self.user,
            title='My Note',
            content='Some content here'
        )
        self.assertEqual(note.title, 'My Note')
        self.assertEqual(note.author, self.user)
        self.assertEqual(note.space, self.space)


class SpaceCreateFormTest(TestCase):
    """Tests for input validation in SpaceCreateForm."""

    def test_valid_form(self):
        """A form with valid data should be valid."""
        form = SpaceCreateForm(data={'name': 'Valid Space', 'description': 'desc'})
        self.assertTrue(form.is_valid())

    def test_name_too_short(self):
        """Name with fewer than 3 characters should fail validation."""
        form = SpaceCreateForm(data={'name': 'ab', 'description': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_name_invalid_characters(self):
        """Name with special characters should fail validation."""
        form = SpaceCreateForm(data={'name': 'Space<script>', 'description': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_description_too_long(self):
        """Description over 500 characters should fail validation."""
        long_desc = 'x' * 501
        form = SpaceCreateForm(data={'name': 'Valid Name', 'description': long_desc})
        self.assertFalse(form.is_valid())
        self.assertIn('description', form.errors)


class SpaceViewsTest(TestCase):
    """Tests for collaboration space views."""

    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='owner', password='testpass123')
        self.other = User.objects.create_user(username='other', password='testpass123')
        self.space = CollaborationSpace.objects.create(
            name='View Test Space', owner=self.owner
        )

    def test_space_list_requires_login(self):
        """Space list should redirect unauthenticated users."""
        response = self.client.get(reverse('space_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_space_list_authenticated(self):
        """Authenticated users should see the space list."""
        self.client.login(username='owner', password='testpass123')
        response = self.client.get(reverse('space_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'View Test Space')

    def test_space_detail_forbidden_for_non_member(self):
        """Non-members should receive a 403 response."""
        self.client.login(username='other', password='testpass123')
        response = self.client.get(reverse('space_detail', args=[self.space.pk]))
        self.assertEqual(response.status_code, 403)

    def test_space_create_post_valid(self):
        """Valid POST to space_create should create a space and redirect."""
        self.client.login(username='owner', password='testpass123')
        response = self.client.post(reverse('space_create'), {
            'name': 'New Space',
            'description': 'A new test space'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CollaborationSpace.objects.filter(name='New Space').exists())

    def test_space_create_post_invalid(self):
        """Invalid POST should return the form with errors."""
        self.client.login(username='owner', password='testpass123')
        response = self.client.post(reverse('space_create'), {'name': 'ab'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'at least 3')

    def test_space_archive_owner_only(self):
        """Only the owner should be able to archive a space."""
        self.client.login(username='other', password='testpass123')
        response = self.client.post(reverse('space_archive', args=[self.space.pk]))
        # Non-owner should get a 404 (space is filtered by owner)
        self.assertEqual(response.status_code, 404)

    def test_space_archive_by_owner(self):
        """Owner can archive a space."""
        self.client.login(username='owner', password='testpass123')
        self.client.post(reverse('space_archive', args=[self.space.pk]))
        self.space.refresh_from_db()
        self.assertEqual(self.space.status, CollaborationSpace.STATUS_ARCHIVED)


class MemberManagementTest(TestCase):
    """Tests for adding/removing members."""

    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='owner', password='testpass123')
        self.new_user = User.objects.create_user(username='newuser', password='testpass123')
        self.space = CollaborationSpace.objects.create(name='Member Space', owner=self.owner)

    def test_add_member(self):
        """Owner should be able to add a member."""
        self.client.login(username='owner', password='testpass123')
        self.client.post(reverse('member_add', args=[self.space.pk]), {
            'username': 'newuser',
            'role': 'editor'
        })
        self.assertTrue(SpaceMember.objects.filter(
            space=self.space, user=self.new_user
        ).exists())

    def test_add_nonexistent_user(self):
        """Adding a non-existent user should show a form error."""
        self.client.login(username='owner', password='testpass123')
        response = self.client.post(reverse('member_add', args=[self.space.pk]), {
            'username': 'ghost_user',
            'role': 'viewer'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No user found')
