from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractUser, Group, Permission

class ScrapingProgress(models.Model):
    progress = models.IntegerField(default=0)
    total_steps=models.IntegerField(default=0)
    step=models.IntegerField(default=0)
    data = models.TextField(null=True, blank=True)
    
class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Person(models.Model):
    url = models.URLField(max_length=2048, default='invalid url')
    email = models.EmailField(max_length=255, null=True, blank=True, default='SMTP E515 : Email Not Found')
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    img_url = models.URLField(max_length=2048)

    class Meta:
        unique_together = ('name', 'company')

class CustomUser(AbstractUser):
    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',  # Change related_name to avoid conflict
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_permissions_set',  # Change related_name to avoid conflict
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    linkedin_profile = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.user.username
