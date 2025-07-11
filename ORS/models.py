from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.conf import settings

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)  # Store hashed password
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Preference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    preference_name = models.CharField(max_length=100)  # e.g., "style", "color_palette", etc.
    preference_value = ArrayField(
        base_field=models.CharField(max_length=100),
        default=list,
        blank=False,
        help_text="List of selected values for this preference (e.g., ['blue', 'green'])"
    )

    class Meta:
        unique_together = ('user', 'preference_name')  # One entry per user per category

    def __str__(self):
        return f"{self.user.username} - {self.preference_name}: {self.preference_value}"

