from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.landing, name='landing'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboards
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('dashboard/manager/', views.manager_dashboard, name='manager_dashboard'),
    path('dashboard/volunteer/', views.volunteer_dashboard, name='volunteer_dashboard'),
    path('dashboard/admin/', views.super_admin_dashboard, name='super_admin_dashboard'),
    path('dashboard/public/', views.public_home, name='public_home'),

    # Needs
    path('report/', views.report_need, name='report_need'),
    path('report/success/', views.report_success, name='report_success'),
    path('submit/', views.submit_need, name='submit_need'),

    # Document Digitization
    path('digitize/', views.digitize_document, name='digitize_document'),
    path('digitize/review/<int:doc_id>/', views.review_document, name='review_document'),
    path('needs/claim/<int:need_id>/', views.claim_need, name='claim_need'),

    # Scoring
    path('needs/score/<int:need_id>/', views.score_need, name='score_need'),

    # Volunteers
    path('volunteers/', views.volunteer_list, name='volunteer_list'),
    path('volunteers/add/', views.add_volunteer, name='add_volunteer'),
    path('volunteers/profile/', views.volunteer_profile, name='volunteer_profile'),
    # Assignments
    path('needs/assign/<int:need_id>/', views.assign_volunteer, name='assign_volunteer'),
    path('needs/history/', views.mission_history, name='mission_history'),
    path('needs/track/<int:need_id>/', views.track_mission, name='track_mission'),
    path('needs/verify/<int:assignment_id>/', views.verify_assignment, name='verify_assignment'),
    path('assignments/update/<int:assignment_id>/', views.update_assignment, name='update_assignment'),
    path('volunteers/availability/', views.update_availability, name='update_availability'),
    path('volunteers/availability/status/', views.availability_status, name='availability_status'),
    path('analytics/', views.impact_analytics, name='impact_analytics'),
    # Super Admin
    path('ngo/register/', views.ngo_register, name='ngo_register'),
    path('ngo/pending/', views.ngo_pending, name='ngo_pending'),
    path('ngo/approve/<int:ngo_id>/', views.approve_ngo, name='approve_ngo'),
]