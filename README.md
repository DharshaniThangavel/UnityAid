# 🤝 UnityAid: Tactical Disaster & NGO Coordination Platform

## 🌍 Overview
UnityAid is a high-accountability, regionalized platform designed to bridge the gap between public reporters, NGOs, and volunteers during crises and disaster relief efforts. 

When a crisis occurs, the biggest hurdles are unverified information, lack of coordination, and delayed response times. UnityAid solves this by providing a centralized command center where public needs are instantly geo-located, NGOs are officially verified, and volunteers are tactically deployed with real-time progress monitoring.

## 🚀 Key Features

* **Role-Based Command Structure:** Distinct interfaces and permissions for Public Reporters, Verified NGO Managers, Field Volunteers, and Platform Super Admins.
* **Tactical Mission Monitoring:** A proactive alert engine that tracks volunteer deployments. NGO managers receive immediate modal alerts if a volunteer fails to accept a task within 30 minutes, or if a mission stalls without resolution for over 1 hour.
* **Geospatial Intelligence:** Integration with Google Maps to instantly pinpoint crisis locations, allowing NGOs to deploy volunteers based on proximity and skill set.
* **Administrative Verification Fence:** To ensure trust and prevent fraud, all newly registered NGOs are placed in a 'Pending' state and cannot access the network until fully vetted and approved by a Super Admin.
* **AI-Ready Mission Archive:** Resolved missions are archived for future predictive modeling and impact analysis, utilizing Google Gemini to analyze resource gaps and response efficiency.

## 🛠️ Technology Stack
* **Backend:** Python, Django 6.x
* **Frontend:** HTML5, Vanilla CSS (Custom Design System), JavaScript
* **Database:** SQLite (Local/Dev) / PostgreSQL (Cloud Run Production)
* **Integrations:** Google Maps API, Google Gemini API, Google OAuth2
* **Deployment:** Docker, Gunicorn, Render/Google Cloud Run

## 🔐 Demo Accounts
To test the features of this platform, you can log in using the following test credentials:
* **Super Admin:** *(Add your super admin username/password here)*
* **NGO Manager:** *(Add your manager username/password here)*
* **Volunteer:** *(Add your volunteer username/password here)*
