import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unityaid.settings')
django.setup()

from core.models import User, VolunteerProfile, Assignment

print("--- Volunteer Availability Audit ---")
volunteers = VolunteerProfile.objects.all()
for vp in volunteers:
    active_assignments = Assignment.objects.filter(
        volunteer=vp.user,
        status__in=['accepted', 'in_progress']
    )
    assignment_count = active_assignments.count()
    print(f"Volunteer: {vp.user.username}")
    print(f"  Field availability: {vp.availability}")
    print(f"  Active assignments: {assignment_count}")
    for a in active_assignments:
        print(f"    - Need: {a.need.title} (Status: {a.status})")
    
    # Check for inconsistency
    if vp.availability and assignment_count > 0:
        print("  !!! INCONSISTENCY DETECTED: Should be BUSY !!!")
    elif not vp.availability and assignment_count == 0:
        print("  (Busy but no active assignments - manual setting?)")
    print("-" * 30)
