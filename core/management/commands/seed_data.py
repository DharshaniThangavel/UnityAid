from django.core.management.base import BaseCommand
from core.models import User, NGO, Role, NeedReport, VolunteerProfile, Assignment

class Command(BaseCommand):
    help = 'Seed sample data for testing'

    def handle(self, *args, **kwargs):

        # ── 1. NGO ──────────────────────────────────────
        ngo, _ = NGO.objects.get_or_create(
            name='Kangayam NGO',
            defaults={
                'city': 'Kangayam',
                'state': 'Tamil Nadu',
                'email': 'kangayamngo@gmail.com',
                'phone': '9876543210',
                'is_approved': True,
                'description': 'Serving Kangayam and surrounding villages'
            }
        )
        self.stdout.write('✅ NGO created')

        # ── 2. Manager ───────────────────────────────────
        if not User.objects.filter(username='manager_kangayam').exists():
            manager = User.objects.create_user(
                username='manager_kangayam',
                email='manager@kangayamngo.com',
                password='manager@123',
                role=Role.NGO_MANAGER,
                ngo=ngo
            )
        else:
            manager = User.objects.get(username='manager_kangayam')
        self.stdout.write('✅ Manager created — username: manager_kangayam | password: manager@123')

        # ── 3. Volunteers ────────────────────────────────
        volunteer_data = [
            {
                'username': 'dr_priya',
                'email': 'priya@volunteer.com',
                'password': 'volunteer@123',
                'skills': 'doctor,nurse',
                'location': 'Kangayam',
            },
            {
                'username': 'rajan_teacher',
                'email': 'rajan@volunteer.com',
                'password': 'volunteer@123',
                'skills': 'teacher,counselor',
                'location': 'Dharapuram',
            },
            {
                'username': 'suresh_engineer',
                'email': 'suresh@volunteer.com',
                'password': 'volunteer@123',
                'skills': 'engineer,technician',
                'location': 'Tirupur',
            },
            {
                'username': 'meena_social',
                'email': 'meena@volunteer.com',
                'password': 'volunteer@123',
                'skills': 'social_worker,cook',
                'location': 'Kangayam',
            },
            {
                'username': 'kumar_driver',
                'email': 'kumar@volunteer.com',
                'password': 'volunteer@123',
                'skills': 'driver',
                'location': 'Erode',
            },
        ]

        volunteers = []
        for vd in volunteer_data:
            if not User.objects.filter(username=vd['username']).exists():
                user = User.objects.create_user(
                    username=vd['username'],
                    email=vd['email'],
                    password=vd['password'],
                    role=Role.VOLUNTEER,
                    ngo=ngo
                )
                profile = VolunteerProfile.objects.create(
                    user=user,
                    skills=vd['skills'],
                    availability=True,
                    location=vd['location'],
                    tasks_completed=0
                )
            else:
                user = User.objects.get(username=vd['username'])
            volunteers.append(user)

        self.stdout.write('✅ 5 Volunteers created')

        # ── 4. Public Reporter ───────────────────────────
        if not User.objects.filter(username='reporter_public').exists():
            User.objects.create_user(
                username='reporter_public',
                email='reporter@public.com',
                password='reporter@123',
                role=Role.PUBLIC,
                ngo=None
            )
        self.stdout.write('✅ Public reporter created — username: reporter_public | password: reporter@123')

        # ── 5. Need Reports ──────────────────────────────
        needs_data = [
            {
                'title': 'Urgent Medical Camp Needed in Kamalapuram Village',
                'description': 'About 300 families in Kamalapuram village have had no access to a doctor for over 6 months. Many elderly people are suffering from chronic illnesses with no treatment. Children need vaccination updates urgently.',
                'category': 'health',
                'location_name': 'Kamalapuram, Kangayam',
                'latitude': 11.0168,
                'longitude': 77.5539,
                'urgency': 'high',
                'status': 'pending',
                'source': 'public',
                'ai_scored': True,
                'ai_recommendation': 'Deploy medical volunteer team immediately. Prioritize elderly and children.',
            },
            {
                'title': 'Panchayat School Roof Needs Repair',
                'description': 'The government school in Thoppampatti village has a damaged roof. During rains water leaks into classrooms affecting 120 students. Classes have been disrupted for 3 weeks.',
                'category': 'infrastructure',
                'location_name': 'Thoppampatti, Kangayam',
                'latitude': 11.0300,
                'longitude': 77.5700,
                'urgency': 'high',
                'status': 'pending',
                'source': 'digital',
                'ai_scored': True,
                'ai_recommendation': 'Send civil engineer volunteer for assessment and repair coordination.',
            },
            {
                'title': 'Food Distribution Needed for Daily Wage Families',
                'description': 'Around 80 families dependent on daily wages in Nallagoundenpalayam are facing food shortage due to drought. They need weekly food kit distribution for at least 2 months.',
                'category': 'food',
                'location_name': 'Nallagoundenpalayam, Kangayam',
                'latitude': 11.0050,
                'longitude': 77.5400,
                'urgency': 'high',
                'status': 'in_progress',
                'source': 'public',
                'ai_scored': True,
                'ai_recommendation': 'Organize food kit distribution with cook and driver volunteers.',
            },
            {
                'title': 'No Science Teacher for 9th and 10th Grade',
                'description': 'Mullaipattu village school has had no science teacher for 4 months. Students appearing for board exams are severely affected. Need a qualified teacher volunteer at least 3 days a week.',
                'category': 'education',
                'location_name': 'Mullaipattu, Kangayam',
                'latitude': 11.0400,
                'longitude': 77.5600,
                'urgency': 'medium',
                'status': 'pending',
                'source': 'digital',
                'ai_scored': True,
                'ai_recommendation': 'Assign teacher volunteer with science background for regular sessions.',
            },
            {
                'title': 'Sanitation Drive Required in Periyanayakkanpalayam',
                'description': 'Open defecation is still practiced in parts of Periyanayakkanpalayam. Community awareness and toilet construction support needed for approximately 40 households.',
                'category': 'sanitation',
                'location_name': 'Periyanayakkanpalayam, Kangayam',
                'latitude': 11.0500,
                'longitude': 77.5800,
                'urgency': 'medium',
                'status': 'pending',
                'source': 'public',
                'ai_scored': True,
                'ai_recommendation': 'Deploy social worker volunteer for community awareness program.',
            },
            {
                'title': 'Elderly Care Support for Isolated Senior Citizens',
                'description': 'About 25 elderly people above 70 years live alone in Sengodampalayam village. They need regular health checkups, medicine reminders and basic daily assistance.',
                'category': 'elderly',
                'location_name': 'Sengodampalayam, Kangayam',
                'latitude': 11.0600,
                'longitude': 77.5300,
                'urgency': 'medium',
                'status': 'pending',
                'source': 'digitized',
                'ai_scored': True,
                'ai_recommendation': 'Assign nurse and social worker volunteers for weekly visits.',
            },
            {
                'title': 'Clean Drinking Water Access in Podhumbu Village',
                'description': 'The only borewell in Podhumbu village has been non-functional for 2 months. Villagers are walking 3km daily to fetch water. Urgent repair or alternative water supply needed.',
                'category': 'sanitation',
                'location_name': 'Podhumbu, Kangayam',
                'latitude': 11.0700,
                'longitude': 77.5100,
                'urgency': 'high',
                'status': 'resolved',
                'source': 'public',
                'ai_scored': True,
                'ai_recommendation': 'Send engineer volunteer to assess borewell repair feasibility.',
            },
            {
                'title': 'Nutrition Awareness Camp for Pregnant Women',
                'description': 'High rate of anemia detected in pregnant women in Ayyampalayam village during last health survey. Need nutrition education camp and iron supplement distribution for 45 women.',
                'category': 'health',
                'location_name': 'Ayyampalayam, Kangayam',
                'latitude': 11.0250,
                'longitude': 77.5650,
                'urgency': 'medium',
                'status': 'pending',
                'source': 'digitized',
                'ai_scored': True,
                'ai_recommendation': 'Deploy doctor and nurse volunteers for nutrition awareness camp.',
            },
        ]

        created_needs = []
        for nd in needs_data:
            if not NeedReport.objects.filter(title=nd['title']).exists():
                need = NeedReport.objects.create(
                    title=nd['title'],
                    description=nd['description'],
                    category=nd['category'],
                    location_name=nd['location_name'],
                    latitude=nd['latitude'],
                    longitude=nd['longitude'],
                    urgency=nd['urgency'],
                    status=nd['status'],
                    source=nd['source'],
                    ai_scored=nd['ai_scored'],
                    ai_recommendation=nd['ai_recommendation'],
                    ngo=ngo,
                    submitted_by=manager
                )
                created_needs.append(need)

        self.stdout.write('✅ 8 Need Reports created')

        # ── 6. Sample Assignment ─────────────────────────
        if created_needs:
            food_need = NeedReport.objects.filter(
                title__icontains='Food Distribution',
                ngo=ngo
            ).first()

            dr_priya = User.objects.filter(username='dr_priya').first()
            if food_need and dr_priya:
                if not Assignment.objects.filter(need=food_need).exists():
                    Assignment.objects.create(
                        need=food_need,
                        volunteer=dr_priya,
                        assigned_by=manager,
                        status='in_progress',
                        notes='Please coordinate with local panchayat for distribution',
                        ai_recommendation='Best match based on availability and location'
                    )
            self.stdout.write('✅ Sample assignment created')

        # ── Summary ──────────────────────────────────────
        self.stdout.write('\n')
        self.stdout.write('═' * 50)
        self.stdout.write('🎉 SAMPLE DATA READY!')
        self.stdout.write('═' * 50)
        self.stdout.write('NGO: Kangayam NGO')
        self.stdout.write('\nLOGIN CREDENTIALS:')
        self.stdout.write('─' * 30)
        self.stdout.write('Super Admin  → admin / (your password)')
        self.stdout.write('NGO Manager  → manager_kangayam / manager@123')
        self.stdout.write('Volunteer 1  → dr_priya / volunteer@123')
        self.stdout.write('Volunteer 2  → rajan_teacher / volunteer@123')
        self.stdout.write('Volunteer 3  → suresh_engineer / volunteer@123')
        self.stdout.write('Volunteer 4  → meena_social / volunteer@123')
        self.stdout.write('Volunteer 5  → kumar_driver / volunteer@123')
        self.stdout.write('Public       → reporter_public / reporter@123')
        self.stdout.write('─' * 30)
        self.stdout.write('8 Need Reports with AI urgency scores')
        self.stdout.write('1 Sample assignment (In Progress)')
        self.stdout.write('═' * 50)