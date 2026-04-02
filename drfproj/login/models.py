from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import CustomUserManager
from django.conf import settings


class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPES = (
        (1, 'SuperAdmin'),
        (2, 'Admin'),
        (3, 'User'),
    )

    user_type = models.PositiveSmallIntegerField(
    choices=USER_TYPES,
    default=3
     )
    username = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(unique=True)

    verification_token = models.CharField(max_length=100, null=True, blank=True)

    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    is_verified = models.BooleanField(default=False)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    max_score = models.IntegerField(default=100)

    def __str__(self):
        return self.name


class reports(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=True, blank=True)
    class_name = models.CharField(max_length=100, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    total_score = models.IntegerField(default=0)
    percentage = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report by {self.user.email} at {self.created_at}"


class SubjectScore(models.Model):
    report = models.ForeignKey(reports, on_delete=models.CASCADE, related_name='scores')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    score = models.IntegerField()

    class Meta:
        unique_together = ('report', 'subject')

    def __str__(self):
        return f"{self.subject.name}: {self.score}"


class pdfreport(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    report_file = models.FileField(upload_to='pdf_reports/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PDF Report for {self.user.email} at {self.created_at}"
