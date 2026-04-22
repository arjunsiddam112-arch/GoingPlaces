
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

# =========================
# PAGE STATE
# =========================
if "page" not in st.session_state:
    st.session_state.page = "home"

if "trip" not in st.session_state:
    st.session_state.trip = None
if "center" not in st.session_state:
    st.session_state.center = None
if "selected_places" not in st.session_state:
    st.session_state.selected_places = set()

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
# AUTH MODE STATE (LOGIN / SIGNUP)
# ==================================================
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"

# ==================================================
# LOAD AUTH CONFIG
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
# TOGGLE BUTTONS
# ==================================================
col1, col2 = st.columns(2)

with col1:
    if st.button(" Login", use_container_width=True):
        st.session_state.auth_mode = "login"

with col2:
    if st.button(" Sign Up", use_container_width=True):
        st.session_state.auth_mode = "signup"

# ==================================================
# LOGIN MODE
# ==================================================
if st.session_state.auth_mode == "login":

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
                    <p style="color: rgba(255,255,255,0.6);">Please sign in to continue</p>
                </div>
            """, unsafe_allow_html=True)
        st.stop()

# ==================================================
# SIGNUP MODE
# ==================================================
elif st.session_state.auth_mode == "signup":

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
            <div style="padding: 40px; background: rgba(255,255,255,0.05); backdrop-filter: blur(20px); border-radius: 24px; border: 1px solid rgba(255,255,255,0.1); margin-top: 60px;">
                <h2 style="color: #00f3ff; text-align:center;">Create Account</h2>
            </div>
        """, unsafe_allow_html=True)

        new_name = st.text_input("Full Name")
        new_username = st.text_input("Username")
        new_password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        if st.button("Create Account", use_container_width=True):

            if not new_name or not new_username or not new_password:
                st.warning("⚠️ Fill all fields")

            elif new_password != confirm_password:
                st.error("❌ Passwords do not match")

            else:
                # Reload config
                with open('config.yaml') as file:
                    config = yaml.load(file, Loader=SafeLoader)

                if new_username in config['credentials']['usernames']:
                    st.error("❌ Username already exists")

                else:
                    # Hash password
                    hashed_password = stauth.Hasher().hash(new_password)

                    # Add new user
                    config['credentials']['usernames'][new_username] = {
                        'name': new_name,
                        'password': hashed_password
                    }

                    # Save file
                    with open('config.yaml', 'w') as file:
                        yaml.dump(config, file)

                    st.success("✅ Account created successfully!")
                    st.session_state.auth_mode = "login"
                    st.rerun()

    st.stop()

# ==================================================
# AFTER LOGIN (MAIN APP)
# ==================================================
if st.session_state.get('authentication_status'):


    st.sidebar.write(f"👤 {st.session_state['name']}")

# ==================================================
# MAIN APP
# ==================================================
if st.session_state.get('authentication_status'):
    authenticator.logout("Logout", "sidebar", key="logout_btn_main")
    
    # Initialize session state
    if "trip" not in st.session_state:
        st.session_state.trip = None
    if "center" not in st.session_state:
        st.session_state.center = None
    if "selected_places" not in st.session_state:
        st.session_state.selected_places = set()
    if "hotels" not in st.session_state:
        st.session_state.hotels = []
    if "selected_hotel" not in st.session_state:
        st.session_state.selected_hotel = {}

    # Load API keys
    load_dotenv()
    GEMINI_KEY = os.getenv("GEMINI_API_KEY")
    AMADEUS_KEY = os.getenv("AMADEUS_API_KEY")
    AMADEUS_SECRET = os.getenv("AMADEUS_API_SECRET")
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

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

    def is_valid_coordinates(lat, lon):
        try:
            lat = float(lat)
            lon = float(lon)
            return -90 <= lat <= 90 and -180 <= lon <= 180
        except (TypeError, ValueError):
            return False

    def known_destination_center(dest):
        query = sanitize_input(dest, 100).lower()
        city_centers = {
            "tokyo": (35.6762, 139.6503),
            "kyoto": (35.0116, 135.7681),
            "osaka": (34.6937, 135.5023),
            "paris": (48.8566, 2.3522),
            "london": (51.5072, -0.1276),
            "new york": (40.7128, -74.0060),
            "dubai": (25.2048, 55.2708),
            "singapore": (1.3521, 103.8198),
            "bangkok": (13.7563, 100.5018),
            "bali": (-8.3405, 115.0920),
            "delhi": (28.6139, 77.2090),
            "mumbai": (19.0760, 72.8777),
            "goa": (15.2993, 74.1240),
            "jaipur": (26.9124, 75.7873),
            "udaipur": (24.5854, 73.7125),
            "agra": (27.1767, 78.0081),
            "chennai": (13.0827, 80.2707),
            "bengaluru": (12.9716, 77.5946),
            "bangalore": (12.9716, 77.5946),
            "hyderabad": (17.3850, 78.4867),
            "kolkata": (22.5726, 88.3639),
            "pune": (18.5204, 73.8567),
            "sydney": (-33.8688, 151.2093),
            "rome": (41.9028, 12.4964),
            "barcelona": (41.3874, 2.1686),
            "istanbul": (41.0082, 28.9784),
            "san francisco": (37.7749, -122.4194),
            "los angeles": (34.0522, -118.2437),
            "toronto": (43.6532, -79.3832),
            "seoul": (37.5665, 126.9780),
            "hong kong": (22.3193, 114.1694),
        }
        for city, center in city_centers.items():
            if city in query:
                return center
        return None

    def place_search_text(place, dest):
        name = place.get("name", "")
        address = place.get("address") or place.get("area") or place.get("location") or ""
        if address:
            return sanitize_input(f"{name}, {address}, {dest}", 300)
        return sanitize_input(f"{name}, {dest}", 300)

    def apply_generated_coordinates(place):
        lat = place.get("lat", place.get("latitude"))
        lon = place.get("lon", place.get("lng", place.get("longitude")))
        if not is_valid_coordinates(lat, lon):
            return False
        place["lat"], place["lon"] = float(lat), float(lon)
        place["map_status"] = "generated"
        return True

    @lru_cache(maxsize=128)
    def get_location(place):
        try:
            last_request_at = st.session_state.get("_last_geocode_request_at", 0)
            elapsed = time.time() - last_request_at
            if elapsed < 1:
                time.sleep(1 - elapsed)

            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": place,
                "format": "json",
                "limit": 1,
                "addressdetails": 1,
                "dedupe": 1
            }
            headers = {"User-Agent": "goingplaces-ai-app"}
            r = requests.get(url, params=params, headers=headers, timeout=10)
            st.session_state["_last_geocode_request_at"] = time.time()
            r.raise_for_status()
            data = r.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
            return None, None
        except Exception as e:
            logger.error(f"Geocoding error: {str(e)}")
            return None, None

    def get_weather(city):
        city = sanitize_input(city, 100)
        if not city or not WEATHER_API_KEY:
            return None

        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            main = data.get("main", {})
            weather = (data.get("weather") or [{}])[0]
            wind = data.get("wind", {})

            return {
                "city": sanitize_input(data.get("name", city), 100),
                "temperature": main.get("temp"),
                "feels_like": main.get("feels_like"),
                "humidity": main.get("humidity"),
                "description": sanitize_input(weather.get("description", "Unknown").title(), 120),
                "wind_speed": wind.get("speed")
            }
        except Exception as e:
            logger.error(f"Weather API error: {str(e)}")
            return None

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

    def fallback_hotels(dest):
        city = sanitize_input(dest) or "Destination"
        return [
            {"name": f"{city} Comfort Stay", "price": 3000, "rating": 4.2},
            {"name": f"{city} Central Hotel", "price": 4500, "rating": 4.5},
            {"name": f"{city} Budget Inn", "price": 1800, "rating": 3.9},
            {"name": f"{city} Premium Suites", "price": 7000, "rating": 4.7},
            {"name": f"{city} City Lodge", "price": 2500, "rating": 4.0}
        ]

    def validate_trip_data(data):
        try:
            if not isinstance(data, dict) or "days" not in data:
                return False
            if not isinstance(data["days"], list):
                return False
            for day in data["days"]:
                if not isinstance(day, dict) or "day" not in day or "places" not in day:
                    return False
                if not isinstance(day["places"], list):
                    return False
                for place in day["places"]:
                    if not isinstance(place, dict):
                        return False
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
- Each place must include a precise address or neighborhood in an address field
- Each place must include real-world decimal lat and lon fields for the exact place
- Include 5 hotel recommendations in the hotels array
- Hotel prices must be numeric INR values per night
- Hotel ratings must be numeric values out of 5
- Only return JSON
- No explanation
- No markdown

Format:
{{"days":[{{"day":1,"places":[{{"name":"Place Name","category":"attraction","description":"Short description","address":"Neighborhood or full address, City, Country","lat":35.6895,"lon":139.6917}}]}}],"hotels":[{{"name":"Hotel Name","price":3000,"rating":4.2}}]}}

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

    def normalize_hotels(raw_hotels):
        if not isinstance(raw_hotels, list):
            raw_hotels = []

        hotels = []
        for h in raw_hotels:
            if not isinstance(h, dict):
                continue

            try:
                price = float(h.get("price", 9999))
            except (TypeError, ValueError):
                price = 9999

            try:
                rating = float(h.get("rating", 0))
            except (TypeError, ValueError):
                rating = 0

            hotels.append({
                "name": h.get("name", "Unknown"),
                "price": price,
                "rating": rating
            })

        return hotels

    def sort_hotels(hotels, order="asc"):
        return sorted(
            hotels,
            key=lambda x: (x["price"], -x["rating"]),
            reverse=(order == "desc")
        )

    def render_category_legend():
        legend_items = "".join(
            f"""
            <div style="display: flex; align-items: center; gap: 8px; min-width: fit-content;">
                <span style="
                    display: inline-block;
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    background: {color};
                    box-shadow: 0 0 10px {color};
                    border: 2px solid rgba(255,255,255,0.85);
                "></span>
                <span style="color: rgba(255,255,255,0.82); font-size: 0.85rem; font-weight: 500;">
                    {CATEGORY_ICONS.get(category, '📍')} {category.title()}
                </span>
            </div>
            """
            for category, color in COLORS.items()
        )

        st.markdown(f"""
            <div style="
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                gap: 10px 16px;
                padding: 14px 24px 10px 24px;
                border-bottom: 1px solid rgba(255,255,255,0.08);
            ">
                <span style="color: rgba(255,255,255,0.55); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700;">
                    Event Type
                </span>
                {legend_items}
            </div>
        """, unsafe_allow_html=True)



if st.session_state.page == "home":
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
        interest_options = [
         "Nature 🌿",
        "History 🏛️",
        "Food 🍜",
        "Shopping 🛍️",
        "Nightlife 🌃",
        "Adventure 🧗",
        "Culture 🎭",
        "Relaxation 🧘",
        "Photography 📸",
        "Beaches 🏖️"
    ]

        selected_interests = st.multiselect(
        "",
        interest_options,
        placeholder="Select your interests",
        label_visibility="collapsed"
    )

    # Convert to string (for your existing AI function)
    interest = ", ".join(selected_interests)
    with col6:
        st.markdown('<p class="input-label">Departure</p>', unsafe_allow_html=True)
        travel_date = st.date_input("", datetime.date.today() + datetime.timedelta(days=7), label_visibility="collapsed")

    st.markdown('<br>', unsafe_allow_html=True)
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        generate_btn = st.button("✨ Generate Itinerary", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # ==================================================
    # WEATHER INSIGHTS
    # ==================================================
    weather_default_city = sanitize_input(dest, 100) if "dest" in locals() and dest else sanitize_input(st.session_state.get("destination", ""), 100)
    if weather_default_city and not st.session_state.get("weather_city"):
        st.session_state.weather_city = weather_default_city

    st.markdown('<br>', unsafe_allow_html=True)
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown('<h2 style="margin-top: 0;">🌦️ Weather Insights</h2>', unsafe_allow_html=True)

    weather_col1, weather_col2 = st.columns([3, 1])
    with weather_col1:
        st.markdown('<p class="input-label">City</p>', unsafe_allow_html=True)
        weather_city = st.text_input(
            "",
            placeholder="Enter a city name",
            key="weather_city",
            label_visibility="collapsed"
        )
    with weather_col2:
        st.markdown('<p class="input-label">&nbsp;</p>', unsafe_allow_html=True)
        get_weather_btn = st.button("Get Weather", use_container_width=True, key="get_weather_btn")

    if get_weather_btn:
        if not weather_city:
            st.error("Please enter a city name to get weather insights.")
        else:
            weather_data = get_weather(weather_city)
            if weather_data:
                condition = weather_data["description"].lower()
                weather_emoji = "☀️"
                if "rain" in condition:
                    weather_emoji = "🌧️"
                elif "cloud" in condition:
                    weather_emoji = "☁️"
                elif "clear" in condition:
                    weather_emoji = "☀️"
                elif "snow" in condition:
                    weather_emoji = "❄️"
                elif "storm" in condition or "thunder" in condition:
                    weather_emoji = "⛈️"
                elif "mist" in condition or "fog" in condition or "haze" in condition:
                    weather_emoji = "🌫️"

                st.markdown(f"""
                    <div style="
                        margin-top: 18px;
                        padding: 24px;
                        border-radius: 20px;
                        background: linear-gradient(135deg, rgba(0, 243, 255, 0.14), rgba(255, 255, 255, 0.06));
                        border: 1px solid rgba(0, 243, 255, 0.25);
                        box-shadow: 0 8px 28px rgba(0, 0, 0, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.12);
                    ">
                        <div style="display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap;">
                            <div>
                                <p style="margin: 0; color: rgba(255,255,255,0.58); text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.78rem; font-weight: 700;">Current Weather</p>
                                <h3 style="margin: 6px 0 0 0; color: #fff; font-size: 1.55rem;">{weather_emoji} {weather_data["city"]}</h3>
                            </div>
                            <div style="color: #00f3ff; font-size: 2.4rem; font-weight: 700; text-shadow: 0 0 20px rgba(0, 243, 255, 0.45);">
                                {weather_data["temperature"]}°C
                            </div>
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 14px; margin-top: 22px;">
                            <div style="background: rgba(255,255,255,0.06); border-radius: 14px; padding: 14px; border-left: 3px solid #00f3ff;">
                                <p style="margin: 0; color: rgba(255,255,255,0.55); font-size: 0.8rem;">Feels Like</p>
                                <p style="margin: 6px 0 0 0; color: #fff; font-weight: 600;">{weather_data["feels_like"]}°C</p>
                            </div>
                            <div style="background: rgba(255,255,255,0.06); border-radius: 14px; padding: 14px; border-left: 3px solid #00f3ff;">
                                <p style="margin: 0; color: rgba(255,255,255,0.55); font-size: 0.8rem;">Condition</p>
                                <p style="margin: 6px 0 0 0; color: #fff; font-weight: 600;">{weather_data["description"]}</p>
                            </div>
                            <div style="background: rgba(255,255,255,0.06); border-radius: 14px; padding: 14px; border-left: 3px solid #00f3ff;">
                                <p style="margin: 0; color: rgba(255,255,255,0.55); font-size: 0.8rem;">Humidity</p>
                                <p style="margin: 6px 0 0 0; color: #fff; font-weight: 600;">{weather_data["humidity"]}%</p>
                            </div>
                            <div style="background: rgba(255,255,255,0.06); border-radius: 14px; padding: 14px; border-left: 3px solid #00f3ff;">
                                <p style="margin: 0; color: rgba(255,255,255,0.55); font-size: 0.8rem;">Wind Speed</p>
                                <p style="margin: 6px 0 0 0; color: #fff; font-weight: 600;">{weather_data["wind_speed"]} m/s</p>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.error("Unable to fetch weather data. Please check the city name.")

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
                if not is_valid_coordinates(lat, lon):
                    logger.warning(f"Destination geocode failed for {dest}")
                    known_center = known_destination_center(dest)
                    if known_center:
                        lat, lon = known_center
                    else:
                        lat = lon = None
                
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

                if not normalize_hotels(data.get("hotels", [])):
                    data["hotels"] = fallback_hotels(dest)
                
                # Geocode places and establish map center
                place_center = None
                unresolved_places = []
                for d in data["days"]:
                    for p in d["places"]:
                        has_generated_coordinates = apply_generated_coordinates(p)
                        lat_p, lon_p = get_location(place_search_text(p, dest))
                        if is_valid_coordinates(lat_p, lon_p):
                            p["lat"], p["lon"] = lat_p, lon_p
                            p["map_status"] = "exact"
                            if place_center is None:
                                place_center = (lat_p, lon_p)
                        elif has_generated_coordinates:
                            if place_center is None:
                                place_center = (p["lat"], p["lon"])
                        else:
                            unresolved_places.append(p)
                        p["selected"] = True
                        p["id"] = f"{d['day']}_{p['name']}_{random.randint(1000,9999)}"

                if not is_valid_coordinates(lat, lon) and place_center is not None:
                    lat, lon = place_center

                if not is_valid_coordinates(lat, lon):
                    st.warning("⚠️ Unable to determine a precise map center. Showing a default world map instead.")
                    lat, lon = 0.0, 0.0

                for p in unresolved_places:
                    p["lat"], p["lon"] = None, None
                    p["map_status"] = "unresolved"

                st.session_state.trip = data
                st.session_state.hotels = data.get("hotels", [])
                st.session_state.selected_hotel = {}
                st.session_state.destination = dest
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
                city_code = st.text_input("City Name", key="dest_hotel")
                col_sort, col_search = st.columns([1.5, 1])
                with col_sort:
                    sort_order = st.selectbox("Sort by Budget", ["Low to High", "High to Low"], key="hotel_sort")
                with col_search:
                    search_btn = st.button("🔍 Search Hotels", use_container_width=True, key="search_hotels_btn")

                hotel_list = normalize_hotels(st.session_state.get("hotels", []))
                order = "desc" if sort_order == "High to Low" else "asc"
                sorted_hotels = sort_hotels(hotel_list, order=order)

                if sorted_hotels:
                    hotel_names = [h["name"] for h in sorted_hotels]
                    current_name = st.session_state.get("selected_hotel", {}).get("name", "")
                    default_index = hotel_names.index(current_name) if current_name in hotel_names else 0
                    selected_name = st.radio(
                        "Select one hotel",
                        options=hotel_names,
                        index=default_index,
                        key="hotel_choice_radio"
                    )
                    selected_hotel = next((h for h in sorted_hotels if h["name"] == selected_name), None)
                    st.session_state.selected_hotel = selected_hotel or {}

                    for h in sorted_hotels:
                        st.markdown(f"""
                            <div style="background: rgba(255,255,255,0.05); border-radius: 12px; padding: 16px; margin: 8px 0; border-left: 3px solid #00f3ff;">
                                <h4 style="margin: 0 0 8px 0; color: #fff;">{h['name']}</h4>
                                <p style="margin: 0 0 4px 0; color: rgba(255,255,255,0.8);">💰 ₹{int(h['price']):,}</p>
                                <p style="margin: 0; color: rgba(255,255,255,0.6);">⭐ {h['rating']} / 5.0</p>
                            </div>
                        """, unsafe_allow_html=True)

                    if selected_hotel:
                        st.markdown(f"**Selected hotel:** {selected_hotel['name']}")
                else:
                    if search_btn:
                        st.info("No hotel data available yet. Generate an itinerary first.")
                    else:
                        st.info("Hotel recommendations are populated after itinerary generation.")
            
            st.markdown('</div>', unsafe_allow_html=True)

        # RIGHT PANEL - Map
        with right:
            st.markdown('<div class="glass-panel" style="padding: 0; overflow: hidden;">', unsafe_allow_html=True)
            st.markdown('<h3 style="padding: 24px 24px 0 24px; margin: 0;">Spatial Map View</h3>', unsafe_allow_html=True)
            render_category_legend()
            
            try:
                lat, lon = st.session_state.center
                current_destination = dest or st.session_state.get("destination", "")
                known_center = known_destination_center(current_destination)
                if known_center and (not is_valid_coordinates(lat, lon) or (float(lat) == 0.0 and float(lon) == 0.0)):
                    lat, lon = known_center
                    st.session_state.center = (lat, lon)
                elif not is_valid_coordinates(lat, lon):
                    lat, lon = 0.0, 0.0
                    st.session_state.center = (lat, lon)

                m = folium.Map(
                    location=[lat, lon],
                    zoom_start=13,
                    tiles="CartoDB dark_matter",
                    attr=' '
                )
                
                # Add selected places to map
                selected_places_to_map = [
                    p
                    for d in trip["days"]
                    for p in d["places"]
                    if p.get("selected", False)
                ]
                has_fresh_map_status = any("map_status" in p for p in selected_places_to_map)
                places_with_location = [
                    p
                    for p in selected_places_to_map
                    if is_valid_coordinates(p.get("lat"), p.get("lon"))
                ]

                if not has_fresh_map_status and selected_places_to_map:
                    st.info("Map pins need a refresh for best accuracy. Generate the itinerary again to update them.")

                for p in places_with_location:
                    cat = p.get("category", "attraction").lower()
                    color = COLORS.get(cat, "#00f3ff")
                    status = "Verified by geocoder" if p.get("map_status") == "exact" else "From itinerary coordinates"

                    folium.Marker(
                        [p["lat"], p["lon"]],
                        popup=folium.Popup(f"""
                            <div style="font-family: sans-serif; min-width: 150px;">
                                <h4 style="margin: 0 0 5px 0; color: {color};">{p['name']}</h4>
                                <p style="margin: 0; color: #666; font-size: 0.9rem;">{cat.title()}</p>
                                <p style="margin: 4px 0 0 0; color: #888; font-size: 0.75rem;">{status}</p>
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
                
                skipped_count = len(selected_places_to_map) - len(places_with_location)
                exact_count = len([p for p in places_with_location if p.get("map_status") == "exact"])
                if skipped_count:
                    st.caption(f"📍 {len(places_with_location)} places mapped · {exact_count} geocoder-verified · {skipped_count} missing coordinates")
                else:
                    st.caption(f"📍 {len(places_with_location)} places mapped · {exact_count} geocoder-verified")
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
