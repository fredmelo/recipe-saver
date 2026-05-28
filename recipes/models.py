from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.contrib.auth.models import User

_hex_color = RegexValidator(r'^#[0-9A-Fa-f]{6}$', 'Enter a valid hex color (e.g. #6366f1)')


class Tag(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#6366f1', validators=[_hex_color])
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tags')

    class Meta:
        unique_together = ('name', 'user')
        ordering = ['name']

    def __str__(self):
        return self.name


class Recipe(models.Model):
    title = models.CharField(max_length=255)
    source_url = models.URLField(blank=True, null=True, max_length=2000)
    thumbnail = models.URLField(blank=True, null=True, max_length=2000)
    description = models.TextField(blank=True, null=True)
    ingredients = models.JSONField(default=list)
    steps = models.JSONField(default=list)
    notes = models.TextField(blank=True, null=True)
    rating = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipes')
    tags = models.ManyToManyField(Tag, blank=True, related_name='recipes')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
