# 🤝 UnityAid: Tactical Mission Mobilization & NGO Platform

UnityAid is a comprehensive, regionalized NGO management and crisis response platform built with Django. It bridges the gap between public need reporters, NGOs, and volunteers through a highly structured, role-based ecosystem.

## 🚀 Key Features

* **Role-Based Access Control (RBAC):** 
 Distinct dashboards and workflows for Public Reporters, Volunteers, NGO Managers, and Super Admins.
* **Super Admin Verification Fence:** 
 All newly registered NGOs are placed in a 'Pending' state until vetted and approved by a Super Admin.
* **Tactical Mission Monitoring:** 
 A high-speed, proactive "Command Center" dashboard for NGO Managers.

  * *Acceptance Delay Alerts:* Automatically flags tasks if a volunteer hasn't accepted within 30 minutes.

  * *Resolution Delay Alerts:* Flags in-progress tasks that haven't been updated within 1 hour.

* **AI Integration:** 
 Uses Gemini 1.5 Flash AI to intelligently categorize and prioritize incoming public need reports.
* **Geospatial Tracking:**
 Integrated with Google Maps API for precise location mapping of needs and missions.

## 💻 Tech Stack

* **Backend:** Python, Django 6.0.3
* **Frontend:** HTML5, CSS3, JavaScript (AJAX for modals)
* **Database:** SQLite (Development) / PostgreSQL (Production ready via `dj-database-url`)
* **Hosting:** Dockerized for Google Cloud Run / Native Python for Render.com

## 🧑‍⚖️ Evaluation Guide (Demo Accounts)

**To Evaluators/Judges:** 
Instead of registering a new NGO from scratch and waiting for verification, you can experience the full platform immediately by logging in with the following demo accounts. Please enter these in the standard Username/Password login form (ignoring the Google OAuth button).

### 1. Super Admin Account
*Access to approve pending NGOs and view platform-wide metrics.*
* **Username:** `admin` 
* **Password:** `dharsh2006kd` 

### 2. NGO Manager Account
*Access the Tactical Command Center to view live alerts, manage volunteers, and assign tasks.*
* **Username:** `manager_kangayam` 
* **Password:** `manager@123` 
### 3. Volunteer Account
*Access to accept assigned tasks, update mission progress, and upload completion photos.*
* **Username:** `dr_priya` 
* **Password:** `volunteer@123` 

---
