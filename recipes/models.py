from django.db import models
from django.contrib.auth.models import User


class Tag(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#6366f1')
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
    rating = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipes')
    tags = models.ManyToManyField(Tag, blank=True, related_name='recipes')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
