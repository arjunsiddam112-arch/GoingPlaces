
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

LOCK = False

# =========================
# PAGE STATE
# =========================
if "page" not in st.session_state:
    st.session_state.page = "home"

if "trip" not in st.session_state:
    st.session_state.trip = None
if "weather" not in st.session_state:
    st.session_state.weather = None
if "center" not in st.session_state:
    st.session_state.center = None
if "selected_places" not in st.session_state:
    st.session_state.selected_places = set()
if "travel_date" not in st.session_state:
    st.session_state.travel_date = datetime.date.today() + datetime.timedelta(days=7)
if "selected_weather_day" not in st.session_state:
    st.session_state.selected_weather_day = 0

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

        .weather-panel {
            padding: 28px 32px 28px 22px;
        }

        .weather-compact {
            padding: 18px 22px 18px 18px;
            border-radius: 20px;
        }

        .weather-metric {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 10px 12px;
            border: 1px solid rgba(255,255,255,0.06);
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
    if "weather" not in st.session_state:
        st.session_state.weather = None
    if "center" not in st.session_state:
        st.session_state.center = None
    if "selected_places" not in st.session_state:
        st.session_state.selected_places = set()
    if "hotels" not in st.session_state:
        st.session_state.hotels = []
    if "selected_hotel" not in st.session_state:
        st.session_state.selected_hotel = {}
    if "travel_date" not in st.session_state:
        st.session_state.travel_date = datetime.date.today() + datetime.timedelta(days=7)
    if "selected_weather_day" not in st.session_state:
        st.session_state.selected_weather_day = 0

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

    CURRENCY_RATES = {
        "INR": 1,
        "USD": 0.012,
        "EUR": 0.011,
        "GBP": 0.0095,
        "JPY": 1.8
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
    def safe_generate(prompt):
        global LOCK

        while LOCK:
            time.sleep(1)

        LOCK = True

        try:
            time.sleep(12)
            return model.generate_content(prompt)
        finally:
            LOCK = False

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

    def weather_code_details(code):
        weather_map = {
            0: ("☀️", "Clear sky"),
            1: ("🌤️", "Mainly clear"),
            2: ("⛅", "Partly cloudy"),
            3: ("☁️", "Overcast"),
            45: ("🌫️", "Fog"),
            48: ("🌫️", "Rime fog"),
            51: ("🌦️", "Light drizzle"),
            53: ("🌦️", "Moderate drizzle"),
            55: ("🌧️", "Dense drizzle"),
            56: ("🌨️", "Light freezing drizzle"),
            57: ("🌨️", "Dense freezing drizzle"),
            61: ("🌦️", "Slight rain"),
            63: ("🌧️", "Moderate rain"),
            65: ("🌧️", "Heavy rain"),
            66: ("🌨️", "Light freezing rain"),
            67: ("🌨️", "Heavy freezing rain"),
            71: ("🌨️", "Slight snow"),
            73: ("❄️", "Moderate snow"),
            75: ("❄️", "Heavy snow"),
            77: ("🌨️", "Snow grains"),
            80: ("🌦️", "Rain showers"),
            81: ("🌧️", "Rain showers"),
            82: ("⛈️", "Violent showers"),
            85: ("🌨️", "Snow showers"),
            86: ("❄️", "Heavy snow showers"),
            95: ("⛈️", "Thunderstorm"),
            96: ("⛈️", "Thunderstorm with hail"),
            99: ("⛈️", "Severe thunderstorm with hail")
        }
        try:
            normalized_code = int(code)
        except (TypeError, ValueError):
            normalized_code = -1
        return weather_map.get(normalized_code, ("🌤️", "Variable weather"))

    def format_metric(value, suffix="", decimals=0):
        if value is None:
            return "N/A"
        try:
            return f"{float(value):.{decimals}f}{suffix}"
        except (TypeError, ValueError):
            return "N/A"

    def format_date_label(date_str, fmt="%a, %d %b"):
        try:
            return datetime.date.fromisoformat(date_str).strftime(fmt)
        except (TypeError, ValueError):
            return date_str or "Unknown"

    def format_time_label(timestamp):
        try:
            return datetime.datetime.fromisoformat(timestamp).strftime("%I:%M %p").lstrip("0")
        except (TypeError, ValueError):
            return "N/A"

    def build_weather_tip(day_data):
        rain_probability = day_data.get("precipitation_probability", 0) or 0
        rainfall = day_data.get("precipitation_total", 0) or 0
        max_temp = day_data.get("temp_max")
        min_temp = day_data.get("temp_min")
        wind_speed = day_data.get("wind_speed")

        if rain_probability >= 60 or rainfall >= 5:
            return "Carry an umbrella and keep indoor options handy for this day."
        if max_temp is not None and max_temp >= 32:
            return "Plan outdoor sightseeing early or late and stay hydrated during the afternoon."
        if min_temp is not None and min_temp <= 10:
            return "Pack a jacket for cooler morning and evening hours."
        if wind_speed is not None and wind_speed >= 28:
            return "Expect breezy conditions, especially around open viewpoints and waterfronts."
        return "Comfortable sightseeing weather overall with good flexibility for outdoor plans."

    def build_hourly_preview(hourly_data, date_str):
        preview = []
        times = hourly_data.get("time", [])
        temperatures = hourly_data.get("temperature_2m", [])
        rain_probabilities = hourly_data.get("precipitation_probability", [])
        weather_codes = hourly_data.get("weather_code", [])
        preferred_hours = {6, 9, 12, 15, 18, 21}

        for idx, time_str in enumerate(times):
            if not str(time_str).startswith(date_str):
                continue

            try:
                hour_dt = datetime.datetime.fromisoformat(time_str)
            except ValueError:
                continue

            if hour_dt.hour not in preferred_hours:
                continue

            icon, description = weather_code_details(weather_codes[idx] if idx < len(weather_codes) else None)
            preview.append({
                "time": hour_dt.strftime("%I %p").lstrip("0"),
                "temperature": temperatures[idx] if idx < len(temperatures) else None,
                "precipitation_probability": rain_probabilities[idx] if idx < len(rain_probabilities) else None,
                "description": description,
                "icon": icon
            })

        if preview:
            return preview[:6]

        fallback_preview = []
        fallback_counter = 0
        for idx, time_str in enumerate(times):
            if not str(time_str).startswith(date_str):
                continue
            fallback_counter += 1
            if fallback_counter % 4 != 1:
                continue
            try:
                hour_dt = datetime.datetime.fromisoformat(time_str)
            except ValueError:
                continue
            icon, description = weather_code_details(weather_codes[idx] if idx < len(weather_codes) else None)
            fallback_preview.append({
                "time": hour_dt.strftime("%I %p").lstrip("0"),
                "temperature": temperatures[idx] if idx < len(temperatures) else None,
                "precipitation_probability": rain_probabilities[idx] if idx < len(rain_probabilities) else None,
                "description": description,
                "icon": icon
            })
            if len(fallback_preview) >= 6:
                break

        return fallback_preview[:6]

    def get_weather(city, trip_date=None):
        city = sanitize_input(city, 100)
        if not city:
            return None

        try:
            lat, lon = get_location(city)
            if not is_valid_coordinates(lat, lon):
                known_center = known_destination_center(city)
                if known_center:
                    lat, lon = known_center
                else:
                    return None

            params = {
                "latitude": float(lat),
                "longitude": float(lon),
                "current": ",".join([
                    "temperature_2m",
                    "apparent_temperature",
                    "relative_humidity_2m",
                    "wind_speed_10m",
                    "weather_code"
                ]),
                "daily": ",".join([
                    "weather_code",
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "apparent_temperature_max",
                    "apparent_temperature_min",
                    "precipitation_probability_max",
                    "precipitation_sum",
                    "wind_speed_10m_max",
                    "sunrise",
                    "sunset"
                ]),
                "hourly": ",".join([
                    "temperature_2m",
                    "precipitation_probability",
                    "weather_code"
                ]),
                "forecast_days": 7,
                "timezone": "auto",
                "temperature_unit": "celsius",
                "wind_speed_unit": "kmh",
                "precipitation_unit": "mm"
            }

            response = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            current = data.get("current", {})
            daily = data.get("daily", {})
            hourly = data.get("hourly", {})
            dates = daily.get("time", [])[:7]
            forecast_days = []

            for idx, date_str in enumerate(dates):
                code = (daily.get("weather_code") or [None] * len(dates))[idx]
                icon, description = weather_code_details(code)
                day_data = {
                    "date": date_str,
                    "label": format_date_label(date_str, "%a, %d %b"),
                    "short_label": format_date_label(date_str, "%d %b"),
                    "day_name": format_date_label(date_str, "%a"),
                    "description": description,
                    "icon": icon,
                    "temp_max": (daily.get("temperature_2m_max") or [None] * len(dates))[idx],
                    "temp_min": (daily.get("temperature_2m_min") or [None] * len(dates))[idx],
                    "feels_like_max": (daily.get("apparent_temperature_max") or [None] * len(dates))[idx],
                    "feels_like_min": (daily.get("apparent_temperature_min") or [None] * len(dates))[idx],
                    "precipitation_probability": (daily.get("precipitation_probability_max") or [None] * len(dates))[idx],
                    "precipitation_total": (daily.get("precipitation_sum") or [None] * len(dates))[idx],
                    "wind_speed": (daily.get("wind_speed_10m_max") or [None] * len(dates))[idx],
                    "sunrise": format_time_label((daily.get("sunrise") or [None] * len(dates))[idx]),
                    "sunset": format_time_label((daily.get("sunset") or [None] * len(dates))[idx]),
                    "hourly_preview": build_hourly_preview(hourly, date_str)
                }
                day_data["tip"] = build_weather_tip(day_data)
                forecast_days.append(day_data)

            if not forecast_days:
                return None

            current_icon, current_description = weather_code_details(current.get("weather_code"))
            selected_index = 0
            travel_date_in_range = False
            serialized_trip_date = None

            if isinstance(trip_date, datetime.date):
                serialized_trip_date = trip_date.isoformat()
                for idx, day_data in enumerate(forecast_days):
                    if day_data["date"] == serialized_trip_date:
                        selected_index = idx
                        travel_date_in_range = True
                        break

            return {
                "city": city.title(),
                "latitude": float(lat),
                "longitude": float(lon),
                "current": {
                    "temperature": current.get("temperature_2m"),
                    "feels_like": current.get("apparent_temperature"),
                    "humidity": current.get("relative_humidity_2m"),
                    "wind_speed": current.get("wind_speed_10m"),
                    "description": current_description,
                    "icon": current_icon,
                    "time": current.get("time")
                },
                "daily": forecast_days,
                "selected_index": selected_index,
                "travel_date": serialized_trip_date,
                "travel_date_in_range": travel_date_in_range,
                "forecast_window": f"{forecast_days[0]['label']} - {forecast_days[-1]['label']}",
                "fetched_at": datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")
            }
        except Exception as e:
            logger.error(f"Weather forecast error: {str(e)}")
            return None

    def render_weather_card(weather_data):
        if not weather_data:
            st.error("Unable to fetch the 7-day weather forecast for this destination right now.")
            return

        current_weather = weather_data.get("current", {})
        forecast_days = weather_data.get("daily", [])
        if not forecast_days:
            st.error("Weather data is unavailable for the selected destination.")
            return

        selected_index = st.session_state.get("selected_weather_day", weather_data.get("selected_index", 0))
        if selected_index >= len(forecast_days):
            selected_index = 0
            st.session_state.selected_weather_day = 0
        selected_day = forecast_days[selected_index]

        header_col, action_col = st.columns([6, 1])
        with header_col:
            st.markdown(
                f"""
                <div class="glass-panel weather-compact">
                    <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap;">
                        <div>
                            <p style="margin: 0; color: rgba(255,255,255,0.58); text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.72rem; font-weight: 700;">Weather Snapshot</p>
                            <h3 style="margin: 4px 0 0 0; font-size: 1.15rem;">{current_weather.get('icon', '🌤️')} {weather_data['city']}</h3>
                            <p style="margin: 4px 0 0 0; color: rgba(255,255,255,0.68); font-size: 0.88rem;">{weather_data.get('forecast_window', 'Next 7 days')}</p>
                        </div>
                        <div style="text-align: right;">
                            <div style="color: #00f3ff; font-size: 1.7rem; font-weight: 700; text-shadow: 0 0 14px rgba(0, 243, 255, 0.35); line-height: 1;">
                                {format_metric(current_weather.get("temperature"), "°C")}
                            </div>
                            <p style="margin: 4px 0 0 0; color: rgba(255,255,255,0.74); font-size: 0.84rem;">{current_weather.get("description", "Current conditions")}</p>
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 10px; margin-top: 14px;">
                        <div class="weather-metric">
                            <p style="margin: 0; color: rgba(255,255,255,0.52); font-size: 0.72rem;">Feels Like</p>
                            <p style="margin: 4px 0 0 0; color: #fff; font-weight: 600; font-size: 0.92rem;">{format_metric(current_weather.get("feels_like"), "°C")}</p>
                        </div>
                        <div class="weather-metric">
                            <p style="margin: 0; color: rgba(255,255,255,0.52); font-size: 0.72rem;">Humidity</p>
                            <p style="margin: 4px 0 0 0; color: #fff; font-weight: 600; font-size: 0.92rem;">{format_metric(current_weather.get("humidity"), "%")}</p>
                        </div>
                        <div class="weather-metric">
                            <p style="margin: 0; color: rgba(255,255,255,0.52); font-size: 0.72rem;">Wind</p>
                            <p style="margin: 4px 0 0 0; color: #fff; font-weight: 600; font-size: 0.92rem;">{format_metric(current_weather.get("wind_speed"), " km/h")}</p>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with action_col:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            if st.button("🔄 Refresh", key="refresh_weather", use_container_width=True):
                refreshed_weather = get_weather(
                    st.session_state.get("destination", weather_data["city"]),
                    st.session_state.get("travel_date")
                )
                if refreshed_weather:
                    st.session_state.weather = refreshed_weather
                    st.session_state.selected_weather_day = refreshed_weather.get("selected_index", 0)
                    st.rerun()
                st.warning("Unable to refresh forecast right now. Please try again in a moment.")

        trip_date = weather_data.get("travel_date")
        if trip_date and weather_data.get("travel_date_in_range"):
            st.caption(f"Trip date {format_date_label(trip_date, '%d %b %Y')} is included in this forecast.")
        elif trip_date:
            st.caption(
                f"Trip date {format_date_label(trip_date, '%d %b %Y')} is outside the current 7-day window."
            )

        with st.expander("View detailed forecast", expanded=False):
            day_options = list(range(len(forecast_days)))
            st.radio(
                "Choose a forecast day",
                options=day_options,
                index=selected_index,
                horizontal=True,
                key="selected_weather_day",
                format_func=lambda idx: (
                    f"{forecast_days[idx]['day_name']} {forecast_days[idx]['short_label']} "
                    f"{forecast_days[idx]['icon']} {format_metric(forecast_days[idx]['temp_max'], '°')}/"
                    f"{format_metric(forecast_days[idx]['temp_min'], '°')}"
                )
            )
            selected_day = forecast_days[st.session_state.get("selected_weather_day", 0)]

            st.markdown(
                f"""
                <div class="glass-panel weather-panel">
                    <div style="display: flex; justify-content: space-between; gap: 14px; align-items: center; flex-wrap: wrap;">
                        <div>
                            <p style="margin: 0; color: rgba(255,255,255,0.58); text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.72rem; font-weight: 700;">Selected Forecast</p>
                            <h3 style="margin: 6px 0 0 0;">{selected_day['icon']} {selected_day['label']}</h3>
                            <p style="margin: 6px 0 0 0; color: rgba(255,255,255,0.72); font-size: 0.9rem;">{selected_day['description']}</p>
                        </div>
                        <div style="text-align: right;">
                            <div style="color: #fff; font-size: 1.15rem; font-weight: 700;">
                                {format_metric(selected_day.get("temp_max"), "°C")} / {format_metric(selected_day.get("temp_min"), "°C")}
                            </div>
                            <p style="margin: 6px 0 0 0; color: rgba(255,255,255,0.68); font-size: 0.84rem;">High / Low</p>
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; margin-top: 16px;">
                        <div class="weather-metric">
                            <p style="margin: 0; color: rgba(255,255,255,0.55); font-size: 0.75rem;">Feels Like</p>
                            <p style="margin: 4px 0 0 0; color: #fff; font-weight: 600; font-size: 0.9rem;">{format_metric(selected_day.get("feels_like_min"), "°C")} to {format_metric(selected_day.get("feels_like_max"), "°C")}</p>
                        </div>
                        <div class="weather-metric">
                            <p style="margin: 0; color: rgba(255,255,255,0.55); font-size: 0.75rem;">Rain Chance</p>
                            <p style="margin: 4px 0 0 0; color: #fff; font-weight: 600; font-size: 0.9rem;">{format_metric(selected_day.get("precipitation_probability"), "%")}</p>
                        </div>
                        <div class="weather-metric">
                            <p style="margin: 0; color: rgba(255,255,255,0.55); font-size: 0.75rem;">Rainfall</p>
                            <p style="margin: 4px 0 0 0; color: #fff; font-weight: 600; font-size: 0.9rem;">{format_metric(selected_day.get("precipitation_total"), " mm", 1)}</p>
                        </div>
                        <div class="weather-metric">
                            <p style="margin: 0; color: rgba(255,255,255,0.55); font-size: 0.75rem;">Max Wind</p>
                            <p style="margin: 4px 0 0 0; color: #fff; font-weight: 600; font-size: 0.9rem;">{format_metric(selected_day.get("wind_speed"), " km/h")}</p>
                        </div>
                        <div class="weather-metric">
                            <p style="margin: 0; color: rgba(255,255,255,0.55); font-size: 0.75rem;">Sunrise</p>
                            <p style="margin: 4px 0 0 0; color: #fff; font-weight: 600; font-size: 0.9rem;">{selected_day.get("sunrise", "N/A")}</p>
                        </div>
                        <div class="weather-metric">
                            <p style="margin: 0; color: rgba(255,255,255,0.55); font-size: 0.75rem;">Sunset</p>
                            <p style="margin: 4px 0 0 0; color: #fff; font-weight: 600; font-size: 0.9rem;">{selected_day.get("sunset", "N/A")}</p>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown("**Day Planner Tip**")
            st.caption(selected_day.get("tip", "Weather guidance is unavailable for this day."))

            hourly_preview = selected_day.get("hourly_preview", [])
            if hourly_preview:
                st.markdown("**Hourly Snapshot**")
                hour_cols = st.columns(len(hourly_preview))
                for col, hour in zip(hour_cols, hourly_preview):
                    with col:
                        st.markdown(
                            f"""
                            <div style="background: rgba(255,255,255,0.06); border-radius: 14px; padding: 10px; text-align: center; border: 1px solid rgba(255,255,255,0.08); min-height: 132px;">
                                <p style="margin: 0; color: rgba(255,255,255,0.65); font-size: 0.78rem;">{hour['time']}</p>
                                <div style="font-size: 1.45rem; margin: 6px 0;">{hour['icon']}</div>
                                <p style="margin: 0; color: #fff; font-weight: 700; font-size: 0.95rem;">{format_metric(hour.get('temperature'), '°C')}</p>
                                <p style="margin: 4px 0 0 0; color: rgba(255,255,255,0.72); font-size: 0.76rem;">{hour['description']}</p>
                                <p style="margin: 4px 0 0 0; color: rgba(255,255,255,0.65); font-size: 0.74rem;">Rain {format_metric(hour.get('precipitation_probability'), '%')}</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

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
- Each place must include "price": numeric INR estimate per person
- Each place must include "rating": numeric value from 0 to 5
- Include 5 hotel recommendations in the hotels array
- Hotel prices must be numeric INR values per night
- Hotel ratings must be numeric values out of 5
- Only return JSON
- No explanation
- No markdown

Format:
{{"days":[{{"day":1,"places":[{{"name":"Place Name","category":"attraction","description":"Short description","address":"Location","lat":35.0,"lon":139.0,"price":500,"rating":4.3}}]}}],"hotels":[{{"name":"Hotel Name","price":3000,"rating":4.2}}]}}

Trip details:
People: {people}
Budget: {budget}
Interest: {interest}"""
            response = safe_generate(prompt)
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

    def convert_currency(amount, rate):
        try:
            return float(amount) * rate
        except (TypeError, ValueError):
            return 0

    def convert_to_inr(amount, rate):
        try:
            return float(amount) / rate
        except (TypeError, ValueError, ZeroDivisionError):
            return 0

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
        st.markdown('<p class="input-label">Budget</p>', unsafe_allow_html=True)
        budget_col, currency_col = st.columns([2, 1])
        with budget_col:
            budget = st.number_input("", 5000, 10000000, 50000, step=5000, label_visibility="collapsed")
        with currency_col:
            budget_currency = st.selectbox(
                "Currency",
                ["INR", "USD", "EUR", "GBP", "JPY"],
                key="budget_currency",
                label_visibility="collapsed"
            )

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
        travel_date = st.date_input(
            "",
            st.session_state.get("travel_date", datetime.date.today() + datetime.timedelta(days=7)),
            label_visibility="collapsed"
        )

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
                if not is_valid_coordinates(lat, lon):
                    logger.warning(f"Destination geocode failed for {dest}")
                    known_center = known_destination_center(dest)
                    if known_center:
                        lat, lon = known_center
                    else:
                        lat = lon = None
                
                budget_in_inr = convert_to_inr(budget, CURRENCY_RATES[budget_currency])
                raw = generate_plan(dest, days, people, budget_in_inr, interest)
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
                        try:
                            p["price"] = float(p.get("price", random.randint(200, 1500)))
                        except (TypeError, ValueError):
                            p["price"] = float(random.randint(200, 1500))
                        try:
                            p["rating"] = float(p.get("rating", round(random.uniform(3.5, 4.8), 1)))
                        except (TypeError, ValueError):
                            p["rating"] = float(round(random.uniform(3.5, 4.8), 1))

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
                st.session_state.travel_date = travel_date
                st.session_state.weather = get_weather(dest, travel_date)
                st.session_state.selected_weather_day = (
                    st.session_state.weather.get("selected_index", 0)
                    if st.session_state.weather else 0
                )
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

        selected_currency = budget_currency
        rate = CURRENCY_RATES[selected_currency]
        converted_budget = budget
        
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
                    <div class="metric-value">{converted_budget/1000:.0f}k</div>
                    <div class="metric-label">Budget ({selected_currency})</div>
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
        render_weather_card(st.session_state.get("weather"))
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
                            converted_price = convert_currency(p.get("price", 0), rate)
                            place_rating = p.get("rating", 0)
                            
                            st.markdown(f"""
                                <div class="{card_class}" onclick="togglePlace('{place_id}')" id="card-{place_id}">
                                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                        <div style="flex: 1;">
                                            <span class="place-category-badge {cat_class}">{CATEGORY_ICONS.get(cat, '📍')} {cat.title()}</span>
                                            <h4 style="margin: 8px 0 4px 0; color: #fff; font-size: 1.1rem; font-weight: 600;">{p['name']}</h4>
                                            <p style="margin: 0; color: rgba(255,255,255,0.7); font-size: 0.9rem; line-height: 1.4;">{p['description'][:80]}...</p>
                                            <p style="margin: 8px 0 0 0; color: rgba(255,255,255,0.82); font-size: 0.85rem;">💰 {converted_price:.0f} {selected_currency}</p>
                                            <p style="margin: 4px 0 0 0; color: rgba(255,255,255,0.72); font-size: 0.85rem;">⭐ {place_rating} / 5</p>
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
                        h["price_converted"] = convert_currency(h.get("price", 0), rate)
                        st.markdown(f"""
                            <div style="background: rgba(255,255,255,0.05); border-radius: 12px; padding: 16px; margin: 8px 0; border-left: 3px solid #00f3ff;">
                                <h4 style="margin: 0 0 8px 0; color: #fff;">{h['name']}</h4>
                                <p style="margin: 0 0 4px 0; color: rgba(255,255,255,0.8);">💰 {h["price_converted"]:.0f} {selected_currency}</p>
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
                            converted_price = convert_currency(p.get("price", 0), rate)
                            place_rating = p.get("rating", 0)
                            st.markdown(f"""
                                <div style="background: rgba(255,255,255,0.05); border-radius: 12px; padding: 12px; margin: 8px 0; border-left: 3px solid {COLORS.get(cat, '#00f3ff')};">
                                    <p style="margin: 0; color: #fff; font-weight: 500; font-size: 0.9rem;">{CATEGORY_ICONS.get(cat, '📍')} {p['name']}</p>
                                    <p style="margin: 4px 0 0 0; color: rgba(255,255,255,0.5); font-size: 0.75rem; text-transform: uppercase;">{cat}</p>
                                    <p style="margin: 8px 0 0 0; color: rgba(255,255,255,0.8); font-size: 0.82rem;">💰 {converted_price:.0f} {selected_currency}</p>
                                    <p style="margin: 4px 0 0 0; color: rgba(255,255,255,0.65); font-size: 0.82rem;">⭐ {place_rating} / 5</p>
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
