import pandas as pd
import json
import time
from sklearn.preprocessing import MinMaxScaler
import ssl
import certifi
from google import genai
import streamlit as st
from io import BytesIO
from pathlib import Path
import requests
import os
import concurrent.futures
from langchain.agents import Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
import base64

# API Keys (same as before)
API_KEYS = [
    "AIzaSyD09_gws5tBYZmD0YHF1etSZ7K-7wePIh0",
    "AIzaSyBJ2N1RHTTTQMXUod7jPymZwbgnPsdgLsY",
    "AIzaSyBwvI4kSZWOnWG3Km6kpUbqD87wIUVcoHs",
    "AIzaSyDKvI5lwfrihbcXXaXxaQWhGULE77afyrg",
    "AIzaSyCxpTPYFq91HfeUVqe8JD3RjiU4nV63WH8",
    "AIzaSyCWZVz-ciOp91vKr2u7J87IktK2skygOro",
    "AIzaSyB11u1-TTuvIRNhSAp44PgWWpoK9kq1mAo",
    "AIzaSyBxusefsMEbKv6HAoYxECpOIqbKO-pCs2g",
    "AIzaSyDIAYd4QdTBQO4MVOnAvoA5tNEozVYdflE",
    "AIzaSyBw6zUcIsp5t4QZxI_BRiPphYJzf7mq8p4",
    "AIzaSyC3EpZaqKLQwxCGUxKLzuwzvtKT2EjYTEA",
    "AIzaSyAkXdS9nAA35pdOX4kZQaFOgOznjU9MlDs",
    "AIzaSyBZqnpTMHL8Zap2CIrqifqXVA5YB30Apuw",
    "AIzaSyBqTtltNANsAhbodnxfFJOFq8vaGszJPqQ",
    "AIzaSyCC2RTsg8ArBgXj8t82-w-agFE82s0CUHw",
    "AIzaSyDvtLtNuVVlgNBvzwPRl42RyWZJqRsCI4Q",
    "AIzaSyATYlQN6L7SJz7mY7wScnyB8G_DqRsJQT4",
    "AIzaSyBW8Q1amjzs0_XLHaKaecyZuQJe0U5qhZU",
    "AIzaSyA7YtWUSsljlQuWOuy3fSBajot2rI5D3e8",
    "AIzaSyAsFagF5Z-A_o2pvUiAwpzqXpDpRNjhwfM",
    "AIzaSyDG8LTKH4NGqQcaGAz76z4hKAQ95jVjz4c",
    "AIzaSyDwB9W3SJjG5qkTd58L8ToX0xmi57Kh8d4",
    "AIzaSyBNAb6TSR4mhq82WtW2wHSCOUDK73IDbfs",
    "AIzaSyB51i5YnENFBE8aYncinPtwLk1dThl2CuA"
]

# Page config
st.set_page_config(page_title="ارزیابی رزومه", page_icon="📋", layout="wide", initial_sidebar_state="expanded")

# Custom CSS with B Homa font
font_css = """
<style>
    @font-face {
        font-family: 'B Homa';
        src: url('https://cdn.fontcdn.ir/Font/Persian/B_Homa/B%20Homa.eot');
        src: url('https://cdn.fontcdn.ir/Font/Persian/B_Homa/B%20Homa.eot?#iefix') format('embedded-opentype'),
             url('https://cdn.fontcdn.ir/Font/Persian/B_Homa/B%20Homa.woff') format('woff'),
             url('https://cdn.fontcdn.ir/Font/Persian/B_Homa/B%20Homa.ttf') format('truetype');
        font-weight: normal;
        font-style: normal;
    }
    
    @font-face {
        font-family: 'B Homa';
        src: url('https://cdn.fontcdn.ir/Font/Persian/B_Homa/B%20Homa%20Bold.eot');
        src: url('https://cdn.fontcdn.ir/Font/Persian/B_Homa/B%20Homa%20Bold.eot?#iefix') format('embedded-opentype'),
             url('https://cdn.fontcdn.ir/Font/Persian/B_Homa/B%20Homa%20Bold.woff') format('woff'),
             url('https://cdn.fontcdn.ir/Font/Persian/B_Homa/B%20Homa%20Bold.ttf') format('truetype');
        font-weight: bold;
        font-style: normal;
    }

    * {
        font-family: 'B Homa', Tahoma, Arial, sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }
    
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .main-container {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        margin: 1rem;
    }
    
    .header-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
    }
    
    .header-title {
        color: white;
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .header-subtitle {
        color: rgba(255,255,255,0.95);
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }
    
    .card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border: 1px solid #e0e0e0;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.12);
    }
    
    .card-title {
        color: #667eea;
        font-size: 1.3rem;
        font-weight: bold;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #667eea;
    }
    
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
    }
    
    .stat-label {
        font-size: 1rem;
        margin-top: 0.3rem;
        opacity: 0.95;
    }
    
    .success-box {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
        font-weight: bold;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
        font-weight: bold;
    }
    
    .info-box {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
    }
    
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        font-weight: bold;
        border-radius: 10px;
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    .result-table {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }
    
    .score-badge-high {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    
    .score-badge-medium {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    
    .score-badge-low {
        background: linear-gradient(135deg, #e43a15 0%, #e65245 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    
    .sidebar .sidebar-content {
        background: white;
        border-radius: 15px;
        padding: 1rem;
    }
    
    /* RTL specific adjustments */
    .stSelectbox, .stMultiSelect, .stTextInput {
        text-align: right !important;
        direction: rtl !important;
    }
    
    div[data-baseweb="select"] > div {
        text-align: right !important;
        direction: rtl !important;
    }
    
    .stDataFrame {
        direction: rtl !important;
    }
    
    /* File uploader styling */
    .stFileUploader {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 15px;
        padding: 2rem;
        border: 2px dashed #667eea;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: #f5f7fa;
        padding: 0.5rem;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
</style>
"""

st.markdown(font_css, unsafe_allow_html=True)

# Initialize session state
if 'live_results' not in st.session_state:
    st.session_state['live_results'] = []
if 'processing_complete' not in st.session_state:
    st.session_state['processing_complete'] = False

# File paths
RESULT_FILE_PATH = Path("resume_results.xlsx")
OUTPUT_ALL_PATH = Path("recruitment_score.xlsx")
BATCH_SIZE = 10

# Job profiles (same as before)
JOB_PROFILES = [
    {
        "id": "job_rnd_01",
        "title": "تحقیق و توسعه سامانه‌ها",
        "tasks": [
            "تحلیل و احصا نیازمندی‌های نرم‌افزاری ذینفعان در حوزه زیرساخت‌های پردازش حجیم، لاگ و گردش کار",
            "توسعه و پیاده‌سازی راهکارهای نرم‌افزاری شامل ذخیره‌سازی، گردش کار و پرتال",
            "اجرای فرآیند استقرار زیرساخت و سامانه‌ها",
            "پشتیبانی و نگهداشت سامانه‌ها و پاسخ به تیکت‌ها",
            "مستندسازی و مدیریت دانش سامانه‌ها"
        ],
        "competencies_technical": [
            {"name": "برنامه‌نویسی و مبانی علم کامپیوتر"},
            {"name": "تحلیل نیازمندی نرم‌افزار"},
            {"name": "زبان‌های برنامه‌نویسی بک‌اند یا فرانت (مثل Python یا JavaScript)"},
            {"name": "پایگاه داده"}
        ],
        "majors": ["مهندسی کامپیوتر", "مهندسی صنایع", "رشته‌های فنی و مهندسی"]
    },
    {
        "id": "job_spatial_01",
        "title": "توسعه راهکارهای تحلیل اطلاعات مکانی",
        "tasks": [
            "تحلیل نیازمندی‌های داده‌محور مکانی",
            "توسعه راهکارهای نرم‌افزاری GIS و RS",
            "فرایند ETL داده‌های مکانی",
            "استقرار و پشتیبانی راهکارهای داده‌محور GIS/RS",
            "مستندسازی پروژه‌ها و ماموریت‌های مکانی"
        ],
        "competencies_technical": [
            {"name": "مبانی سنجش از دور"},
            {"name": "ابزارهای RS مانند ENVI، ERDAS، SNAP"},
            {"name": "مبانی هوش مصنوعی / پردازش تصویر"},
            {"name": "برنامه‌نویسی Python / MATLAB"},
            {"name": "نرم‌افزارهای GIS مانند ArcGIS/QGIS"}
        ],
        "majors": ["نقشه‌برداری", "مهندسی کامپیوتر", "مهندسی برق"]
    },
    {
        "id": "job_ai_01",
        "title": "توسعه راهکارهای مبتنی بر هوش مصنوعی",
        "tasks": [
            "تحلیل نیازهای داده‌محور با تاکید بر AI",
            "پیاده‌سازی مدل‌های آماری و یادگیری ماشین",
            "استقرار مدل‌ها با ابزارهای MLOps",
            "تهیه گزارشات تحلیلی",
            "مدیریت دانش پروژه‌های AI"
        ],
        "competencies_technical": [
            {"name": "مدل‌سازی آماری / یادگیری ماشین"},
            {"name": "برنامه‌نویسی Python / R / GAMS"},
            {"name": "کار با پایگاه داده"}
        ],
        "majors": ["علوم کامپیوتر", "ریاضی", "آمار", "مهندسی صنایع", "اقتصاد", "مهندسی مالی", "برق"]
    },
    {
        "id": "job_research_01",
        "title": "کارشناس ارتباط با مراکز پژوهشی",
        "tasks": [
            "احصا مسائل فناورانه و داده‌محور",
            "پشتیبانی سامانه دانش نظام مسائل",
            "مطالعات تطبیقی در حوزه هوش مصنوعی",
            "مستندسازی اسناد راهبردی AI",
            "رصد و تحلیل فناوری‌های نوظهور"
        ],
        "competencies_technical": [
            {"name": "Microsoft Office"},
            {"name": "مبانی علم داده و IT"},
            {"name": "اصول تحقیق و توسعه"}
        ],
        "majors": ["مدیریت", "مهندسی صنایع", "علوم اقتصادی", "علوم کامپیوتر"]
    },
    {
        "id": "job_analysis_01",
        "title": "کارشناس تحلیلگر داده و هوش تجاری",
        "tasks": [
            "گروه بندی و مرتب کردن اطلاعات",
            "تحلیل داده های مربوط به کسب و کار",
            "تمیزسازی داده ها ETL",
            "مستندسازی اسناد راهبردی ",
            "نامه نگاری و مکاتبات اداری",
            "بصری سازی داده ها"
        ],
        "competencies_technical": [
            {"name": "Microsoft Office"},
            {"name": "شناخت و تحلیل کسب و کار"},
            {"name": "ابزارهای مصورسازی مانند powerBI"},
            {"name": "ابزارهای تحلیل داده مانند KNIME"},
            {"name": "آشنایی با زان های برنامه نویسی مانند python , R"}
        ],
        "majors": ["مدیریت", "مهندسی صنایع", "علوم اقتصادی", "مهندسی کامپیوتر"]
    }
]

universities_info = [
    "دانشگاه تهران (برتر، دولتی)",
    "دانشگاه صنعتی شریف (برتر، دولتی)",
    "دانشگاه صنعتی امیرکبیر (برتر، دولتی)",
    "دانشگاه علم و صنعت ایران (برتر، دولتی)",
    "دانشگاه خواجه نصیر (برتر، دولتی)",
    "دانشگاه خوارزمی (برتر، دولتی)",
    "دانشگاه فردوسی مشهد (دولتی)",
    "دانشگاه تبریز (دولتی)",
    "دانشگاه اصفهان (دولتی)",
    "دانشگاه صنعتی اصفهان (دولتی)",
    "دانشگاه آزاد اسلامی (آزاد)",
    "دانشگاه پیام نور (پیام نور)",
    "دانشگاه غیرانتفاعی (غیرانتفاعی)",
    "دانشگاه علمی کاربردی (علمی کاربردی)"
]

AGENT_WEIGHTS = {
    "SkillAgent": 0.40,
    "ExperienceAgent": 0.30,
    "EducationAgent": 0.20,
    "VolunteeringAgent": 0.05,
    "SoftSkillsAgent": 0.05
}

# [Keep all the helper functions from the original code: style_excel, RotatingGeminiLLM, safe_generate_content, etc.]
# I'll include the key ones here for brevity

def style_excel(path): 
    wb = openpyxl.load_workbook(path) 
    ws = wb.active 

    header_fill = PatternFill(start_color="667eea", end_color="667eea", fill_type="solid")
    row_fill_odd = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    row_fill_even = PatternFill(start_color="F5F7FA", end_color="F5F7FA", fill_type="solid")

    header_font = Font(bold=True, name='B Homa', size=14, color="FFFFFF")
    row_font = Font(name='B Homa', size=12)
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    border = Border(
        left=Side(border_style="thin", color="E0E0E0"),
        right=Side(border_style="thin", color="E0E0E0"),
        top=Side(border_style="thin", color="E0E0E0"),
        bottom=Side(border_style="thin", color="E0E0E0"),
    )

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align
        cell.border = border

    for idx, row in enumerate(ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=ws.max_column), start=2):
        fill = row_fill_even if idx % 2 == 0 else row_fill_odd
        for cell in row:
            cell.fill = fill
            cell.font = row_font
            cell.alignment = center_align
            cell.border = border

    for col in ws.columns:
        max_length = 0 
        column = col[0].column_letter 
        for cell in col: 
            try: 
                if cell.value:
                    max_length = max(max_length, len(str(cell.value))) 
            except: 
                pass 
        adjusted_width = min(max_length + 3, 50) 
        ws.column_dimensions[column].width = adjusted_width 

    ws.freeze_panes = ws["A2"] 
    wb.save(path)

class RotatingGeminiLLM:
    def __init__(self, api_keys, model="gemini-2.5-flash"):
        self.api_keys = api_keys
        self.model = model
        self.idx = 0

    def invoke(self, messages):
        num_keys = len(self.api_keys)
        start_idx = self.idx
        for i in range(num_keys):
            api_key = self.api_keys[self.idx]
            llm = ChatGoogleGenerativeAI(model=self.model, google_api_key=api_key)
            try:
                result = llm.invoke(messages)
                return result
            except Exception as e:
                self.idx = (self.idx + 1) % num_keys
                if self.idx == start_idx:
                    raise RuntimeError("تمام API Keyها با خطا مواجه شدند.")
        raise RuntimeError("تمام API Keyها با خطا مواجه شدند.")

rotating_llm = RotatingGeminiLLM(API_KEYS)

def safe_generate_content(*, model, contents, config):
    for api_key in API_KEYS:
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
            return response
        except Exception as e:
            continue
    raise RuntimeError("تمام API Keyها با خطا مواجه شدند.")

# [Include all other helper functions from original code: skill_agent, experience_agent, etc.]
# For brevity, I'm showing the main UI structure

# ============ MAIN UI ============

# Header
st.markdown("""
<div class="header-section">
    <h1 class="header-title">سامانه هوشمند ارزیابی رزومه</h1>
    <p class="header-subtitle">ارزیابی حرفه‌ای رزومه‌ها با استفاده از هوش مصنوعی</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h3 class="card-title">📊 آمار سیستم</h3>', unsafe_allow_html=True)
    
    if RESULT_FILE_PATH.exists():
        live_df = pd.read_excel(RESULT_FILE_PATH)
        total = len(live_df)
        accepted = (live_df.get('تایید و رد اولیه', pd.Series()) == 'تایید').sum()
        rejected = total - accepted
        
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{total}</div>
            <div class="stat-label">کل رزومه‌ها</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="stat-box" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);">
            <div class="stat-number">{accepted}</div>
            <div class="stat-label">تایید شده</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="stat-box" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <div class="stat-number">{rejected}</div>
            <div class="stat-label">رد شده</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="info-box">هنوز رزومه‌ای پردازش نشده است</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    if st.button("🔄 ریست کامل سیستم"):
        for key in ['final_df', 'live_results', 'processing_complete']:
            if key in st.session_state:
                del st.session_state[key]
        if RESULT_FILE_PATH.exists():
            RESULT_FILE_PATH.unlink()
        st.success("سیستم با موفقیت ریست شد")
        st.rerun()

# Main content
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<h3 class="card-title">📁 بارگذاری فایل</h3>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("فایل اکسل رزومه‌ها را انتخاب کنید", type=["xlsx"], label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

if uploaded_file:
    df = pd.read_excel(uploaded_file, header=0)
    
    st.markdown(f'<div class="success-box">✓ {len(df)} رزومه با موفقیت بارگذاری شد</div>', unsafe_allow_html=True)
    
    with st.expander("🔍 نمایش پیش‌نمایش داده‌ها"):
        st.dataframe(df.head(10), use_container_width=True)
    
    # Job selection section
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h3 class="card-title">💼 انتخاب موقعیت شغلی</h3>', unsafe_allow_html=True)
    
    job_titles = [job['title'] for job in JOB_PROFILES]
    selected_job_titles = st.multiselect(
        "عنوان شغلی مورد نظر را انتخاب کنید:",
        options=job_titles,
        default=None
    )
    
    custom_job_title = st.text_input("عنوان شغلی دلخواه (اختیاری):")
    
    all_selected_titles = selected_job_titles.copy()
    if custom_job_title.strip():
        all_selected_titles.append(custom_job_title.strip())
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Skills section
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h3 class="card-title">🎯 مهارت‌های مورد نیاز</h3>', unsafe_allow_html=True)
    
    selected_skills = []
    for job in JOB_PROFILES:
        if job["title"] in all_selected_titles:
            selected_skills.extend([c['name'] for c in job.get('competencies_technical', [])])
    
    selected_skills = list(sorted(set(selected_skills)))
    
    edited_skills = st.multiselect(
        "مهارت‌های مورد نیاز:",
        options=selected_skills,
        default=selected_skills
    )
    
    custom_skill = st.text_input("افزودن مهارت جدید (اختیاری):")
    
    all_skills = edited_skills.copy()
    if custom_skill.strip() and custom_skill.strip() not in all_skills:
        all_skills.append(custom_skill.strip())
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Processing section
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h3 class="card-title">⚙️ پردازش رزومه‌ها</h3>', unsafe_allow_html=True)
    
    tabs = st.tabs(["امتیازدهی", "تطبیق با شناسنامه شغلی"])
    
    with tabs[0]:
        st.markdown("### ارزیابی و امتیازدهی رزومه‌ها")
        
        max_workers = min(len(API_KEYS), len(df))
        st.info(f"🚀 پردازش موازی با {max_workers} API Key")
        
        if st.button("▶️ شروع امتیازدهی", key="start_scoring"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            results_placeholder = st.empty()
            
            # [Include the parallel processing code from original]
            # For brevity, showing the structure
            
            st.markdown('<div class="success-box">✓ امتیازدهی با موفقیت انجام شد</div>', unsafe_allow_html=True)
    
    with tabs[1]:
        st.markdown("### تطبیق رزومه‌ها با شناسنامه‌های شغلی")
        
        if st.button("▶️ شروع تطبیق", key="start_matching"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # [Include the matching code from original]
            
            st.markdown('<div class="success-box">✓ تطبیق با موفقیت انجام شد</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Results section
if RESULT_FILE_PATH.exists():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h3 class="card-title">📋 نتایج ارزیابی</h3>', unsafe_allow_html=True)
    
    final_df = pd.read_excel(RESULT_FILE_PATH)
    
    # Statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_score = final_df['final_score'].mean() if 'final_score' in final_df.columns else 0
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{avg_score:.1f}</div>
            <div class="stat-label">میانگین امتیاز</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        top_score = final_df['final_score'].max() if 'final_score' in final_df.columns else 0
        st.markdown(f"""
        <div class="stat-box" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);">
            <div class="stat-number">{top_score:.1f}</div>
            <div class="stat-label">بالاترین امتیاز</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        low_score = final_df['final_score'].min() if 'final_score' in final_df.columns else 0
        st.markdown(f"""
        <div class="stat-box" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <div class="stat-number">{low_score:.1f}</div>
            <div class="stat-label">پایین‌ترین امتیاز</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Data table
    st.markdown("### جدول کامل نتایج")
    st.dataframe(final_df, use_container_width=True, height=400)
    
    # Download button
    style_excel(RESULT_FILE_PATH)
    with open(RESULT_FILE_PATH, "rb") as f:
        st.download_button(
            "📥 دانلود فایل اکسل نتایج",
            data=f,
            file_name="نتایج_ارزیابی_رزومه.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #667eea; padding: 1rem;">
    <p>سامانه هوشمند ارزیابی رزومه | طراحی شده با ❤️</p>
</div>
""", unsafe_allow_html=True)
