from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    last_csv = models.TextField(max_length=1000, blank=True)
