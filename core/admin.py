from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, NGO, VolunteerProfile, NeedReport
from .models import User, NGO, VolunteerProfile, NeedReport, Document
from .models import User, NGO, VolunteerProfile, NeedReport, Document, Assignment
admin.site.register(Assignment)
admin.site.register(Document)
admin.site.register(NGO)
admin.site.register(VolunteerProfile)
admin.site.register(NeedReport)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'ngo']
    list_filter = ['role']
    fieldsets = UserAdmin.fieldsets + (
        ('UnityAid Info', {
            'fields': ('role', 'ngo', 'phone', 'profile_photo')
        }),
    )