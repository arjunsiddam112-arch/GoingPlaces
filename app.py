#strrupdated goingplaces



import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import requests
import folium
import os
import json
import datetime
import google.generativeai as genai
from dotenv import load_dotenv
from streamlit_folium import st_folium
import logging
from functools import lru_cache
import time
import random  # <-- ADD THIS LINE

# ==================================================
# LOGGING SETUP
# ==================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="GoingPlaces | Spatial Travel",
    layout="wide",
    page_icon="🌐",
    initial_sidebar_state="collapsed"
)

# ==================================================
# VISIONOS GLASSMORPHIC STYLING
# ==================================================
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');
        
        * {
            font-family: 'SF Pro Display', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        /* Deep Space Background with Earth */
        .stApp {
            background: 
                radial-gradient(ellipse at top, #1a1a2e 0%, #16213e 40%, #0f3460 100%),
                url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1920&q=80') center/cover fixed;
            background-blend-mode: multiply;
            color: #ffffff;
        }
        
        section[data-testid="stAppViewContainer"] {
            background: transparent;
        }
        
        /* Glassmorphic Sidebar */
        section[data-testid="stSidebar"] {
            background: rgba(255, 255, 255, 0.05) !important;
            backdrop-filter: blur(20px) saturate(180%) !important;
            -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        
        /* HERO SECTION - Glass Banner */
        .hero-glass {
            position: relative;
            margin: -80px -80px 40px -80px;
            padding: 100px 60px;
            background: linear-gradient(135deg, 
                rgba(0, 243, 255, 0.1) 0%, 
                rgba(255, 255, 255, 0.05) 50%,
                rgba(0, 243, 255, 0.05) 100%);
            backdrop-filter: blur(40px) saturate(200%);
            -webkit-backdrop-filter: blur(40px) saturate(200%);
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 
                0 20px 60px rgba(0, 0, 0, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.2);
            overflow: hidden;
        }
        
        /* Animated Gradient Orb */
        .hero-glass::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -10%;
            width: 600px;
            height: 600px;
            background: radial-gradient(circle, rgba(0, 243, 255, 0.4) 0%, transparent 70%);
            filter: blur(60px);
            animation: float 8s ease-in-out infinite;
            z-index: 0;
        }
        
        .hero-glass::after {
            content: '';
            position: absolute;
            bottom: -30%;
            right: -5%;
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, rgba(255, 0, 255, 0.3) 0%, transparent 70%);
            filter: blur(60px);
            animation: float 10s ease-in-out infinite reverse;
            z-index: 0;
        }
        
        @keyframes float {
            0%, 100% { transform: translate(0, 0) scale(1); }
            50% { transform: translate(30px, -30px) scale(1.1); }
        }
        
        .hero-content {
            position: relative;
            z-index: 1;
            text-align: center;
        }
        
        .hero-title {
            font-size: 5rem;
            font-weight: 700;
            letter-spacing: -0.03em;
            margin: 0;
            line-height: 1;
            background: linear-gradient(180deg, #ffffff 0%, rgba(255,255,255,0.8) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 80px rgba(0, 243, 255, 0.5);
        }
        
        .hero-subtitle {
            font-size: 1.25rem;
            font-weight: 400;
            color: rgba(255, 255, 255, 0.7);
            margin-top: 20px;
            letter-spacing: 0.05em;
        }
        
        /* Glass Cards - Main Container */
        .glass-panel {
            background: rgba(255, 255, 255, 0.07);
            backdrop-filter: blur(20px) saturate(180%);
            -webkit-backdrop-filter: blur(20px) saturate(180%);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 24px;
            padding: 32px;
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .glass-panel:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: rgba(0, 243, 255, 0.3);
            box-shadow: 
                0 12px 48px rgba(0, 0, 0, 0.3),
                0 0 0 1px rgba(0, 243, 255, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.15);
            transform: translateY(-2px);
        }
        
        /* Typography */
        h1, h2, h3 {
            font-weight: 600;
            letter-spacing: -0.02em;
        }
        
        h2 {
            color: #ffffff;
            font-size: 1.75rem;
            margin-bottom: 1.5rem;
            font-weight: 600;
        }
        
        h3 {
            color: rgba(255, 255, 255, 0.9);
            font-size: 1.25rem;
            margin-bottom: 1rem;
        }
        
        /* Input Fields - Glass Style */
        .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox select {
            background: rgba(0, 0, 0, 0.2) !important;
            backdrop-filter: blur(10px) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 16px !important;
            padding: 16px 20px !important;
            color: #ffffff !important;
            font-size: 1rem !important;
            font-weight: 400 !important;
            transition: all 0.3s ease !important;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1) !important;
        }
        
        .stTextInput input:focus, .stNumberInput input:focus, .stDateInput input:focus {
            border-color: rgba(0, 243, 255, 0.6) !important;
            box-shadow: 
                0 0 0 4px rgba(0, 243, 255, 0.1),
                inset 0 2px 4px rgba(0, 0, 0, 0.1) !important;
            background: rgba(0, 0, 0, 0.3) !important;
        }
        
        .stTextInput input::placeholder {
            color: rgba(255, 255, 255, 0.4) !important;
        }
        
        /* Labels */
        .input-label {
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.875rem;
            font-weight: 500;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        /* Primary Button - Cyan Glow */
        .stButton > button {
            background: linear-gradient(135deg, rgba(0, 243, 255, 0.9), rgba(0, 200, 255, 0.9)) !important;
            color: #000 !important;
            border: none !important;
            border-radius: 16px !important;
            padding: 18px 32px !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
            letter-spacing: 0.02em !important;
            box-shadow: 
                0 4px 20px rgba(0, 243, 255, 0.3),
                0 0 0 1px rgba(255, 255, 255, 0.2) inset !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            position: relative;
            overflow: hidden;
        }
        
        .stButton > button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
            transition: left 0.5s;
        }
        
        .stButton > button:hover::before {
            left: 100%;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px) scale(1.02);
            box-shadow: 
                0 8px 30px rgba(0, 243, 255, 0.5),
                0 0 0 1px rgba(255, 255, 255, 0.3) inset !important;
        }
        
        .stButton > button:active {
            transform: translateY(0) scale(0.98);
        }
        
        /* Secondary Button */
        button[kind="secondary"] {
            background: rgba(255, 255, 255, 0.1) !important;
            color: #fff !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }
        
        /* Tabs - Glass Style */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: rgba(0, 0, 0, 0.2);
            padding: 8px;
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .stTabs [data-baseweb="tab"] {
            background: transparent !important;
            border-radius: 12px !important;
            padding: 12px 24px !important;
            color: rgba(255, 255, 255, 0.6) !important;
            font-weight: 500 !important;
            border: none !important;
            transition: all 0.3s ease !important;
        }
        
        .stTabs [aria-selected="true"] [data-baseweb="tab"] {
            background: rgba(0, 243, 255, 0.2) !important;
            color: #00f3ff !important;
            box-shadow: 0 2px 8px rgba(0, 243, 255, 0.2) !important;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            color: rgba(255, 255, 255, 0.9) !important;
            background: rgba(255, 255, 255, 0.05) !important;
        }
        
        /* Expander - Glass */
        .streamlit-expanderHeader {
            background: rgba(255, 255, 255, 0.05) !important;
            backdrop-filter: blur(10px) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 16px !important;
            color: #fff !important;
            font-weight: 500 !important;
            padding: 16px 20px !important;
            transition: all 0.3s ease !important;
        }
        
        .streamlit-expanderHeader:hover {
            background: rgba(255, 255, 255, 0.1) !important;
            border-color: rgba(0, 243, 255, 0.3) !important;
        }
        
        /* IMPROVED PLACE SELECTION - Visual Cards */
        .place-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 20px;
            margin: 12px 0;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }
        
        .place-card:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: rgba(0, 243, 255, 0.4);
            transform: translateX(8px);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        }
        
        .place-card.selected {
            background: rgba(0, 243, 255, 0.15);
            border-color: rgba(0, 243, 255, 0.6);
            box-shadow: 0 0 0 1px rgba(0, 243, 255, 0.3), 0 4px 20px rgba(0, 243, 255, 0.2);
        }
        
        .place-card.selected::after {
            content: '✓';
            position: absolute;
            top: 12px;
            right: 12px;
            width: 28px;
            height: 28px;
            background: rgba(0, 243, 255, 0.9);
            color: #000;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 14px;
            box-shadow: 0 2px 8px rgba(0, 243, 255, 0.4);
        }
        
        .place-category-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
        }
        
        .place-time {
            color: rgba(255, 255, 255, 0.5);
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        /* Category Colors */
        .cat-dining { background: rgba(255, 100, 100, 0.2); color: #ff6464; }
        .cat-hotel { background: rgba(100, 255, 100, 0.2); color: #64ff64; }
        .cat-event { background: rgba(255, 100, 255, 0.2); color: #ff64ff; }
        .cat-attraction { background: rgba(0, 243, 255, 0.2); color: #00f3ff; }
        .cat-shopping { background: rgba(255, 200, 100, 0.2); color: #ffc864; }
        
        /* Checkbox Replacement - Toggle Switch */
        .toggle-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: pointer;
        }
        
        .toggle-switch {
            width: 52px;
            height: 28px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 14px;
            position: relative;
            transition: all 0.3s ease;
        }
        
        .toggle-switch.active {
            background: rgba(0, 243, 255, 0.6);
        }
        
        .toggle-switch::after {
            content: '';
            position: absolute;
            width: 24px;
            height: 24px;
            background: #fff;
            border-radius: 50%;
            top: 2px;
            left: 2px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        .toggle-switch.active::after {
            left: 26px;
        }
        
        /* Map Container - Glass */
        .map-container {
            background: rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        }
        
        /* Alerts - Glass Style */
        .stAlert {
            border-radius: 16px !important;
            backdrop-filter: blur(10px) !important;
            border: 1px solid !important;
            font-weight: 500 !important;
        }
        
        .stSuccess {
            background: rgba(100, 255, 100, 0.1) !important;
            border-color: rgba(100, 255, 100, 0.3) !important;
            color: #64ff64 !important;
        }
        
        .stWarning {
            background: rgba(255, 200, 100, 0.1) !important;
            border-color: rgba(255, 200, 100, 0.3) !important;
            color: #ffc864 !important;
        }
        
        .stError {
            background: rgba(255, 100, 100, 0.1) !important;
            border-color: rgba(255, 100, 100, 0.3) !important;
            color: #ff6464 !important;
        }
        
        /* Progress Bar */
        .stProgress > div > div {
            background: linear-gradient(90deg, #00f3ff, #00c8ff) !important;
            border-radius: 10px !important;
            box-shadow: 0 0 10px rgba(0, 243, 255, 0.5);
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(0, 243, 255, 0.6);
        }
        
        /* Loading Animation */
        .glass-loading {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 60px;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-top-color: #00f3ff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            box-shadow: 0 0 20px rgba(0, 243, 255, 0.3);
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Metric Cards */
        .metric-glass {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 20px;
            text-align: center;
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: #00f3ff;
            text-shadow: 0 0 20px rgba(0, 243, 255, 0.5);
        }
        
        .metric-label {
            font-size: 0.875rem;
            color: rgba(255, 255, 255, 0.6);
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-top: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# ==================================================
# LOAD AUTHENTICATION CONFIG
# ==================================================
try:
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
    )
except FileNotFoundError:
    st.error("⚠️ Configuration file not found")
    st.stop()
except Exception as e:
    st.error(f"⚠️ Error: {str(e)}")
    st.stop()

# ==================================================
# LOGIN UI - Glass Style
# ==================================================
authenticator.login(location='main')

if st.session_state.get('authentication_status') is False:
    st.error('❌ Access Denied')
    st.stop()
    
elif st.session_state.get('authentication_status') is None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div style="text-align: center; padding: 60px 40px; background: rgba(255,255,255,0.05); backdrop-filter: blur(20px); border-radius: 24px; border: 1px solid rgba(255,255,255,0.1); margin-top: 100px;">
                <h2 style="color: #00f3ff; margin-bottom: 20px;">Authentication Required</h2>
                <p style="color: rgba(255,255,255,0.6);">Please sign in to access the spatial travel system</p>
            </div>
        """, unsafe_allow_html=True)
    st.stop()

# ==================================================
# MAIN APP
# ==================================================
if st.session_state.get('authentication_status'):
    
    # Initialize session state
    if "trip" not in st.session_state:
        st.session_state.trip = None
    if "center" not in st.session_state:
        st.session_state.center = None
    if "selected_places" not in st.session_state:
        st.session_state.selected_places = set()

    # Load API keys
    load_dotenv()
    GEMINI_KEY = os.getenv("GEMINI_API_KEY")
    AMADEUS_KEY = os.getenv("AMADEUS_API_KEY")
    AMADEUS_SECRET = os.getenv("AMADEUS_API_SECRET")

    if not GEMINI_KEY:
        st.error("⚠️ API key missing")
        st.stop()

    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    # Color scheme
    COLORS = {
        "dining": "#ff6464",
        "hotel": "#64ff64",
        "event": "#ff64ff",
        "attraction": "#00f3ff",
        "shopping": "#ffc864"
    }

    CATEGORY_ICONS = {
        "dining": "🍽️",
        "hotel": "🏨",
        "event": "🎭",
        "attraction": "🎯",
        "shopping": "🛍️"
    }

    # ==================================================
    # HELPER FUNCTIONS
    # ==================================================
    def sanitize_input(text, max_length=500):
        if not text:
            return ""
        text = text[:max_length]
        for char in ['<', '>', '"', "'", '{', '}', '\\', '\0']:
            text = text.replace(char, '')
        return text.strip()

    @lru_cache(maxsize=128)
    def get_location(place):
        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {"q": place, "format": "json", "limit": 1}
            headers = {"User-Agent": "goingplaces-ai-app"}
            r = requests.get(url, params=params, headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
            return None, None
        except Exception as e:
            logger.error(f"Geocoding error: {str(e)}")
            return None, None

    def extract_json_robust(text):
        import re
        if not text:
            return None
        try:
            text = re.sub(r'```json', '', text)
            text = re.sub(r'```', '', text)
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1:
                return None
            return json.loads(text[start:end+1])
        except Exception as e:
            logger.error("JSON extraction failed")
            return None

    def validate_trip_data(data):
        try:
            if "days" not in data:
                return False
            for day in data["days"]:
                if "day" not in day or "places" not in day:
                    return False
                for place in day["places"]:
                    if not all(k in place for k in ["name", "category", "description"]):
                        return False
            return True
        except Exception as e:
            return False

    def generate_plan(dest, days, people, budget, interest):
        try:
            interest = sanitize_input(interest)
            dest = sanitize_input(dest)
            prompt = f"""Create a {days}-day itinerary for {dest}.
Rules:
- 5 places per day
- Include dining, attractions, shopping, events
- Do NOT include coordinates
- Only return JSON
- No explanation
- No markdown

Format:
{{"days":[{{"day":1,"theme":"Day theme","places":[{{"name":"Place Name","category":"dining","description":"Short description","timeOfDay":"Morning"}}]}}]}}

Trip details:
People: {people}
Budget: {budget}
Interest: {interest}"""
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return None

    def get_amadeus_token():
        try:
            url = "https://test.api.amadeus.com/v1/security/oauth2/token"
            data = {
                "grant_type": "client_credentials",
                "client_id": AMADEUS_KEY,
                "client_secret": AMADEUS_SECRET
            }
            r = requests.post(url, data=data, timeout=10)
            r.raise_for_status()
            return r.json().get("access_token")
        except Exception as e:
            logger.error(f"Amadeus token error: {str(e)}")
            return None

    def search_flights(origin, dest, date):
        try:
            token = get_amadeus_token()
            if not token:
                return {"error": "Authentication failed"}
            url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
            headers = {"Authorization": f"Bearer {token}"}
            params = {
                "originLocationCode": origin.upper(),
                "destinationLocationCode": dest.upper(),
                "departureDate": str(date),
                "adults": 1,
                "max": 5
            }
            r = requests.get(url, headers=headers, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            if "errors" in data:
                return {"error": data["errors"][0].get("title", "Unknown error")}
            return data
        except Exception as e:
            return {"error": str(e)}

    def search_hotels(city):
        try:
            token = get_amadeus_token()
            if not token:
                return {"error": "Authentication failed"}
            url = "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city"
            headers = {"Authorization": f"Bearer {token}"}
            params = {"cityCode": city.upper()}
            r = requests.get(url, headers=headers, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            if "errors" in data:
                return {"error": data["errors"][0].get("title", "Unknown error")}
            return data
        except Exception as e:
            return {"error": str(e)}

    # ==================================================
    # HERO BANNER - Glassmorphic
    # ==================================================
    st.markdown("""
        <div class="hero-glass">
            <div class="hero-content">
                <h3 class="hero-title">Going Places</h3>
                <p class="hero-subtitle">One Life.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ==================================================
    # INPUT SECTION - Floating Glass Panels
    # ==================================================
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown('<h2 style="margin-top: 0;">Plan Your Journey</h2>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<p class="input-label">Destination</p>', unsafe_allow_html=True)
        dest = st.text_input("", placeholder="e.g., Tokyo", label_visibility="collapsed")
    with col2:
        st.markdown('<p class="input-label">Duration</p>', unsafe_allow_html=True)
        days = st.number_input("", 1, 30, 5, label_visibility="collapsed")
    with col3:
        st.markdown('<p class="input-label">Travelers</p>', unsafe_allow_html=True)
        people = st.number_input("", 1, 20, 1, label_visibility="collapsed")
    with col4:
        st.markdown('<p class="input-label">Budget (INR)</p>', unsafe_allow_html=True)
        budget = st.number_input("", 5000, 10000000, 50000, step=5000, label_visibility="collapsed")

    col5, col6 = st.columns([2, 1])
    with col5:
        st.markdown('<p class="input-label">Interests</p>', unsafe_allow_html=True)
        interest = st.text_input("", placeholder="Nature, History, Food...", label_visibility="collapsed")
    with col6:
        st.markdown('<p class="input-label">Departure</p>', unsafe_allow_html=True)
        travel_date = st.date_input("", datetime.date.today() + datetime.timedelta(days=7), label_visibility="collapsed")

    st.markdown('<br>', unsafe_allow_html=True)
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        generate_btn = st.button("✨ Generate Itinerary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ==================================================
    # GENERATE ITINERARY
    # ==================================================
    if generate_btn:
        if not dest:
            st.warning("⚠️ Please enter a destination")
        else:
            loading_placeholder = st.empty()
            
            with loading_placeholder.container():
                st.markdown("""
                    <div class="glass-loading">
                        <div class="spinner"></div>
                        <p style="color: rgba(255,255,255,0.8); margin-top: 20px; font-weight: 500;">Generating your spatial itinerary...</p>
                    </div>
                """, unsafe_allow_html=True)
            
            try:
                lat, lon = get_location(dest)
                if not lat or not lon:
                    loading_placeholder.empty()
                    st.error(f"❌ Location not found: '{dest}'")
                    st.stop()
                
                raw = generate_plan(dest, days, people, budget, interest)
                if not raw:
                    loading_placeholder.empty()
                    st.error("❌ AI generation failed")
                    st.stop()
                
                data = extract_json_robust(raw)
                if not data or not validate_trip_data(data):
                    loading_placeholder.empty()
                    st.error("❌ Invalid itinerary format")
                    st.stop()
                
                # Geocode places
                for d in data["days"]:
                    for p in d["places"]:
                        lat_p, lon_p = get_location(f"{p['name']} {dest}")
                        if lat_p and lon_p:
                            p["lat"], p["lon"] = lat_p, lon_p
                        else:
                            p["lat"], p["lon"] = lat, lon
                        p["selected"] = True
                        p["id"] = f"{d['day']}_{p['name']}_{random.randint(1000,9999)}"
                
                st.session_state.trip = data
                st.session_state.center = (lat, lon)
                st.session_state.selected_places = set()
                
                loading_placeholder.empty()
                st.success("✅ Itinerary generated successfully!")
                
            except Exception as e:
                loading_placeholder.empty()
                st.error(f"❌ Error: {str(e)}")

    # ==================================================
    # DASHBOARD - Glass Layout
    # ==================================================
    if st.session_state.trip:
        trip = st.session_state.trip
        st.markdown("---")
        
        # Header with stats
        col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
        with col_stats1:
            st.markdown(f"""
                <div class="metric-glass">
                    <div class="metric-value">{len(trip['days'])}</div>
                    <div class="metric-label">Days</div>
                </div>
            """, unsafe_allow_html=True)
        with col_stats2:
            total_places = sum(len(d['places']) for d in trip['days'])
            st.markdown(f"""
                <div class="metric-glass">
                    <div class="metric-value">{total_places}</div>
                    <div class="metric-label">Places</div>
                </div>
            """, unsafe_allow_html=True)
        with col_stats3:
            st.markdown(f"""
                <div class="metric-glass">
                    <div class="metric-value">₹{budget//1000}k</div>
                    <div class="metric-label">Budget</div>
                </div>
            """, unsafe_allow_html=True)
        with col_stats4:
            st.markdown(f"""
                <div class="metric-glass">
                    <div class="metric-value">{people}</div>
                    <div class="metric-label">Travelers</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Main content
        left, right = st.columns([2, 3], gap="large")

        # LEFT PANEL - Visual Place Selection
        with left:
            st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
            tab_iter, tab_flights, tab_hotels = st.tabs(["📍 Itinerary", "✈️ Flights", "🏨 Hotels"])

            with tab_iter:
                for d in trip["days"]:
                    day_theme = d.get('theme', 'Exploration')
                    
                    with st.expander(f"**Day {d['day']}** — {day_theme}", expanded=(d["day"] == 1)):
                        
                        # Day summary
                        selected_in_day = [p for p in d["places"] if p.get("selected", False)]
                        st.caption(f"{len(selected_in_day)} of {len(d['places'])} places selected")
                        
                        # Visual place cards
                        for i, p in enumerate(d["places"]):
                            place_id = p.get('id', f"{d['day']}_{i}")
                            is_selected = p.get("selected", False)
                            
                            # Determine category class
                            cat = p.get("category", "attraction").lower()
                            cat_class = f"cat-{cat}"
                            cat_color = COLORS.get(cat, "#00f3ff")
                            
                            # Card HTML
                            card_class = "place-card selected" if is_selected else "place-card"
                            
                            st.markdown(f"""
                                <div class="{card_class}" onclick="togglePlace('{place_id}')" id="card-{place_id}">
                                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                        <div style="flex: 1;">
                                            <span class="place-category-badge {cat_class}">{CATEGORY_ICONS.get(cat, '📍')} {cat.title()}</span>
                                            <h4 style="margin: 8px 0 4px 0; color: #fff; font-size: 1.1rem; font-weight: 600;">{p['name']}</h4>
                                            <p style="margin: 0; color: rgba(255,255,255,0.7); font-size: 0.9rem; line-height: 1.4;">{p['description'][:80]}...</p>
                                            <p class="place-time">🕐 {p.get('timeOfDay', 'All day')}</p>
                                        </div>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # Hidden checkbox for functionality
                            key = f"place_{place_id}"
                            new_selected = st.checkbox("Select", value=is_selected, key=key, label_visibility="collapsed")
                            p["selected"] = new_selected

            with tab_flights:
                st.markdown('<h3 style="margin-top: 0;">Find Flights</h3>', unsafe_allow_html=True)
                col_origin, col_dest = st.columns(2)
                with col_origin:
                    origin = st.text_input("From (Airport)", "DEL")
                with col_dest:
                    dest_air = st.text_input("To (Airport)", key="dest_flight")
                
                if st.button("🔍 Search Flights", use_container_width=True, key="search_flights_btn"):
                    if origin and dest_air:
                        with st.spinner("Searching..."):
                            flights = search_flights(origin, dest_air, str(travel_date))
                            if "error" in flights:
                                st.error(flights["error"])
                            elif flights and "data" in flights:
                                for f in flights["data"][:3]:
                                    airline = f.get("itineraries", [{}])[0].get("segments", [{}])[0].get("carrierCode", "N/A")
                                    price = f.get("price", {}).get("total", "N/A")
                                    st.metric(airline, f"₹{float(price)*83:.0f}" if price != "N/A" else "N/A")

            with tab_hotels:
                st.markdown('<h3 style="margin-top: 0;">Find Hotels</h3>', unsafe_allow_html=True)
                city_code = st.text_input("City Code", key="dest_hotel")
                if st.button("🔍 Search Hotels", use_container_width=True, key="search_hotels_btn"):
                    if city_code:
                        with st.spinner("Searching..."):
                            hotels = search_hotels(city_code)
                            if "error" in hotels:
                                st.error(hotels["error"])
                            elif hotels and "data" in hotels:
                                for h in hotels["data"][:5]:
                                    st.write(f"🏨 {h.get('name', 'Unknown')}")
            
            st.markdown('</div>', unsafe_allow_html=True)

        # RIGHT PANEL - Map
        with right:
            st.markdown('<div class="glass-panel" style="padding: 0; overflow: hidden;">', unsafe_allow_html=True)
            st.markdown('<h3 style="padding: 24px 24px 0 24px; margin: 0;">Spatial Map View</h3>', unsafe_allow_html=True)
            
            try:
                lat, lon = st.session_state.center
                m = folium.Map(
                    location=[lat, lon],
                    zoom_start=13,
                    tiles="CartoDB dark_matter",
                    attr=' '
                )
                
                # Add selected places to map
                selected_count = 0
                for d in trip["days"]:
                    for p in d["places"]:
                        if p.get("selected", False):
                            selected_count += 1
                            cat = p.get("category", "attraction").lower()
                            color = COLORS.get(cat, "#00f3ff")
                            
                            folium.Marker(
                                [p["lat"], p["lon"]],
                                popup=folium.Popup(f"""
                                    <div style="font-family: sans-serif; min-width: 150px;">
                                        <h4 style="margin: 0 0 5px 0; color: {color};">{p['name']}</h4>
                                        <p style="margin: 0; color: #666; font-size: 0.9rem;">{cat.title()}</p>
                                    </div>
                                """, max_width=200),
                                tooltip=p['name'],
                                icon=folium.DivIcon(html=f"""
                                    <div style="
                                        background-color: {color};
                                        width: 16px;
                                        height: 16px;
                                        border-radius: 50%;
                                        border: 3px solid white;
                                        box-shadow: 0 0 10px {color};
                                    "></div>
                                """)
                            ).add_to(m)
                
                st.caption(f"📍 {selected_count} places mapped")
                st_folium(m, width=None, height=550, key="main_map")
                
            except Exception as e:
                st.error(f"Map error: {str(e)}")
            
            st.markdown('</div>', unsafe_allow_html=True)

        # Summary Section
        st.markdown("---")
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        st.markdown('<h2 style="margin-top: 0;">Trip Summary</h2>', unsafe_allow_html=True)
        
        sum_col1, sum_col2 = st.columns([3, 1])
        
        with sum_col1:
            for d in trip["days"]:
                day_items = [p for p in d["places"] if p.get("selected", False)]
                if day_items:
                    st.markdown(f'<h3>Day {d["day"]} — {len(day_items)} places</h3>', unsafe_allow_html=True)
                    cols = st.columns(min(len(day_items), 3))
                    for idx, p in enumerate(day_items):
                        with cols[idx % 3]:
                            cat = p.get("category", "attraction")
                            st.markdown(f"""
                                <div style="background: rgba(255,255,255,0.05); border-radius: 12px; padding: 12px; margin: 8px 0; border-left: 3px solid {COLORS.get(cat, '#00f3ff')};">
                                    <p style="margin: 0; color: #fff; font-weight: 500; font-size: 0.9rem;">{CATEGORY_ICONS.get(cat, '📍')} {p['name']}</p>
                                    <p style="margin: 4px 0 0 0; color: rgba(255,255,255,0.5); font-size: 0.75rem; text-transform: uppercase;">{cat}</p>
                                </div>
                            """, unsafe_allow_html=True)
        
        with sum_col2:
            total_selected = sum(len([p for p in d["places"] if p.get("selected", False)]) for d in trip['days'])
            st.metric("Selected", f"{total_selected}")
            st.metric("Total", f"{sum(len(d['places']) for d in trip['days'])}")
            
            if st.button("📥 Export", use_container_width=True):
                st.info("Export coming soon!")
        
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.error("❌ Authentication required")
