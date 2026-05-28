import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('color', models.CharField(
                    default='#6366f1',
                    max_length=7,
                    validators=[django.core.validators.RegexValidator('^#[0-9A-Fa-f]{6}$', 'Enter a valid hex color (e.g. #6366f1)')]
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='tags',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Recipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('source_url', models.URLField(blank=True, max_length=2000, null=True)),
                ('thumbnail', models.URLField(blank=True, max_length=2000, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('ingredients', models.JSONField(default=list)),
                ('steps', models.JSONField(default=list)),
                ('notes', models.TextField(blank=True, null=True)),
                ('rating', models.IntegerField(
                    blank=True,
                    null=True,
                    validators=[
                        django.core.validators.MinValueValidator(1),
                        django.core.validators.MaxValueValidator(5),
                    ],
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='recipes',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('tags', models.ManyToManyField(blank=True, related_name='recipes', to='recipes.tag')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='tag',
            unique_together={('name', 'user')},
        ),
    ]
