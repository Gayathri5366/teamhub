from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CollaborationSpace',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(
                    help_text='Space name (3-100 characters)',
                    max_length=100,
                    validators=[django.core.validators.MinLengthValidator(3)]
                )),
                ('description', models.TextField(
                    blank=True,
                    help_text='Optional description (max 500 characters)',
                    validators=[django.core.validators.MaxLengthValidator(500)]
                )),
                ('status', models.CharField(
                    choices=[('active', 'Active'), ('archived', 'Archived')],
                    default='active',
                    max_length=10
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='owned_spaces',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='SpaceMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(
                    choices=[('admin', 'Admin'), ('editor', 'Editor'), ('viewer', 'Viewer')],
                    default='viewer',
                    max_length=10
                )),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('space', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='members',
                    to='collaboration.collaborationspace'
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='space_memberships',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={'ordering': ['joined_at'], 'unique_together': {('space', 'user')}},
        ),
        migrations.CreateModel(
            name='SharedNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(
                    help_text='Note title (3-200 characters)',
                    max_length=200,
                    validators=[django.core.validators.MinLengthValidator(3)]
                )),
                ('content', models.TextField(
                    help_text='Note content',
                    validators=[django.core.validators.MinLengthValidator(1)]
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='authored_notes',
                    to=settings.AUTH_USER_MODEL
                )),
                ('space', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notes',
                    to='collaboration.collaborationspace'
                )),
            ],
            options={'ordering': ['-updated_at']},
        ),
    ]
