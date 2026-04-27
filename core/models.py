from django.contrib.auth.models import AbstractUser
from django.db import models

class Role(models.TextChoices):
    SUPER_ADMIN = 'super_admin', 'Super Admin'
    NGO_MANAGER = 'ngo_manager', 'NGO Manager'
    VOLUNTEER = 'volunteer', 'Volunteer'
    PUBLIC = 'public', 'Public'

class NGO(models.Model):
    name = models.CharField(max_length=200, default='')
    description = models.TextField(blank=True, default='')
    city = models.CharField(max_length=100, default='')
    state = models.CharField(max_length=100, default='')
    address = models.TextField(blank=True, default='')
    email = models.EmailField(unique=True, blank=True, default='')
    phone = models.CharField(max_length=15, blank=True, default='')
    
    # Location for broadcasting
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.PUBLIC
    )
    ngo = models.ForeignKey(
        NGO,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members'
    )
    phone = models.CharField(max_length=15, blank=True, default='')
    profile_photo = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

    def is_super_admin(self):
        return self.role == Role.SUPER_ADMIN

    def is_ngo_manager(self):
        return self.role == Role.NGO_MANAGER

    def is_volunteer(self):
        return self.role == Role.VOLUNTEER

class VolunteerProfile(models.Model):
    SKILL_CHOICES = [
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('teacher', 'Teacher'),
        ('engineer', 'Engineer'),
        ('driver', 'Driver'),
        ('cook', 'Cook'),
        ('counselor', 'Counselor'),
        ('technician', 'Technician'),
        ('social_worker', 'Social Worker'),
        ('other', 'Other'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='volunteer_profile'
    )
    skills = models.CharField(max_length=500, default='')
    availability = models.BooleanField(default=True)
    location = models.CharField(max_length=200, blank=True, default='')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    tasks_completed = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - Volunteer"

    def is_available(self):
        return self.availability

class NeedReport(models.Model):

    CATEGORY_CHOICES = [
        ('health', '🏥 Health & Medical'),
        ('education', '🎓 Education'),
        ('food', '🍱 Food & Nutrition'),
        ('infrastructure', '🏗️ Infrastructure'),
        ('sanitation', '🚿 Sanitation & Water'),
        ('elderly', '👵 Elderly & Disabled Care'),
        ('other', '📌 Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('awaiting_verification', 'Awaiting Verification'),
        ('resolved', 'Resolved'),
    ]

    URGENCY_CHOICES = [
        ('high', '🔴 High'),
        ('medium', '🟡 Medium'),
        ('low', '🟢 Low'),
        ('unscored', 'Not Scored Yet'),
    ]

    SOURCE_CHOICES = [
        ('digital', 'Digital Submission'),
        ('digitized', 'Digitized Document'),
        ('public', 'Public Report'),
    ]

    # Basic info
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')

    # AI scoring
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='unscored')
    ai_recommendation = models.TextField(blank=True, default='')
    ai_scored = models.BooleanField(default=False)

    # Location
    location_name = models.CharField(max_length=200)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # Photo
    photo = models.ImageField(upload_to='needs/', blank=True, null=True)

    # Source tracking
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='digital')
    submitted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submitted_needs'
    )
    ngo = models.ForeignKey(
        NGO,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='needs'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — {self.category} ({self.urgency})"
    
class Document(models.Model):
    SOURCE_CHOICES = [
        ('photo', 'Paper Photo'),
        ('pdf', 'Scanned PDF'),
        ('sheet', 'Spreadsheet'),
    ]

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='documents'
    )
    ngo = models.ForeignKey(
        NGO,
        on_delete=models.SET_NULL,
        null=True,
        related_name='documents'
    )
    file = models.ImageField(upload_to='documents/')
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='photo')
    extracted_text = models.TextField(blank=True, default='')
    extracted_title = models.CharField(max_length=200, blank=True, default='')
    extracted_category = models.CharField(max_length=50, blank=True, default='')
    extracted_location = models.CharField(max_length=200, blank=True, default='')
    extracted_urgency = models.CharField(max_length=20, blank=True, default='')
    is_converted = models.BooleanField(default=False)
    linked_need = models.ForeignKey(
        NeedReport,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_documents'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Document by {self.uploaded_by} — {self.source_type}"
    
class Assignment(models.Model):
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    need = models.ForeignKey(
        NeedReport,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    volunteer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_assignments'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='assigned'
    )
    ai_recommendation = models.TextField(blank=True, default='')
    notes = models.TextField(blank=True, default='')
    completion_photo = models.ImageField(
        upload_to='completions/',
        blank=True,
        null=True
    )
    completion_notes = models.TextField(blank=True, default='')
    assigned_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Manager Verification
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.need.title} → {self.volunteer.username}"