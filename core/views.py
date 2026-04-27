from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .models import User, NGO, Role, NeedReport, Document, VolunteerProfile, Assignment
from .gemini import (
    extract_from_document, 
    score_need_urgency, 
    geocode_location, 
    match_volunteers
)

# Landing page
def landing(request):
    return render(request, 'landing.html')

# Login
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            error = 'Invalid username or password'

    return render(request, 'login.html', {'error': error})

# Signup
def signup_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            error = 'Username already taken'
        elif User.objects.filter(email=email).exists():
            error = 'Email already registered'
        else:
            # Signup only creates PUBLIC users
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role=Role.PUBLIC
            )
            login(request, user)
            return redirect('dashboard')

    return render(request, 'signup.html', {'error': error})
# Logout
def logout_view(request):
    logout(request)
    return redirect('login')

# Dashboard redirect based on role
@login_required
def dashboard_redirect(request):
    user = request.user
    if user.is_superuser or user.role == Role.SUPER_ADMIN:
        return redirect('super_admin_dashboard')
    elif user.role == Role.NGO_MANAGER:
        if user.ngo and user.ngo.is_approved:
            return redirect('manager_dashboard')
        return redirect('ngo_pending')
    elif user.role == Role.VOLUNTEER:
        if user.ngo and user.ngo.is_approved:
            return redirect('volunteer_dashboard')
        return redirect('ngo_pending')
    else:
        return redirect('public_home')

def ngo_pending(request):
    return render(request, 'ngo/pending.html')
@login_required
def manager_dashboard(request):
    if not request.user.is_ngo_manager() and not request.user.is_superuser:
        return redirect('dashboard')

    ngo = request.user.ngo
    # Hide resolved reports (archived for AI history)
    needs = NeedReport.objects.filter(ngo=ngo).exclude(status='resolved').order_by('-created_at')
    
    # Filters
    category = request.GET.get('category', '')
    urgency = request.GET.get('urgency', '')
    status = request.GET.get('status', '')

    if category: needs = needs.filter(category=category)
    if urgency: needs = needs.filter(urgency=urgency)
    if status: needs = needs.filter(status=status)

    # --- Intelligence: Proactive Analysis ---
    volunteers = VolunteerProfile.objects.filter(user__ngo=ngo)
    resource_gaps = []
    response_alerts = []
    
    # 1. Gap Analysis
    for code, label in NeedReport.CATEGORY_CHOICES:
        pending_count = needs.filter(category=code, status='pending').count()
        vol_count = volunteers.filter(skills__icontains=label, availability=True).count()
        if pending_count > 0 and vol_count == 0:
            resource_gaps.append({
                'category': label,
                'count': pending_count,
                'message': f"Immediate Attention: {pending_count} {label} needs are pending, but no {label}-skilled volunteers are currently available."
            })
    
    # 2. Response Time Monitoring (30-minute threshold)
    now = timezone.now()
    thirty_mins_ago = now - timedelta(minutes=30)
    stale_assignments = Assignment.objects.filter(
        need__ngo=ngo,
        status='assigned',
        assigned_at__lt=thirty_mins_ago
    ).select_related('volunteer', 'need')
    
    for sa in stale_assignments:
        delta = now - sa.assigned_at
        mins = int(delta.total_seconds() / 60)
        response_alerts.append({
            'type': 'Acceptance Delay',
            'volunteer': sa.volunteer.username,
            'need_title': sa.need.title,
            'need_id': sa.need.id,
            'delay': f"{mins}m",
            'message': f"Volunteer {sa.volunteer.username} assigned to '{sa.need.title}' hasn't responded for {mins} minutes."
        })

    # 3. Resolution Monitoring (1-hour threshold for in-progress tasks)
    one_hour_ago = now - timedelta(hours=1)
    stalled_missions = Assignment.objects.filter(
        need__ngo=ngo,
        status__in=['accepted', 'in_progress'],
        updated_at__lt=one_hour_ago
    ).select_related('volunteer', 'need')

    for sm in stalled_missions:
        delta = now - sm.updated_at
        hrs = int(delta.total_seconds() / 3600)
        mins = int((delta.total_seconds() % 3600) / 60)
        time_str = f"{hrs}h {mins}m" if hrs > 0 else f"{mins}m"
        response_alerts.append({
            'type': 'Resolution Delay',
            'volunteer': sm.volunteer.username,
            'need_title': sm.need.title,
            'need_id': sm.need.id,
            'delay': time_str,
            'message': f"Mission '{sm.need.title}' led by {sm.volunteer.username} is stalled for {time_str} without status update."
        })

    # Summary counts
    all_needs = NeedReport.objects.filter(ngo=ngo)
    total = all_needs.count()
    high = all_needs.filter(urgency='high').count()
    pending = all_needs.filter(status='pending').count()
    resolved = all_needs.filter(status='resolved').count()

    # Map data — only needs with coordinates
    map_data = []
    for need in needs.filter(latitude__isnull=False, longitude__isnull=False):
        map_data.append({
            'title': need.title,
            'location': need.location_name,
            'category': need.get_category_display(),
            'urgency': need.urgency,
            'lat': need.latitude,
            'lng': need.longitude,
            'status': need.status,
        })

    # Broadcasted nearby public needs (unclaimed)
    broadcasted_needs = NeedReport.objects.filter(
        ngo__isnull=True
    ).order_by('-created_at')[:10]

    return render(request, 'dashboard/manager.html', {
        'ngo': ngo,
        'needs': needs,
        'total': total,
        'high': high,
        'pending': pending,
        'resolved': resolved,
        'broadcasted_needs': broadcasted_needs,
        'resource_gaps': resource_gaps,
        'response_alerts': response_alerts,
        'categories': NeedReport.CATEGORY_CHOICES,
        'map_data': json.dumps(map_data),
        'google_maps_key': settings.GOOGLE_MAPS_API_KEY,
    })
@login_required
def volunteer_dashboard(request):
    if not request.user.is_volunteer():
        return redirect('dashboard')

    try:
        profile = request.user.volunteer_profile
    except VolunteerProfile.DoesNotExist:
        profile = VolunteerProfile.objects.create(
            user=request.user,
            skills='',
            availability=True
        )

    return render(request, 'dashboard/volunteer.html', {
        'profile': profile,
    })
@login_required
def super_admin_dashboard(request):
    return render(request, 'dashboard/super_admin.html')


# Public need report (no login required)
def report_need(request):
    ngos = NGO.objects.filter(is_approved=True)
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        category = request.POST.get('category')
        location_name = request.POST.get('location_name')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        photo = request.FILES.get('photo')
        ngo_id = request.POST.get('ngo')

        need = NeedReport(
            title=title,
            description=description,
            category=category,
            location_name=location_name,
            source='public'
        )
        if latitude:
            need.latitude = float(latitude)
        if longitude:
            need.longitude = float(longitude)
        if photo:
            need.photo = photo
        if request.user.is_authenticated:
            need.submitted_by = request.user
        if ngo_id:
            try:
                need.ngo = NGO.objects.get(id=ngo_id)
            except NGO.DoesNotExist:
                pass

        need.save()
        # Auto geocode location
        if not need.latitude and location_name:
            lat, lng = geocode_location(location_name, settings.GOOGLE_MAPS_API_KEY)
            if lat:
                need.latitude = lat
                need.longitude = lng

        # Auto score with Gemini AI
        scored = score_need_urgency(title, description, category, location_name)
        need.urgency = scored.get('urgency', 'medium')
        need.ai_recommendation = scored.get('recommendation', '')
        need.ai_scored = True
        need.save()

        return redirect('report_success')

    return render(request, 'needs/report_need.html', {
        'ngos': ngos,
        'categories': NeedReport.CATEGORY_CHOICES,
    })
# Success page after submission
def report_success(request):
    return render(request, 'needs/report_success.html')

@login_required
def claim_need(request, need_id):
    """Allows an NGO to claim an unassigned public need report"""
    if not request.user.is_ngo_manager():
        return redirect('dashboard')
    
    try:
        need = NeedReport.objects.get(id=need_id, ngo=None)
        need.ngo = request.user.ngo
        need.save()
    except NeedReport.DoesNotExist:
        pass
        
    return redirect('manager_dashboard')

# Field worker detailed submission (login required)
@login_required
def submit_need(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        category = request.POST.get('category')
        location_name = request.POST.get('location_name')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        photo = request.FILES.get('photo')

        need = NeedReport(
            title=title,
            description=description,
            category=category,
            location_name=location_name,
            source='digital',
            submitted_by=request.user,
            ngo=request.user.ngo
        )
        if latitude:
            need.latitude = float(latitude)
        if longitude:
            need.longitude = float(longitude)
        if photo:
            need.photo = photo

        need.save()
        # Auto geocode location
        if not need.latitude and location_name:
            lat, lng = geocode_location(location_name, settings.GOOGLE_MAPS_API_KEY)
            if lat:
                need.latitude = lat
                need.longitude = lng

        # Auto score with Gemini AI
        scored = score_need_urgency(title, description, category, location_name)
        need.urgency = scored.get('urgency', 'medium')
        need.ai_recommendation = scored.get('recommendation', '')
        need.ai_scored = True
        need.save()

        return redirect('report_success')

    return render(request, 'needs/submit_need.html', {
        'categories': NeedReport.CATEGORY_CHOICES,
    })
# Document digitization page
@login_required
def digitize_document(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        if not file:
            return render(request, 'needs/digitize.html', {
                'error': 'Please upload a file'
            })

        # Save document
        doc = Document(
            uploaded_by=request.user,
            file=file,
            source_type='photo'
        )
        # Only assign NGO if user has one
        if hasattr(request.user, 'ngo') and request.user.ngo:
            doc.ngo = request.user.ngo
        doc.save()
        
        try:
            # Send to Gemini Vision
            # Note: doc.file.path might raise ValueError if file is not found/empty
            image_path = doc.file.path
            extracted = extract_from_document(image_path)

            # Save extracted data
            doc.extracted_title = extracted.get('title', 'Extracted Document')
            doc.extracted_category = extracted.get('category', 'other')
            doc.extracted_location = extracted.get('location', '')
            doc.extracted_urgency = extracted.get('urgency', 'medium')
            doc.extracted_text = extracted.get('description', '')
            doc.save()

            return redirect(f'/digitize/review/{doc.id}/')
            
        except Exception as e:
            messages.error(request, f"Artificial Intelligence encountered a problem: {str(e)}. You can still fill details manually.")
            # Fallback values
            doc.extracted_title = "Manual Entry Required"
            doc.save()
            return redirect(f'/digitize/review/{doc.id}/')

    return render(request, 'needs/digitize.html')

# Review extracted data before saving
@login_required
def review_document(request, doc_id):
    try:
        doc = Document.objects.get(id=doc_id, uploaded_by=request.user)
    except Document.DoesNotExist:
        return redirect('digitize_document')

    if request.method == 'POST':
        location_name = request.POST.get('location_name')
        need = NeedReport(
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            category=request.POST.get('category'),
            location_name=location_name,
            urgency=request.POST.get('urgency'),
            source='digitized',
            submitted_by=request.user,
            ai_scored=True,
            photo=doc.file # Carry over the original photo
        )
        if hasattr(request.user, 'ngo') and request.user.ngo:
            need.ngo = request.user.ngo
            
        # Geocode the confirmed location
        lat, lng = geocode_location(location_name, settings.GOOGLE_MAPS_API_KEY)
        if lat:
            need.latitude = lat
            need.longitude = lng
            
        need.save()

        doc.linked_need = need
        doc.is_converted = True
        doc.save()

        return redirect('report_success')

    return render(request, 'needs/review_document.html', {
        'doc': doc,
        'categories': NeedReport.CATEGORY_CHOICES,
    })

# Manually trigger AI scoring for existing needs
@login_required
def score_need(request, need_id):
    try:
        need = NeedReport.objects.get(id=need_id)
    except NeedReport.DoesNotExist:
        return redirect('manager_dashboard')

    scored = score_need_urgency(
        need.title,
        need.description,
        need.category,
        need.location_name
    )
    need.urgency = scored.get('urgency', 'medium')
    need.ai_recommendation = scored.get('recommendation', '')
    need.ai_scored = True
    need.save()

    return redirect('manager_dashboard')

# Volunteer list — manager sees all volunteers
@login_required
def volunteer_list(request):
    if not request.user.is_ngo_manager() and not request.user.is_superuser:
        return redirect('dashboard')

    volunteers = VolunteerProfile.objects.filter(
        user__ngo=request.user.ngo
    ).select_related('user')

    # Filter by skill
    skill = request.GET.get('skill', '')
    availability = request.GET.get('availability', '')

    if skill:
        volunteers = volunteers.filter(skills__icontains=skill)
    if availability == 'available':
        volunteers = volunteers.filter(availability=True)
    elif availability == 'busy':
        volunteers = volunteers.filter(availability=False)

    return render(request, 'volunteers/volunteer_list.html', {
        'volunteers': volunteers,
        'skill_choices': VolunteerProfile.SKILL_CHOICES,
    })


# Volunteer profile edit — volunteer edits own profile
@login_required
def volunteer_profile(request):
    if not request.user.is_volunteer():
        return redirect('dashboard')

    # Get or create profile safely
    profile, created = VolunteerProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'skills': '',
            'availability': True,
            'location': ''
        }
    )

    if request.method == 'POST':
        skills_list = request.POST.getlist('skills')
        profile.skills = ','.join(skills_list)
        profile.availability = 'availability' in request.POST
        profile.location = request.POST.get('location', '')
        profile.save()
        return redirect('volunteer_dashboard')

    selected_skills = [s.strip() for s in profile.skills.split(',')] if profile.skills else []

    return render(request, 'volunteers/volunteer_profile.html', {
        'profile': profile,
        'skill_choices': VolunteerProfile.SKILL_CHOICES,
        'selected_skills': selected_skills,
    })

# Add volunteer — manager adds volunteer manually
@login_required
def add_volunteer(request):
    if not request.user.is_ngo_manager() and not request.user.is_superuser:
        return redirect('dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        skills = ','.join(request.POST.getlist('skills'))
        location = request.POST.get('location', '')

        if User.objects.filter(username=username).exists():
            error = 'Username already taken'
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role=Role.VOLUNTEER,
                ngo=request.user.ngo
            )
            VolunteerProfile.objects.create(
                user=user,
                skills=skills,
                availability=True,
                location=location
            )
            return redirect('volunteer_list')

    # THIS LINE WAS MISSING — always return render for GET
    return render(request, 'volunteers/add_volunteer.html', {
        'skill_choices': VolunteerProfile.SKILL_CHOICES,
        'error': error,
    })

# Assign volunteer to need
@login_required
def assign_volunteer(request, need_id):
    if not request.user.is_ngo_manager() and not request.user.is_superuser:
        return redirect('dashboard')

    try:
        need = NeedReport.objects.get(id=need_id)
    except NeedReport.DoesNotExist:
        return redirect('manager_dashboard')

    # Get IDs of volunteers already assigned to this need
    already_assigned = Assignment.objects.filter(need=need).values_list('volunteer_id', flat=True)

    # Get available volunteers from same NGO, excluding those already on this mission
    volunteers = VolunteerProfile.objects.filter(
        user__ngo=request.user.ngo,
        availability=True
    ).exclude(user_id__in=already_assigned).select_related('user')

    ai_matches = None
    if volunteers.exists():
        result = match_volunteers(
            need.title,
            need.description,
            need.category,
            need.location_name,
            volunteers
        )
        ai_matches = result.get('matches', [])
        ai_recommendation = result.get('recommendation', '')
    else:
        ai_recommendation = 'No available volunteers found.'

    if request.method == 'POST':
        volunteer_ids = request.POST.getlist('volunteer_ids')
        notes = request.POST.get('notes', '')
        
        if volunteer_ids:
            for v_id in volunteer_ids:
                try:
                    volunteer = User.objects.get(id=v_id)
                    Assignment.objects.create(
                        need=need,
                        volunteer=volunteer,
                        assigned_by=request.user,
                        notes=notes,
                        ai_recommendation=ai_recommendation
                    )
                    # NOTE: Availability is now updated on acceptance, not assignment
                    # to allow for alternate assignments/rejections
                except User.DoesNotExist:
                    continue
            
            # Update need status
            need.status = 'in_progress'
            need.save()
            return redirect('manager_dashboard')

    return render(request, 'assignments/assign.html', {
        'need': need,
        'volunteers': volunteers,
        'ai_matches': ai_matches,
        'ai_recommendation': ai_recommendation,
    })

# Track individual assignments for a specific need/problem
@login_required
def track_mission(request, need_id):
    if not request.user.is_ngo_manager() and not request.user.is_superuser:
        return redirect('dashboard')
    
    try:
        need = NeedReport.objects.get(id=need_id, ngo=request.user.ngo)
    except NeedReport.DoesNotExist:
        return redirect('manager_dashboard')
    
    assignments = Assignment.objects.filter(need=need).select_related('volunteer', 'volunteer__volunteer_profile')
    
    return render(request, 'assignments/track.html', {
        'need': need,
        'assignments': assignments,
    })

@login_required
def mission_history(request):
    if not request.user.is_ngo_manager() and not request.user.is_superuser:
        return redirect('dashboard')
    
    ngo = request.user.ngo
    # Show only resolved/verified needs for historical data
    history = NeedReport.objects.filter(ngo=ngo, status='resolved').order_by('-updated_at')
    
    return render(request, 'dashboard/history.html', {
        'history': history,
        'ngo': ngo
    })

@login_required
def verify_assignment(request, assignment_id):
    if not request.user.is_ngo_manager() and not request.user.is_superuser:
        return redirect('dashboard')
    
    try:
        assignment = Assignment.objects.get(id=assignment_id, need__ngo=request.user.ngo)
    except Assignment.DoesNotExist:
        return redirect('manager_dashboard')
    
    if request.method == 'POST':
        assignment.is_verified = True
        assignment.verified_at = timezone.now()
        assignment.save()
        
        # Check if ALL assignments for this need are now verified
        all_assignments = assignment.need.assignments.all()
        if all_assignments.exists() and all(a.is_verified for a in all_assignments):
            assignment.need.status = 'resolved'
            assignment.need.save()
            
        return redirect('track_mission', need_id=assignment.need.id)
    
    return redirect('track_mission', need_id=assignment.need.id)


# Volunteer updates task status
@login_required
def update_assignment(request, assignment_id):
    try:
        assignment = Assignment.objects.get(
            id=assignment_id,
            volunteer=request.user
        )
    except Assignment.DoesNotExist:
        return redirect('volunteer_dashboard')

    if request.method == 'POST':
        new_status = request.POST.get('status')
        completion_notes = request.POST.get('completion_notes', '')
        completion_photo = request.FILES.get('completion_photo')

        assignment.status = new_status
        assignment.completion_notes = completion_notes

        if completion_photo:
            assignment.completion_photo = completion_photo

        if new_status in ['accepted', 'in_progress']:
            # Force Busy status whenever a mission is accepted or active
            profile = request.user.volunteer_profile
            profile.availability = False
            profile.save()

        if new_status == 'completed':
            assignment.completed_at = timezone.now()
            # Update need status to signal it's ready for audit
            assignment.need.status = 'awaiting_verification'
            assignment.need.save()
            # Update volunteer stats
            profile = request.user.volunteer_profile
            profile.tasks_completed += 1
            
            # Smart Availability: Only set to Available if no other active missions exist
            active_missions = Assignment.objects.filter(
                volunteer=request.user,
                status__in=['accepted', 'in_progress']
            ).exclude(id=assignment.id).exists()
            
            if not active_missions:
                profile.availability = True
            profile.save()

        assignment.save()
        return redirect('volunteer_dashboard')

    return render(request, 'assignments/update.html', {
        'assignment': assignment,
    })


# Volunteer dashboard with assignments
@login_required
def volunteer_dashboard(request):
    if not request.user.is_volunteer():
        return redirect('dashboard')

    profile, created = VolunteerProfile.objects.get_or_create(
        user=request.user,
        defaults={'skills': '', 'availability': True}
    )

    assignments = Assignment.objects.filter(
        volunteer=request.user
    ).select_related('need').order_by('-assigned_at')

    # --- Auto-Sync Logic: Prevent inconsistency ---
    has_active_mission = assignments.filter(status__in=['accepted', 'in_progress']).exists()
    if has_active_mission and profile.availability:
        profile.availability = False
        profile.save()
    # --- End Auto-Sync ---

    return render(request, 'dashboard/volunteer.html', {
        'profile': profile,
        'assignments': assignments,
    })


@login_required
def update_availability(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            available = data.get('available', True)
            profile = request.user.volunteer_profile
            profile.availability = available
            profile.save()
            return JsonResponse({'status': 'ok', 'available': available})
        except Exception as e:
            return JsonResponse({'status': 'error'}, status=400)
    return JsonResponse({'status': 'error'}, status=405)

@login_required
def availability_status(request):
    try:
        available = request.user.volunteer_profile.availability
    except:
        available = True
    return JsonResponse({'available': available})

@login_required
def impact_analytics(request):
    if not request.user.is_ngo_manager() and not request.user.is_superuser:
        return redirect('dashboard')

    ngo = request.user.ngo
    all_needs = NeedReport.objects.filter(ngo=ngo)
    
    # Existing basic stats...
    total_needs = all_needs.count()
    resolved_needs = all_needs.filter(status='resolved').count()
    pending_needs = all_needs.filter(status='pending').count()
    high_urgency = all_needs.filter(urgency='high').count()
    digitized_docs = all_needs.filter(source='digitized').count()
    total_volunteers = VolunteerProfile.objects.filter(user__ngo=ngo).count()
    available_volunteers = VolunteerProfile.objects.filter(user__ngo=ngo, availability=True).count()
    total_assignments = Assignment.objects.filter(need__ngo=ngo).count()

    # --- Intelligence Layer (Trend Analysis) ---
    four_weeks_ago = timezone.now() - timezone.timedelta(weeks=4)
    weekly_data = []
    for i in range(4):
        start = four_weeks_ago + timezone.timedelta(weeks=i)
        end = start + timezone.timedelta(weeks=1)
        count = all_needs.filter(created_at__range=(start, end)).count()
        weekly_data.append(count)
    
    # Get Predictive Insights from AI
    ai_insights = get_intelligence_insights(all_needs[:50]) # Send recent samples for context
    
    # --- Visualization Prep ---
    # Top volunteers leaderboard
    top_volunteers = VolunteerProfile.objects.filter(
        user__ngo=ngo
    ).order_by('-tasks_completed')[:5]

    # Recently resolved
    recent_resolved = all_needs.filter(status='resolved').order_by('-updated_at')[:5]

    # Data for Charts
    categories = {}
    for choice in NeedReport.CATEGORY_CHOICES:
        categories[choice[1]] = all_needs.filter(category=choice[0]).count()

    urgency_data = {
        'High': high_urgency,
        'Medium': all_needs.filter(urgency='medium').count(),
        'Low': all_needs.filter(urgency='low').count()
    }

    status_data = {
        'Pending': pending_needs,
        'In Progress': all_needs.filter(status='in_progress').count(),
        'Resolved': resolved_needs
    }

    # Heatmap data
    map_data = []
    for need in all_needs.filter(latitude__isnull=False, longitude__isnull=False):
        map_data.append({
            'lat': need.latitude,
            'lng': need.longitude,
            'weight': 1.0 if need.urgency == 'low' else (2.0 if need.urgency == 'medium' else 3.0)
        })

    return render(request, 'analytics/impact.html', {
        'ngo': ngo,
        'total_needs': total_needs,
        'resolved_needs': resolved_needs,
        'pending_needs': pending_needs,
        'high_urgency': high_urgency,
        'digitized_docs': digitized_docs,
        'total_volunteers': total_volunteers,
        'available_volunteers': available_volunteers,
        'total_assignments': total_assignments,
        'top_volunteers': top_volunteers,
        'recent_resolved': recent_resolved,
        'categories': json.dumps(categories),
        'urgency_data': json.dumps(urgency_data),
        'status_data': json.dumps(status_data),
        'ai_insights': ai_insights,
        'map_data': json.dumps(map_data),
        'weekly_counts': json.dumps(weekly_data),
        'google_maps_key': settings.GOOGLE_MAPS_API_KEY,
    })

@login_required
def super_admin_dashboard(request):
    if not request.user.is_superuser and not request.user.role == Role.SUPER_ADMIN:
        return redirect('dashboard')

    # All NGOs
    all_ngos = NGO.objects.all()
    approved_ngos = all_ngos.filter(is_approved=True).count()
    pending_ngos = all_ngos.filter(is_approved=False).count()

    # All needs across all NGOs
    all_needs = NeedReport.objects.all()
    total_needs = all_needs.count()
    resolved_needs = all_needs.filter(status='resolved').count()
    high_urgency = all_needs.filter(urgency='high').count()

    # All volunteers
    total_volunteers = VolunteerProfile.objects.all().count()

    # All assignments
    total_assignments = Assignment.objects.all().count()

    # NGO wise breakdown
    ngo_stats = []
    for ngo in all_ngos:
        ngo_needs = NeedReport.objects.filter(ngo=ngo)
        ngo_volunteers = VolunteerProfile.objects.filter(user__ngo=ngo)
        ngo_stats.append({
            'ngo': ngo,
            'total_needs': ngo_needs.count(),
            'resolved': ngo_needs.filter(status='resolved').count(),
            'pending': ngo_needs.filter(status='pending').count(),
            'high_urgency': ngo_needs.filter(urgency='high').count(),
            'volunteers': ngo_volunteers.count(),
        })

    return render(request, 'dashboard/super_admin.html', {
        'all_ngos': all_ngos,
        'approved_ngos': approved_ngos,
        'pending_ngos': pending_ngos,
        'total_needs': total_needs,
        'resolved_needs': resolved_needs,
        'high_urgency': high_urgency,
        'total_volunteers': total_volunteers,
        'total_assignments': total_assignments,
        'ngo_stats': ngo_stats,
    })


# Approve or reject NGO
@login_required
def approve_ngo(request, ngo_id):
    if not request.user.is_superuser and not request.user.role == Role.SUPER_ADMIN:
        return redirect('dashboard')

    try:
        ngo = NGO.objects.get(id=ngo_id)
        action = request.POST.get('action')
        if action == 'approve':
            ngo.is_approved = True
            ngo.save()
        elif action == 'reject':
            ngo.delete()
    except NGO.DoesNotExist:
        pass

    return redirect('super_admin_dashboard')


# NGO Registration page (public)
def ngo_register(request):
    error = None
    success = False

    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address', '')
        city = request.POST.get('city')
        state = request.POST.get('state')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        description = request.POST.get('description')
        username = request.POST.get('username')
        password = request.POST.get('password')

        if NGO.objects.filter(email=email).exists():
            error = 'An NGO with this email already exists'
        elif User.objects.filter(username=username).exists():
            error = 'Username already taken'
        else:
            ngo = NGO.objects.create(
                name=name,
                address=address,
                city=city,
                state=state,
                email=email,
                phone=phone,
                description=description or "",
                is_approved=False
            )
            
            # Geocode NGO HQ
            loc_str = f"{address}, {city}, {state}"
            lat, lng = geocode_location(loc_str, settings.GOOGLE_MAPS_API_KEY)
            if lat:
                ngo.latitude = lat
                ngo.longitude = lng
                ngo.save()
            
            User.objects.create_user(
                username=username,
                password=password,
                role=Role.NGO_MANAGER,
                ngo=ngo
            )
            success = True

    return render(request, 'ngo/register.html', {
        'error': error,
        'success': success,
    })

@login_required
def public_home(request):
    if not request.user.is_authenticated or request.user.role != Role.PUBLIC:
        return redirect('landing')
    
    # Reports submitted by this user
    my_reports = NeedReport.objects.filter(submitted_by=request.user).order_by('-created_at')
    
    return render(request, 'dashboard/public.html', {
        'my_reports': my_reports
    })