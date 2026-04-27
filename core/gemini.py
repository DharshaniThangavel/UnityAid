import os
import requests
import base64
import json


GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

def encode_image(image_path):
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def extract_from_document(image_path):
    """
    Sends a paper document photo to Gemini Vision
    and extracts structured community need data.
    """
    try:
        image_data = encode_image(image_path)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"

        payload = {
            "contents": [{
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_data
                        }
                    },
                    {
                        "text": """You are analyzing a paper community needs survey or field report.
                        Extract the following information and return ONLY a JSON object:
                        {
                            "title": "short problem title",
                            "description": "full description of the need",
                            "category": "one of: health, education, food, infrastructure, sanitation, elderly, other",
                            "location": "location/area/village name",
                            "urgency": "one of: high, medium, low",
                            "recommendation": "suggested action"
                        }
                        If any field is unclear, make your best guess from context.
                        Return ONLY the JSON, no extra text."""
                    }
                ]
            }]
        }

        response = requests.post(url, json=payload, timeout=30)
        result = response.json()

        if 'error' in result:
            print(f"Gemini API Error: {result['error'].get('message')}")
            raise ValueError(f"API Error: {result['error'].get('message')}")

        if 'candidates' not in result or not result['candidates']:
            print(f"Gemini API returned no candidates: {result}")
            raise ValueError("No candidates returned from AI")

        import re
        text = result['candidates'][0]['content']['parts'][0]['text']
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return data
        else:
            raise ValueError("No valid JSON snippet found in AI response")

    except Exception as e:
        print(f"Extraction Failure: {str(e)}")
        return {
            "title": "Extracted Document",
            "description": "AI extraction was not 100% confident. Please review and fill manually.",
            "category": "other",
            "location": "",
            "urgency": "medium",
            "recommendation": ""
        }


def score_need_urgency(title, description, category, location):
    """
    Sends a need report to Gemini for urgency scoring.
    """
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"

        payload = {
            "contents": [{
                "parts": [{
                    "text": f"""You are an AI assistant for an NGO coordination platform.
                    Analyse this community need and return ONLY a JSON object:
                    {{
                        "urgency": "high or medium or low",
                        "reason": "one sentence explanation",
                        "recommendation": "specific action the NGO should take",
                        "skills_needed": "comma separated skills e.g. doctor, teacher"
                    }}

                    Need Title: {title}
                    Category: {category}
                    Location: {location}
                    Description: {description}

                    Return ONLY the JSON, no extra text."""
                }]
            }]
        }

        response = requests.post(url, json=payload)
        result = response.json()

        import re
        text = result['candidates'][0]['content']['parts'][0]['text']
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return data
        else:
            raise ValueError("No JSON found")

    except Exception as e:
        return {
            "urgency": "medium",
            "reason": "Could not score automatically.",
            "recommendation": "Please review manually.",
            "skills_needed": ""
        }
    
def geocode_location(location_name, api_key):
    """Convert location name to lat/lng using Google Geocoding API"""
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': location_name,
            'key': api_key
        }
        response = requests.get(url, params=params)
        data = response.json()
        if data['status'] == 'OK':
            loc = data['results'][0]['geometry']['location']
            return loc['lat'], loc['lng']
    except:
        pass
    return None, None

def get_intelligence_insights(recent_needs):
    """
    Analyzes recent needs to predict trends and suggest strategies.
    """
    try:
        needs_context = []
        for n in recent_needs:
            needs_context.append({
                'category': n.get_category_display(),
                'urgency': n.urgency,
                'location': n.location_name,
                'created_at': n.created_at.strftime("%Y-%m-%d")
            })

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"

        payload = {
            "contents": [{
                "parts": [{
                    "text": f"""You are the Social Impact intelligence lead for UnityAid. 
                    Analyze these recent community needs and provide a high-level strategic forecast.
                    
                    DATA:
                    {json.dumps(needs_context, indent=2)}
                    
                    Return ONLY a JSON object with:
                    {{
                        "trend_analysis": "one sentence summarizing current trend",
                        "predicted_risk": "the biggest predicted problem in the next 14 days",
                        "proactive_strategy": "clear suggested action for the NGO manager",
                        "urgency_score": 1-10
                    }}
                    Return ONLY JSON."""
                }]
            }]
        }

        response = requests.post(url, json=payload)
        result = response.json()
        import re
        text = result['candidates'][0]['content']['parts'][0]['text']
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        else:
            raise ValueError("No JSON found")
    except Exception as e:
        print(f"Intelligence Error: {e}")
        return {
            "trend_analysis": "Steady inflow of reports across all sectors.",
            "predicted_risk": "Sustained high resource demand in current hotspots.",
            "proactive_strategy": "Maintain current volunteer dispatch levels and monitor high-urgency zones.",
            "urgency_score": 5
        }

def match_volunteers(need_title, need_description, need_category, need_location, volunteers):
    """
    Sends need + volunteer list to Gemini
    Returns top 3 recommended volunteers with reasons
    """
    try:
        volunteer_list = []
        for v in volunteers:
            volunteer_list.append({
                'id': v.user.id,
                'name': v.user.username,
                'skills': v.skills,
                'location': v.location,
                'tasks_completed': v.tasks_completed,
                'available': v.availability
            })

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"

        payload = {
            "contents": [{
                "parts": [{
                    "text": f"""You are an AI assistant for an NGO volunteer coordination platform.
Match the best volunteers for this community need.

NEED:
Title: {need_title}
Category: {need_category}
Location: {need_location}
Description: {need_description}

AVAILABLE VOLUNTEERS:
{json.dumps(volunteer_list, indent=2)}

Return ONLY a JSON object like this:
{{
    "matches": [
        {{
            "volunteer_id": 1,
            "volunteer_name": "name",
            "match_score": 95,
            "reason": "one sentence reason why this volunteer is best"
        }},
        {{
            "volunteer_id": 2,
            "volunteer_name": "name",
            "match_score": 80,
            "reason": "reason"
        }},
        {{
            "volunteer_id": 3,
            "volunteer_name": "name",
            "match_score": 70,
            "reason": "reason"
        }}
    ],
    "recommendation": "overall recommendation note"
}}

Return top 3 matches only. Return ONLY JSON, no extra text."""
                }]
            }]
        }

        response = requests.post(url, json=payload)
        result = response.json()
        import re
        text = result['candidates'][0]['content']['parts'][0]['text']
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return data
        else:
            raise ValueError("No JSON found")

    except Exception as e:
        return {
            "matches": [],
            "recommendation": "Could not get AI recommendation. Please assign manually."
        }