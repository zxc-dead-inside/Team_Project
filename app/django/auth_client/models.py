# import uuid
# from django.db import models
# from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


# class CustomUserManager(BaseUserManager):
#     def create_user(self, username, email, password=None, **extra_fields):
#         if not email:
#             raise ValueError('Users must have an email address')
        
#         email = self.normalize_email(email)
#         user = self.model(username=username, email=email, **extra_fields)
#         if password:
#             user.set_password(password)
#         user.save(using=self._db)
#         return user

#     def create_superuser(self, username, email, password=None, **extra_fields):
#         extra_fields.setdefault('is_staff', True)
#         extra_fields.setdefault('is_superuser', True)
#         extra_fields.setdefault('is_active', True)
        
#         return self.create_user(username, email, password, **extra_fields)


# class CustomUser(AbstractBaseUser, PermissionsMixin):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     username = models.CharField(max_length=150, unique=True)
#     email = models.EmailField(unique=True)
#     first_name = models.CharField(max_length=150, blank=True)
#     last_name = models.CharField(max_length=150, blank=True)
    
#     # Django specific fields
#     is_active = models.BooleanField(default=True)
#     is_staff = models.BooleanField(default=False)
#     date_joined = models.DateTimeField(auto_now_add=True)
    
#     # Auth service specific fields
#     token_version = models.IntegerField(default=0)
    
#     objects = CustomUserManager()
    
#     USERNAME_FIELD = 'username'
#     EMAIL_FIELD = 'email'
#     REQUIRED_FIELDS = ['email']
    
#     def __str__(self):
#         return f"{self.username} ({self.email})"


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

