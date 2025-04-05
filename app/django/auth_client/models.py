import uuid

from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    """Profile model that extends the default User model with additional fields."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token_version = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username}'s profile"

