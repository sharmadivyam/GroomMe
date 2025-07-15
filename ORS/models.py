from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    user_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Required fields for Django admin and authentication
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.first_name


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


class WardrobeItem(models.Model):
    CATEGORY_CHOICES = [
    ('tops', 'Tops'),
    ('bottoms', 'Bottoms'),
    ('outerwear', 'Outerwear'),
    ('footwear', 'Footwear'),
    ('accessories', 'Accessories'),
    ('onepiece', 'Dresses/Jumpsuits'),
    ('bags', 'Bags/Backpacks'),
    ('sets', 'Co-ords/Suits/Sets'),  
    ]


    FABRIC_DENSITY_CHOICES = [
        ('lightweight', 'Lightweight'),
        ('medium', 'Medium'),
        ('heavy', 'Heavy'),
    ]

    PATTERN_CHOICES = [
        ('solid', 'Solid'),
        ('striped', 'Striped'),
        ('floral', 'Floral'),
        ('plaid', 'Plaid'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    color = models.CharField(max_length=50, blank=True, null=True)
    material = models.CharField(max_length=100, blank=True, null=True)
    size = models.CharField(max_length=20, blank=True, null=True)
    brand = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='wardrobe_images/', blank=True, null=True)
    added_at = models.DateTimeField(auto_now_add=True)

    is_basic_essential = models.BooleanField(default=False)
    essential_reference = models.ForeignKey(
        'EssentialItem', null=True, blank=True,
        on_delete=models.SET_NULL
    )
    
    season_suitability = ArrayField(
        base_field=models.CharField(max_length=50),
        blank=True,
        default=list,
        help_text="e.g., ['Summer', 'Spring']"
    )

    occasion_suitability = ArrayField(
        base_field=models.CharField(max_length=50),
        blank=True,
        default=list,
        help_text="e.g., ['Casual', 'Work']"
    )

    style_tags = ArrayField(
        base_field=models.CharField(max_length=50),
        blank=True,
        default=list,
        help_text="e.g., ['Bohemian', 'Minimalist']"
    )

    pattern = models.CharField(max_length=20, choices=PATTERN_CHOICES, blank=True, null=True)
    fabric_density = models.CharField(max_length=20, choices=FABRIC_DENSITY_CHOICES, blank=True, null=True)
    last_worn_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.user.email}"


class EssentialItem(models.Model):
    name = models.CharField(max_length=100, unique=True)

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='variants'
    )
    category = models.CharField(max_length=50, choices=WardrobeItem.CATEGORY_CHOICES)
    color = models.CharField(max_length=50, blank=True, null=True)
    material = models.CharField(max_length=100, blank=True, null=True)
    size = models.CharField(max_length=20, blank=True, null=True)
    brand = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='essentials/', blank=True, null=True)
    season_suitability = ArrayField(models.CharField(max_length=50), blank=True, default=list)
    occasion_suitability = ArrayField(models.CharField(max_length=50), blank=True, default=list)
    style_tags = ArrayField(models.CharField(max_length=50), blank=True, default=list)
    pattern = models.CharField(max_length=20, choices=WardrobeItem.PATTERN_CHOICES, blank=True, null=True)
    fabric_density = models.CharField(max_length=20, choices=WardrobeItem.FABRIC_DENSITY_CHOICES, blank=True, null=True)

    def __str__(self):
        return self.name
