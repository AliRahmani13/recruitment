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
# Page Configuration
st.set_page_config(
    page_title="سامانه هوشمند ارزیابی رزومه",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Beautiful UI
def load_css():
    css = """
    <style>
    /* Import Google Font for Persian */
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap');
    
    /* Main Theme Colors */
    :root {
        --primary-color: #6C63FF;
        --secondary-color: #FF6B6B;
        --success-color: #4ECDC4;
        --warning-color: #FFD93D;
        --info-color: #74C0FC;
        --dark-bg: #1A1B3A;
        --light-bg: #F7F9FC;
        --card-bg: #FFFFFF;
        --text-dark: #2D3436;
        --text-light: #636E72;
    }
    
    /* Global Font and Direction */
    * {
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
        direction: rtl !important;
    }
    
    /* Main App Background */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    /* Header Styling */
    .main-header {
        background: linear-gradient(135deg, #6C63FF 0%, #8B7FFF 100%);
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .main-title {
        font-size: 3.5rem;
        font-weight: 700;
        color: white;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .main-subtitle {
        font-size: 1.2rem;
        color: rgba(255,255,255,0.9);
        font-weight: 300;
    }
    
    /* Card Styles */
    .custom-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 5px 20px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .custom-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
    }
    
    .card-header {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 0.8rem;
        border-bottom: 2px solid #f0f0f0;
    }
    
    .card-icon {
        font-size: 1.5rem;
        margin-left: 0.8rem;
    }
    
    .card-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: var(--text-dark);
    }
    
    /* Stats Cards */
    .stats-card {
        background: linear-gradient(135deg, var(--primary-color) 0%, #8B7FFF 100%);
        border-radius: 15px;
        padding: 1.5rem;
        color: white;
        text-align: center;
        box-shadow: 0 5px 20px rgba(108, 99, 255, 0.3);
        transition: transform 0.3s ease;
    }
    
    .stats-card:hover {
        transform: scale(1.05);
    }
    
    .stats-number {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .stats-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    
    /* Button Styles */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-color) 0%, #8B7FFF 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        font-weight: 500;
        border-radius: 50px;
        box-shadow: 0 5px 20px rgba(108, 99, 255, 0.3);
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 7px 25px rgba(108, 99, 255, 0.4);
    }
    
    /* Upload Area */
    .uploadedFile {
        background: white;
        border: 2px dashed var(--primary-color);
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .uploadedFile:hover {
        border-color: var(--secondary-color);
        background: rgba(108, 99, 255, 0.05);
    }
    
    /* Progress Bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--success-color) 0%, var(--primary-color) 100%);
        border-radius: 10px;
        height: 10px;
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: linear-gradient(180deg, var(--dark-bg) 0%, #2D3456 100%);
    }
    
    .sidebar-card {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(255,255,255,0.2);
        color: white;
    }
    
    /* Select Box and Input Styling */
    .stSelectbox > div > div, .stMultiSelect > div > div {
        background: white;
        border-radius: 10px;
        border: 2px solid #E0E0E0;
        transition: border-color 0.3s ease;
    }
    
    .stSelectbox > div > div:focus-within, .stMultiSelect > div > div:focus-within {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(108, 99, 255, 0.1);
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        background: white;
        border-radius: 15px;
        padding: 0.5rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--primary-color) 0%, #8B7FFF 100%);
        color: white !important;
    }
    
    /* Alert Boxes */
    .success-box {
        background: linear-gradient(135deg, #00C9A7 0%, #00D4AA 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0, 201, 167, 0.3);
    }
    
    .warning-box {
        background: linear-gradient(135deg, #FFB800 0%, #FFD93D 100%);
        color: var(--text-dark);
        padding: 1rem 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(255, 184, 0, 0.3);
    }
    
    .info-box {
        background: linear-gradient(135deg, #74C0FC 0%, #94D3FF 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(116, 192, 252, 0.3);
    }
    
    /* Metrics Display */
    [data-testid="metric-container"] {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 3px 15px rgba(0,0,0,0.08);
        border: 1px solid #f0f0f0;
        transition: all 0.3s ease;
    }
    
    [data-testid="metric-container"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 5px 20px rgba(0,0,0,0.12);
    }
    
    /* Dataframe Styling */
    [data-testid="stDataFrame"] {
        background: white;
        border-radius: 15px;
        padding: 1rem;
        box-shadow: 0 3px 15px rgba(0,0,0,0.08);
    }
    
    /* Expander Styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 10px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, #e9ecef 0%, #adb5bd 100%);
    }
    
    /* Loading Animation */
    @keyframes pulse {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.05); opacity: 0.8; }
        100% { transform: scale(1); opacity: 1; }
    }
    
    .loading {
        animation: pulse 2s infinite;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main-title { font-size: 2.5rem; }
        .stats-number { font-size: 2rem; }
        .custom-card { padding: 1rem; }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def load_font_css():
    font_regular = None
    font_bold = None
    
    if os.path.exists("0 Nazanin.TTF"):
        with open("0 Nazanin.TTF", "rb") as f:
            font_regular = base64.b64encode(f.read()).decode()
    
    if os.path.exists("0 Nazanin Bold.TTF"):
        with open("0 Nazanin Bold.TTF", "rb") as f:
            font_bold = base64.b64encode(f.read()).decode()
    
    if font_regular and font_bold:
        font_css = f"""
        <style>
          @font-face {{
            font-family: 'Nazanin';
            src: url(data:font/truetype;charset=utf-8;base64,{font_regular}) format('truetype');
            font-weight: normal;
          }}
          @font-face {{
            font-family: 'Nazanin';
            src: url(data:font/truetype;charset=utf-8;base64,{font_bold}) format('truetype');
            font-weight: bold;
          }}
          * {{
            font-family: 'Nazanin', 'Vazirmatn', Tahoma, sans-serif !important;
          }}
        </style>
        """
        st.markdown(font_css, unsafe_allow_html=True)
# Initialize the app
load_css()
load_font_css()

# Header Section
st.markdown("""
<div class="main-header">
    <div class="main-title">📋 سامانه هوشمند ارزیابی رزومه</div>
    <div class="main-subtitle">ارزیابی حرفه‌ای رزومه‌ها با هوش مصنوعی پیشرفته</div>
</div>
""", unsafe_allow_html=True)

# Create tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["🏠 صفحه اصلی", "📊 تحلیل رزومه", "⚙️ تنظیمات", "📈 گزارشات"])

with tab1:
    # Stats Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="stats-card">
            <div class="stats-number">0</div>
            <div class="stats-label">رزومه بررسی شده</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stats-card" style="background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);">
            <div class="stats-number">0</div>
            <div class="stats-label">رزومه تأیید شده</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="stats-card" style="background: linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%);">
            <div class="stats-number">0%</div>
            <div class="stats-label">نرخ پذیرش</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="stats-card" style="background: linear-gradient(135deg, #FFD93D 0%, #FF6B6B 100%);">
            <div class="stats-number">0</div>
            <div class="stats-label">در حال بررسی</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Main Content Area
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.markdown("""
        <div class="custom-card">
            <div class="card-header">
                <span class="card-icon">📁</span>
                <span class="card-title">بارگذاری فایل رزومه‌ها</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "فایل اکسل حاوی رزومه‌ها را انتخاب کنید",
            type=["xlsx", "xls"],
            help="فایل اکسل باید حاوی اطلاعات رزومه‌ها باشد"
        )
        
        if uploaded_file:
            st.markdown("""
            <div class="success-box">
                ✅ فایل با موفقیت بارگذاری شد
            </div>
            """, unsafe_allow_html=True)
            
            # Read Excel with proper header handling
            df = pd.read_excel(uploaded_file, skiprows=2)  # Skip first 2 header rows
            
            with st.expander("👀 مشاهده پیش‌نمایش داده‌ها"):
                st.dataframe(df.head(10), use_container_width=True)
    
    with col_right:
        st.markdown("""
        <div class="custom-card">
            <div class="card-header">
                <span class="card-icon">💡</span>
                <span class="card-title">راهنمای سریع</span>
            </div>
            <div style="padding: 0.5rem 0;">
                <p>📌 فایل اکسل خود را آپلود کنید</p>
                <p>📌 موقعیت‌های شغلی را انتخاب کنید</p>
                <p>📌 مهارت‌های مورد نیاز را تنظیم کنید</p>
                <p>📌 فرآیند ارزیابی را شروع کنید</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="custom-card" style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);">
            <div class="card-header">
                <span class="card-icon">🎯</span>
                <span class="card-title">وضعیت سیستم</span>
            </div>
            <div style="text-align: center; padding: 1rem;">
                <div style="font-size: 2rem;">🟢</div>
                <div style="font-weight: 600;">سیستم فعال</div>
                <div style="color: #666; font-size: 0.9rem;">آماده پردازش</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.markdown("""
    <div class="custom-card">
        <div class="card-header">
            <span class="card-icon">🎯</span>
            <span class="card-title">انتخاب موقعیت‌های شغلی</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        job_titles = [
            "تحقیق و توسعه سامانه‌ها",
            "توسعه راهکارهای تحلیل اطلاعات مکانی",
            "توسعه راهکارهای مبتنی بر هوش مصنوعی",
            "کارشناس ارتباط با مراکز پژوهشی",
            "کارشناس تحلیلگر داده و هوش تجاری"
        ]
        
        selected_jobs = st.multiselect(
            "موقعیت‌های شغلی مورد نظر",
            job_titles,
            help="می‌توانید چند موقعیت را انتخاب کنید"
        )
    
    with col2:
        custom_job = st.text_input(
            "موقعیت شغلی سفارشی",
            placeholder="در صورت نیاز، عنوان شغلی جدید وارد کنید"
        )
    
    st.markdown("""
    <div class="custom-card">
        <div class="card-header">
            <span class="card-icon">💼</span>
            <span class="card-title">مهارت‌های مورد نیاز</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    skills = [
        "Python", "JavaScript", "SQL", "Machine Learning",
        "Data Analysis", "GIS", "Remote Sensing"
    ]
    
    selected_skills = st.multiselect(
        "مهارت‌های تخصصی",
        skills,
        help="مهارت‌های مورد نیاز برای موقعیت شغلی را انتخاب کنید"
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col2:
        if st.button("🚀 شروع فرآیند ارزیابی", use_container_width=True):
            st.balloons()
            st.markdown("""
            <div class="info-box">
                ⏳ در حال پردازش رزومه‌ها... لطفا صبر کنید
            </div>
            """, unsafe_allow_html=True)

with tab3:
    st.markdown("""
    <div class="custom-card">
        <div class="card-header">
            <span class="card-icon">⚙️</span>
            <span class="card-title">تنظیمات سیستم</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.slider("حداقل امتیاز قبولی", 0, 100, 70, help="رزومه‌هایی با امتیاز بالاتر از این مقدار تأیید می‌شوند")
        st.slider("تعداد رزومه در هر دسته", 5, 50, 10)
        st.selectbox("مدل هوش مصنوعی", ["Gemini 2.5 Flash", "Gemini Pro", "GPT-4"])
    
    with col2:
        st.number_input("حداقل سن", 18, 65, 22)
        st.number_input("حداکثر سن", 18, 65, 35)
        st.number_input("حقوق پایه (میلیون تومان)", 10, 100, 20)

with tab4:
    st.markdown("""
    <div class="custom-card">
        <div class="card-header">
            <span class="card-icon">📈</span>
            <span class="card-title">گزارش تحلیل رزومه‌ها</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sample data for demonstration
    if st.checkbox("نمایش نمونه گزارش"):
        sample_data = pd.DataFrame({
            'نام': ['علی', 'مریم', 'حسن', 'زهرا'],
            'امتیاز نهایی': [85, 92, 78, 88],
            'وضعیت': ['تأیید', 'تأیید', 'در انتظار', 'تأیید'],
            'موقعیت پیشنهادی': ['توسعه‌دهنده', 'تحلیلگر', 'پشتیبان', 'طراح']
        })
        
        st.dataframe(sample_data, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📥 دانلود گزارش Excel",
                data=b"",  # This would be your actual Excel data
                file_name="report.xlsx",
                mime="application/vnd.ms-excel",
                use_container_width=True
            )
        with col2:
            st.download_button(
                "📥 دانلود گزارش PDF",
                data=b"",  # This would be your actual PDF data
                file_name="report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
def style_excel(path): 
    wb = openpyxl.load_workbook(path) 
    ws = wb.active 

    header_fill = PatternFill(start_color="B7DEE8", end_color="B7DEE8", fill_type="solid")
    row_fill_odd = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    row_fill_even = PatternFill(start_color="EAF3FA", end_color="EAF3FA", fill_type="solid")

    header_font = Font(bold=True, name='B Homa', size=14)
    row_font = Font(name='B Homa', size=12)
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    border = Border(
        left=Side(border_style="thin", color="CCCCCC"),
        right=Side(border_style="thin", color="CCCCCC"),
        top=Side(border_style="thin", color="CCCCCC"),
        bottom=Side(border_style="thin", color="CCCCCC"),
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
        if col[0].value == "تحلیل نهایی":
            for cell in col:
                cell.alignment = Alignment(wrap_text=True, vertical="top", horizontal="center")

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
                print(f"⚠️ خطا با API {api_key[:10]}...: {str(e)}")
                self.idx = (self.idx + 1) % num_keys
                if self.idx == start_idx:
                    raise RuntimeError("❌ تمام API Keyها با خطا مواجه شدند.")
        raise RuntimeError("❌ تمام API Keyها با خطا مواجه شدند.")

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
            print(f"⚠️ خطا با API {api_key[:10]}...: {str(e)}")
            continue
    raise RuntimeError("❌ تمام API Keyها با خطا مواجه شدند.")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key="AIzaSyC8tN4kY2QU5ACRacPazzRQeJPtAC08Vm8")

RESULT_FILE_PATH = Path("resume_results.xlsx")
if RESULT_FILE_PATH.exists():
    RESULT_FILE_PATH.unlink()

os.environ['SSL_CERT_FILE'] = certifi.where()

proxy_url = "http://172.16.217.234:33525"
os.environ['HTTP_PROXY'] = proxy_url
os.environ['HTTPS_PROXY'] = proxy_url

test_url = "https://generativelanguage.googleapis.com/v1beta/models"
try:
    response = requests.get(test_url, proxies={"http": proxy_url, "https": proxy_url}, timeout=5)
    if response.status_code == 200:
        print("✅ اتصال برقرار است.")
    else:
        print(f"⚠️ کد وضعیت: {response.status_code}")
except Exception as e:
    print(f"❌ خطا در اتصال پراکسی: {e}")

pd.set_option('display.max_rows', None)
OUTPUT_ALL_PATH = Path("recruitment_score.xlsx")
BATCH_SIZE = 10
RESULT_FILE_PATH = Path("resume_results.xlsx")

if 'live_results' not in st.session_state:
    st.session_state['live_results'] = []

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

def score_text_section(text): 
    if not text or str(text).strip() == "": 
        return 30

    prompt = f"""  
    Please rate the quality of the following resume section on a scale of 0 to 100.  
    Consider clarity, relevance, and value in a resume.  
    Return only a number between 0.0 and 1.0.  

    Text: 
    \"\"\" 
    {text} 
    \"\"\" 
    """ 

    try: 
        response = llm.invoke([HumanMessage(content=prompt)]) 
        score = float(response.content.strip()) 
        return round(max(0.0, min(1.0, score)) * 100, 2)
    except: 
        return 30

def process_batch(batch_df, prompt_text):
    payload = {
        "employer requirements": prompt_text,
        "applicant information": [
            {"resume": " ".join([str(row[col]) for col in batch_df.columns]), "id": str(idx)}
            for idx, row in batch_df.iterrows()
        ]
    }
    try:
        response = safe_generate_content(
            model='gemini-2.5-flash',
            contents=json.dumps(payload, ensure_ascii=False),
            config={
                'response_mime_type': 'application/json',
                'system_instruction': """
شما یک ارزیاب حرفه‌ای منابع انسانی هستید. معیارهای ارزیابی:
- تطابق مهارت‌های نرم‌افزاری
- تطابق سوابق شغلی
- مقطع و رشته تحصیلی مرتبط
- دانشگاه دولتی و معتبر
- سن مناسب (۲۲ تا ۳۵)
- حقوق درخواستی (۲۰ تا ۴۵ میلیون)
امتیاز بین ۱ تا ۱۰ بدهید. اگر اطلاعات نبود، بنویسید: 'اطلاعات کافی نیست'.
""",
                'response_schema': {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "score": {"type": "number", "nullable": False},
                            "check_id": {"type": "string", "nullable": False},
                            "why": {"type": "string", "nullable": False}
                        }
                    }
                },
                'temperature': 0
            }
        )
        result = json.loads(response.candidates[0].content.parts[0].text)
        return pd.DataFrame(result)
    except Exception:
        return pd.DataFrame([{
            "score": 1.0,
            "check_id": str(idx),
            "why": "خطا در پردازش - اطلاعات کافی نیست"
        } for idx, row in batch_df.iterrows()])

def to_excel(df, path):
    df.to_excel(path, index=False)

def match_resume_to_job_parallel(resume_text, job_profiles, threshold=7):
    best_match = None
    best_score = -1
    best_reason = ""
    log_messages = []

    def evaluate_job_with_key(api_key, job):
        prompt = f"""بر اساس اطلاعات زیر:
رزومه:
{resume_text}

موقعیت شغلی:
عنوان: {job['title']}
شرح وظایف: {'؛ '.join(job['tasks'])}
مهارت‌های تخصصی: {'؛ '.join([c['name'] for c in job.get('competencies_technical', [])])}
رشته‌های مرتبط: {'؛ '.join(job.get('majors', []))}

آیا این رزومه با این موقعیت شغلی تطابق دارد؟ لطفاً:
- یک امتیاز بین ۰ تا 100 بده
- در صورت مناسب بودن، دلیل را شرح بده
- در صورت نامناسب بودن، بنویس چرا مناسب نیست

لطفاً همیشه پاسخ را به فرمت زیر و با هردو بخش بده:
امتیاز: [یک عدد از 0 تا 100]
دلیل: [یک جمله واضح و دقیق شامل دلیل انتخاب یا عدم انتخاب]

"""
        try:
            response = safe_generate_content_for_key(
                api_key=api_key,
                model="gemini-2.5-flash",
                contents=prompt,
                config={"temperature": 0}
            )
            if isinstance(response, dict) and "error" in response:
                return None

            text = response.candidates[0].content.parts[0].text.strip()
            lines = [line.strip() for line in text.splitlines() if line.strip() != ""]

            score = -1
            reason = "توضیحی ارائه نشده است"

            for line in lines:
                if line.startswith("امتیاز"):
                    try:
                        score = int("".join(filter(str.isdigit, line)))
                    except:
                        score = -1
                if line.startswith("دلیل"):
                    reason = line.replace("دلیل:", "").strip()

            if reason == "توضیحی ارائه نشده است":
                for i, line in enumerate(lines):
                    if "امتیاز" in line and i + 1 < len(lines):
                        possible_reason = lines[i + 1]
                        if not possible_reason.startswith("امتیاز") and "دلیل" not in possible_reason:
                            reason = possible_reason
                            break

            return {"title": job["title"], "score": score, "reason": reason}

        except Exception as e:
            return None

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_job = {
            executor.submit(evaluate_job_with_key, api_key, job): job
            for api_key, job in zip(API_KEYS * (len(job_profiles) // len(API_KEYS) + 1), job_profiles)
        }

        for future in concurrent.futures.as_completed(future_to_job):
            result = future.result()
            if result:
                log_messages.append(f"🔹 {result['title']} → امتیاز: {result['score']} | دلیل: {result['reason']}")
                if result["score"] > best_score:
                    best_score = result["score"]
                    best_match = result["title"]
                    best_reason = result["reason"]

    log = "\n".join(log_messages)

    if best_score >= threshold:
        return best_match, best_reason, log
    else:
        return "مناسب هیچکدام از شناسنامه‌های شغلی نمی‌باشد", best_reason or "رزومه تطابق کافی با هیچ‌کدام از شغل‌ها ندارد.", log


def apply_matching_to_batch(batch_df):
    all_results = []

    for idx, row in batch_df.iterrows():
        resume_text = " ".join([str(row[col]) for col in batch_df.columns])
        match_df = evaluate_resume_against_all_jobs(resume_text, JOB_PROFILES)

        match_df["ردیف رزومه"] = idx + 1
        match_df["نام"] = row.get("نام", "")
        match_df["نام خانوادگی"] = row.get("نام خانوادگی", "")

        all_results.append(match_df)

    final_df = pd.concat(all_results, ignore_index=True)
    return final_df

top_universities = ['دانشگاه صنعتی شریف', 'دانشگاه تهران', 'دانشگاه صنعتی امیرکبیر', 'دانشگاه علم و صنعت ایران']
public_keywords = ['صنعتی', 'تهران', 'امیرکبیر', 'علم و صنعت', 'فردوسی', 'تبریز', 'اصفهان', 'دولتی']

def is_public_university(univ_name):
    return any(keyword in str(univ_name) for keyword in public_keywords)

def is_top_university(univ_name):
    return any(top in str(univ_name) for top in top_universities)

def color_score_column(val):
    if val >= 9:
        color = '#00C853'
    elif val >= 8:
        color = '#AEEA00'
    elif val >= 7:
        color = '#FFD600'
    elif val >= 6:
        color = '#FF9100'
    elif val >= 5:
        color = '#FF3D00'
    else:
        color = '#D50000'
    return f'background-color: {color}; color: white; font-weight: bold'


def adjust_score(row):
    score = row['score']
    if 'سن' in row and (row['سن'] < 22 or row['سن'] > 35):
        score -= 1
    if 'حقوق درخواستی' in row and (row['حقوق درخواستی'] < 20 or row['حقوق درخواستی'] > 45):
        score -= 1
    if 'مقطع تحصیلی' in row and 'کارشناسی' not in str(row['مقطع تحصیلی']):
        score -= 0.5
    univ = row.get('نام دانشگاه', '')
    if is_public_university(univ):
        score += 0.5
    if is_top_university(univ):
        score += 0.5
    return max(min(score, 10), 1.0)

def skill_agent(resume, skills):
    prompt = f"""
    شما یک ارزیاب منابع انسانی هستید. فقط مهارت‌های زیر را در رزومه زیر بررسی کن:
    مهارت‌های مورد انتظار: {', '.join(skills)}
    رزومه:
    {resume}
    
    یک عدد بین ۰ تا ۱۰۰ به میزان تطابق مهارت‌های رزومه با مهارت‌های مورد انتظار بده و یک جمله دلیل برای این امتیاز بنویس.
    فرمت دقیق پاسخ:
    امتیاز: [یک عدد]
    دلیل: [یک جمله کوتاه]
    """
    messages = [HumanMessage(content=prompt)]
    result = rotating_llm.invoke(messages)
    text = result.content
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    score, reason = 0, ""
    for line in lines:
        if line.startswith("امتیاز"):
            score = int("".join(filter(str.isdigit, line)))
        if line.startswith("دلیل"):
            reason = line.replace("دلیل:", "").strip()
    return score, reason

skill_tool = Tool(
    name="SkillAgent",
    func=lambda input: skill_agent(input["resume"], input["skills"]),
    description="ارزیابی مهارت‌های نرم‌افزاری"
)
experience_tool = Tool(
    name="ExperienceAgent",
    func=lambda input: experience_agent(input["resume"], input["required_experience_desc"]),
    description="ارزیابی تجربه شغلی"
)
education_tool = Tool(
    name="EducationAgent",
    func=lambda input: education_agent(
        input["resume"],
        input["university_list"],
        input["major_list"],
        input["job_profile_title"]
    ),
    description="ارزیابی تحصیلات دانشگاهی"
)
volunteering_tool = Tool(
    name="VolunteeringAgent",
    func=lambda input: volunteering_agent(input["resume"], input.get("volunteering_field")),
    description="ارزیابی فعالیت داوطلبانه"
)
softskills_tool = Tool(
    name="SoftSkillsAgent",
    func=lambda input: softskills_agent(input["resume"], input.get("about_me_field")),
    description="ارزیابی مهارت‌های نرم و شایستگی فردی"
)

def experience_agent(resume, required_experience_desc):
    prompt = f"""
    شما یک ارزیاب منابع انسانی هستید. فقط تجربه‌های شغلی رزومه زیر را از نظر میزان تطابق با نیازهای شغلی زیر بررسی کن:
    سابقه مورد انتظار: {required_experience_desc}
    رزومه:
    {resume}
    
    یک عدد بین ۰ تا ۱۰۰ به میزان تطابق سابقه کاری رزومه با نیازهای موقعیت شغلی بده و یک جمله دلیل برای این امتیاز بنویس.
    فرمت دقیق پاسخ:
    امتیاز: [یک عدد]
    دلیل: [یک جمله کوتاه]
    """
    messages = [HumanMessage(content=prompt)]
    result = rotating_llm.invoke(messages)
    text = result.content
    lines = [l.strip() for l in text.splitlines() if l.strip()]  
    score, reason = 0, ""
    for line in lines:
        if line.startswith("امتیاز"):
            score = int("".join(filter(str.isdigit, line)))
        if line.startswith("دلیل"):
            reason = line.replace("دلیل:", "").strip()
    return score, reason


def education_agent(resume, universities_info, major_list, job_profile_title):
    prompt = f"""
    شما یک ارزیاب منابع انسانی هستید. بخش تحصیلات رزومه زیر را فقط از نظر سه معیار بررسی کن:
    ۱. اعتبار دانشگاه و نوع آن (در فهرست زیر دانشگاه‌های معتبر و نوع هرکدام آمده است، دانشگاه‌های برتر و دولتی امتیاز بیشتری دارند، آزاد و پیام نور امتیاز متوسط، غیرانتفاعی و علمی کاربردی امتیاز پایین‌تر):
    {chr(10).join(universities_info)}
    ۲. تطابق رشته تحصیلی با موقعیت شغلی "{job_profile_title}" (لیست رشته‌های مطلوب: {', '.join(major_list)})
    ۳. مدت زمان تحصیل کارشناسی (زیر ۴ سال عالی، ۴ سال خوب، بیشتر از ۴ سال ضعیف)
    
    رزومه:
    {resume}

    یک عدد بین ۰ تا ۱۰۰ به میزان شایستگی تحصیلات رزومه نسبت به نیازهای شغلی بده و یک جمله دلیل برای این امتیاز بنویس.
    فرمت دقیق پاسخ:
    امتیاز: [یک عدد]
    دلیل: [یک جمله کوتاه]
    """
    messages = [HumanMessage(content=prompt)]
    result = rotating_llm.invoke(messages)
    text = result.content
    lines = [l.strip() for l in text.splitlines() if l.strip()]  
    score, reason = 0, ""
    for line in lines:
        if line.startswith("امتیاز"):
            score = int("".join(filter(str.isdigit, line)))
        if line.startswith("دلیل"):
            reason = line.replace("دلیل:", "").strip()
    return score, reason

def volunteering_agent(resume, volunteering_field=None):
    field = volunteering_field if volunteering_field else resume
    prompt = f"""
    شما یک ارزیاب منابع انسانی هستید. فقط فعالیت‌های داوطلبانه و کارهای اجتماعی رزومه زیر را بررسی کن:
    اگر فعالیت داوطلبانه مرتبط و تأثیرگذار (در سطح بالا) باشد، امتیاز بالا بده، اگر نباشد یا کم باشد امتیاز پایین.
    رزومه/فعالیت داوطلبانه:
    {field}

    یک عدد بین ۰ تا ۱۰۰ به فعالیت داوطلبانه بده و یک جمله دلیل برای این امتیاز بنویس.
    فرمت دقیق پاسخ:
    امتیاز: [یک عدد]
    دلیل: [یک جمله کوتاه]
    """
    messages = [HumanMessage(content=prompt)]
    result = rotating_llm.invoke(messages)
    text = result.content
    lines = [l.strip() for l in text.splitlines() if l.strip()]  
    score, reason = 0, ""
    for line in lines:
        if line.startswith("امتیاز"):
            score = int("".join(filter(str.isdigit, line)))
        if line.startswith("دلیل"):
            reason = line.replace("دلیل:", "").strip()
    return score, reason

def softskills_agent(resume, about_me_field=None):
    field = about_me_field if about_me_field else resume
    prompt = f"""
    شما یک ارزیاب منابع انسانی هستید. فقط مهارت‌های نرم و شایستگی‌های فردی رزومه زیر را بررسی کن:
    ویژگی‌هایی مثل: کار تیمی، ارتباط موثر، مدیریت، مسئولیت‌پذیری، دقت، میل به یادگیری و هوش هیجانی (EQ) را تحلیل کن.
    اگر رزومه یا بخش 'درباره من' شواهد قوی از این ویژگی‌ها دارد امتیاز بالا بده، اگر نداشت یا ضعیف بود امتیاز پایین.
    متن برای تحلیل:
    {field}

    یک عدد بین ۰ تا ۱۰۰ به مهارت‌های نرم بده و یک جمله دلیل برای این امتیاز بنویس.
    فرمت دقیق پاسخ:
    امتیاز: [یک عدد]
    دلیل: [یک جمله کوتاه]
    """
    messages = [HumanMessage(content=prompt)]
    result = rotating_llm.invoke(messages)
    text = result.content
    lines = [l.strip() for l in text.splitlines() if l.strip()]  
    score, reason = 0, ""
    for line in lines:
        if line.startswith("امتیاز"):
            score = int("".join(filter(str.isdigit, line)))
        if line.startswith("دلیل"):
            reason = line.replace("دلیل:", "").strip()
    return score, reason

def scoring_chain(
    resume,
    skills,
    required_experience_desc,
    universities_info,
    major_list,
    job_profile_title,
    volunteering_field=None,
    about_me_field=None
):
    results = {}

    skill_score, skill_reason = skill_agent(resume, skills)
    results["SkillAgent"] = {"score": skill_score, "reason": skill_reason}

    exp_score, exp_reason = experience_agent(resume, required_experience_desc)
    results["ExperienceAgent"] = {"score": exp_score, "reason": exp_reason}

    edu_score, edu_reason = education_agent(resume, universities_info, major_list, job_profile_title)
    results["EducationAgent"] = {"score": edu_score, "reason": edu_reason}

    vol_score, vol_reason = volunteering_agent(resume, volunteering_field)
    results["VolunteeringAgent"] = {"score": vol_score, "reason": vol_reason}

    soft_score, soft_reason = softskills_agent(resume, about_me_field)
    results["SoftSkillsAgent"] = {"score": soft_score, "reason": soft_reason}

    results["VolunteeringAgent"]["score"] = score_text_section(vol_reason)
    results["SoftSkillsAgent"]["score"] = score_text_section(soft_reason)

    final_score = 0
    for agent, w in AGENT_WEIGHTS.items():
        final_score += results[agent]["score"] * w

    final_score = round(final_score / sum(AGENT_WEIGHTS.values()), 2)
    results["FinalScore"] = final_score

    return results


def evaluate_resume_against_all_jobs(resume_text, job_profiles):
    prompt = f"""شما یک ارزیاب منابع انسانی هستید. با توجه به رزومه زیر، لطفاً برای هر یک از موقعیت‌های شغلی تعریف‌شده، یک درصد تطابق بین ۰ تا ۱۰۰ بدهید و یک دلیل منطقی برای آن ذکر کنید.

رزومه:
{resume_text}

ساختار پاسخ دقیقا به صورت JSON زیر باشد:
[
  {{
    "title": "عنوان شغل اول",
    "match_percent": 85,
    "reason": "توضیح دلیل تطابق یا عدم تطابق"
  }},
  {{
    "title": "عنوان شغل دوم",
    "match_percent": 45,
    "reason": "..."
  }}
  ...
]
موقعیت‌های شغلی:
{json.dumps(job_profiles, ensure_ascii=False)}
"""

    try:
        response = safe_generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0
            }
        )
        json_text = response.candidates[0].content.parts[0].text.strip()
        parsed = json.loads(json_text)
        return pd.DataFrame(parsed)
    except Exception as e:
        st.error(f"❌ خطا در تحلیل تطابق: {e}")
        return pd.DataFrame()

def process_resume_row(row, row_index):
    resume_text = " ".join([str(row[col]) for col in row.index])
    title, reason, log = match_resume_to_job(resume_text, JOB_PROFILES)

    gemini_df = process_batch(pd.DataFrame([row]), prompt_text="ارزیابی عمومی رزومه")
    initial_score = gemini_df.iloc[0]['score']

    score = adjust_score({**row.to_dict(), 'score': initial_score})

    new_data = row.to_dict()
    new_data.update({
        "ردیف": row_index + 1,
        "score": score,
        "دلیل": gemini_df.iloc[0]['why'],
        "موقعیت شغلی پیشنهادی": title,
        "دلیل انتخاب موقعیت شغلی": reason,
        "گزارش بررسی شناسنامه‌ها": log
    })

    if RESULT_FILE_PATH.exists():
        existing = pd.read_excel(RESULT_FILE_PATH)
        updated = pd.concat([existing, pd.DataFrame([new_data])], ignore_index=True)
    else:
        updated = pd.DataFrame([new_data])

    updated.to_excel(RESULT_FILE_PATH, index=False)

    st.session_state['live_results'].append(new_data)
    return new_data

st.markdown("""
    <style>
    .custom-title {
        font-size: 50px !important;
        color: #1a73e8 !important;
        font-weight: bold !important;
        text-align: center !important;
        margin-top: 40px !important;
        margin-bottom: 30px !important;
    }
    </style>
""", unsafe_allow_html=True)
st.markdown('<div class="custom-title">📋 سامانه هوشمند ارزیابی رزومه</div>', unsafe_allow_html=True)
st.markdown("<p style='font-size: 16px; color: #555;'>ارزیابی هوشمند رزومه‌ها بر اساس معیارهای منابع انسانی، شناسنامه‌های شغلی و مهارت‌های تخصصی.</p>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("📄 فایل اکسل رزومه‌ها را بارگذاری کنید:", type=["xlsx"])

# Sidebar Enhancement
with st.sidebar:
    st.markdown("""
    <div class="sidebar-card">
        <h3 style="text-align: center;">📊 آمار لحظه‌ای</h3>
        <hr style="opacity: 0.3;">
    </div>
    """, unsafe_allow_html=True)
    
    st.metric("رزومه‌های پردازش شده", "0", "0")
    st.metric("زمان باقیمانده", "0:00", "")
    
    st.markdown("""
    <div class="sidebar-card">
        <h3 style="text-align: center;">🔄 عملیات سریع</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔄 بازنشانی سیستم", use_container_width=True):
        st.rerun()
    
    if st.button("💾 ذخیره پیکربندی", use_container_width=True):
        st.success("تنظیمات ذخیره شد!")
    
    st.markdown("""
    <div class="sidebar-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
        <div style="text-align: center;">
            <div style="font-size: 2rem;">💎</div>
            <div style="font-weight: 600;">نسخه حرفه‌ای</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">v2.0.0</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

job_titles = [job['title'] for job in JOB_PROFILES]

selected_job_titles = st.multiselect(
    "عنوان شغلی مورد نظر را انتخاب کنید (امکان انتخاب چندتایی):",
    options=job_titles,
    default=None
)

custom_job_title = st.text_input("در صورتی که عنوان شغلی مورد نظر شما در لیست نبود، اینجا وارد کنید:")

all_selected_titles = selected_job_titles.copy()
if custom_job_title.strip() != "":
    all_selected_titles.append(custom_job_title.strip())

selected_skills = []
for job in JOB_PROFILES:
    if job["title"] in all_selected_titles:
        selected_skills.extend([c['name'] for c in job.get('competencies_technical', [])])

selected_skills = list(sorted(set(selected_skills)))

edited_skills = st.multiselect(
    "مهارت‌های مورد نیاز را بررسی و ویرایش کنید:",
    options=selected_skills,
    default=selected_skills
)

custom_skill = st.text_input("در صورت نیاز، مهارت جدید وارد کنید:")

all_skills = edited_skills.copy()
if custom_skill.strip() and custom_skill.strip() not in all_skills:
    all_skills.append(custom_skill.strip())

def process_single_resume(args):
    """Process a single resume with a specific API key"""
    idx, row, api_key, all_skills = args
    
    try:
        llm_instance = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)
        
        resume = " ".join([str(row[col]) for col in row.index]) 
        required_experience_desc = "سابقه مرتبط با عنوان شغلی" 
        universities = universities_info 
        major_list = []
        job_profile_title = ""
        volunteering_field = row.get("فعالیت داوطلبانه", "") 
        about_me_field = row.get("درباره من", "")

        results = scoring_chain(
            resume, 
            all_skills, 
            required_experience_desc, 
            universities, 
            major_list, 
            job_profile_title, 
            volunteering_field, 
            about_me_field
        )

        row_data = row.to_dict()
        row_data['ردیف'] = idx + 1
        for agent, detail in results.items():
            if agent != "FinalScore":
                row_data[f"{agent}_score"] = detail['score']
                row_data[f"{agent}_reason"] = detail['reason']
        row_data['final_score'] = results['FinalScore']
        row_data['تایید و رد اولیه'] = "تایید" if row_data['final_score'] >= 70 else "رد"
        
        return (idx, row_data, None)
    
    except Exception as e:
        return (idx, None, str(e))

if uploaded_file:
    df = pd.read_excel(uploaded_file, skiprows=2)
    
    st.info(f"تعداد رزومه‌های بارگذاری شده: {len(df)} | تعداد ستون‌ها: {len(df.columns)}")
    
    with st.expander("نمایش پیش‌نمایش داده‌ها"):
        st.dataframe(df.head())
    
    stage = st.radio("🧩 مرحله موردنظر را انتخاب کنید:", ["امتیازدهی", "تطبیق با شناسنامه‌های شغلی"])

    if stage == "امتیازدهی": 
        st.markdown("### 🚀 مرحله امتیازدهی رزومه‌ها") 
        
        max_workers = min(len(API_KEYS), len(df))
        st.info(f"پردازش موازی با {max_workers} API Key برای {len(df)} رزومه")
        
        if st.button("شروع امتیازدهی"): 
            results_placeholder = st.empty() 
            progress_bar = st.progress(0) 
            rows = [None] * len(df)
            completed = 0
            
            processing_args = [
                (idx, row, API_KEYS[idx % len(API_KEYS)], all_skills)
                for idx, (_, row) in enumerate(df.iterrows())
            ]
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_idx = {
                    executor.submit(process_single_resume, args): args[0] 
                    for args in processing_args
                }
                
                for future in concurrent.futures.as_completed(future_to_idx):
                    idx, row_data, error = future.result()
                    
                    if error:
                        st.warning(f"⚠️ خطا در پردازش رزومه ردیف {idx + 1}: {error}")
                        row_data = df.iloc[idx].to_dict()
                        row_data['ردیف'] = idx + 1
                        row_data['تایید و رد اولیه'] = "خطا"
                        row_data['final_score'] = 0
                    
                    rows[idx] = row_data
                    completed += 1
                    
                    progress_bar.progress(completed / len(df))
                    
                    current_results = [r for r in rows if r is not None]
                    if current_results:
                        temp_df = pd.DataFrame(current_results)
                        results_placeholder.dataframe(temp_df)
                    
                    live_df = pd.DataFrame(current_results)
                    total = len(df)
                    checked = len(live_df)
                    accepted = (live_df['تایید و رد اولیه'] == 'تایید').sum() if 'تایید و رد اولیه' in live_df.columns else 0
                    failed = (live_df['تایید و رد اولیه'] != 'تایید').sum() if 'تایید و رد اولیه' in live_df.columns else 0
                    
                    status_placeholder.success(f"بررسی شده: {checked} / {total}")
                    status_placeholder.markdown(f"🟢 قبول‌شده: {accepted}")
                    status_placeholder.markdown(f"🔴 رد‌شده: {failed}")
                    progress_placeholder.progress(checked / total)
            
            results_df = pd.DataFrame(rows)
            results_placeholder.dataframe(results_df)
            results_df.to_excel("resume_scoring.xlsx", index=False)
            style_excel("resume_scoring.xlsx")

            st.success("✅ امتیازدهی به پایان رسید.")

            with open("resume_scoring.xlsx", "rb") as f:
                st.download_button(
                    label="📥 دانلود فایل اکسل امتیازدهی",
                    data=f,
                    file_name="resume_scoring.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    elif stage == "تطبیق با شناسنامه‌های شغلی":
        st.markdown("### 🔍 مرحله تطبیق با شناسنامه‌های شغلی")
        results_placeholder = st.empty()
        progress_bar = st.progress(0)
        
        max_workers = min(len(API_KEYS), len(df))
        st.info(f"پردازش موازی با {max_workers} API Key برای {len(df)} رزومه")

        if st.button("🚀 شروع تطبیق با شناسنامه‌های شغلی"):
            try:
                def process_single_matching(args):
                    """Process job matching for a single resume"""
                    idx, row, api_key = args
                    try:
                        resume_text = " ".join([str(row[col]) for col in row.index])
                        
                        prompt = f"""شما یک ارزیاب منابع انسانی هستید. با توجه به رزومه زیر، لطفاً برای هر یک از موقعیت‌های شغلی تعریف‌شده، یک درصد تطابق بین ۰ تا ۱۰۰ بدهید و یک دلیل منطقی برای آن ذکر کنید.

رزومه:
{resume_text}

ساختار پاسخ دقیقا به صورت JSON زیر باشد:
[
  {{
    "title": "عنوان شغل اول",
    "match_percent": 85,
    "reason": "توضیح دلیل تطابق یا عدم تطابق"
  }},
  {{
    "title": "عنوان شغل دوم",
    "match_percent": 45,
    "reason": "..."
  }}
  ...
]
موقعیت‌های شغلی:
{json.dumps(JOB_PROFILES, ensure_ascii=False)}
"""
                        
                        client = genai.Client(api_key=api_key)
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=prompt,
                            config={
                                "response_mime_type": "application/json",
                                "temperature": 0
                            }
                        )
                        
                        json_text = response.candidates[0].content.parts[0].text.strip()
                        parsed = json.loads(json_text)
                        match_df = pd.DataFrame(parsed)
                        
                        match_df["ردیف رزومه"] = idx + 1
                        match_df["نام"] = row.get("نام", "")
                        match_df["نام خانوادگی"] = row.get("نام خانوادگی", "")
                        
                        return (idx, match_df, None)
                    except Exception as e:
                        return (idx, None, str(e))
                
                processing_args = [
                    (idx, row, API_KEYS[idx % len(API_KEYS)])
                    for idx, (_, row) in enumerate(df.iterrows())
                ]
                
                all_results = [None] * len(df)
                completed = 0
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_idx = {
                        executor.submit(process_single_matching, args): args[0]
                        for args in processing_args
                    }
                    
                    for future in concurrent.futures.as_completed(future_to_idx):
                        idx, match_df, error = future.result()
                        
                        if error:
                            st.warning(f"⚠️ خطا در تطبیق رزومه ردیف {idx + 1}: {error}")
                        else:
                            all_results[idx] = match_df
                        
                        completed += 1
                        progress_bar.progress(completed / len(df))
                
                match_results = pd.concat([r for r in all_results if r is not None], ignore_index=True)
                
                def make_sentence(row):
                    return f"میزان انطباق با موقعیت شغلی {row['title']} {int(row['match_percent'])}٪ است، زیرا: {row['reason']}"

                grouped = match_results.groupby("ردیف رزومه")

                final_rows = []
                for resume_row_num, group in grouped:
                    name = group["نام"].iloc[0]
                    family = group["نام خانوادگی"].iloc[0]
                    sentences = [make_sentence(row) for _, row in group.iterrows()]
                    full_text = "  ".join(sentences)
                    best_row = group.loc[group["match_percent"].idxmax()]
                    best_title = best_row["title"]

                    final_rows.append({
                        "ردیف رزومه": resume_row_num,
                        "نام": name,
                        "نام خانوادگی": family,
                        "موقعیت شغلی پیشنهادی": best_title,
                        "تحلیل نهایی": full_text
                    })

                summary_df = pd.DataFrame(final_rows)

                summary_path = "job_matching_summary.xlsx"
                summary_df.to_excel(summary_path, index=False)
                style_excel(summary_path)

                st.success("✅ تطبیق با شناسنامه‌های شغلی با موفقیت انجام شد.")
                st.dataframe(summary_df)

                with open(summary_path, "rb") as f:
                    st.download_button("📥 دانلود فایل نهایی تحلیل‌شده", f, file_name=summary_path)

                progress_bar.progress(1.0)
            
            except Exception as e:
                st.error(f"❌ خطا در انجام تطبیق: {e}")

if RESULT_FILE_PATH.exists():
    final_df = pd.read_excel(RESULT_FILE_PATH)

    display_df = final_df.copy()
    display_df.index = display_df.index + 1
    display_df.index.name = "ردیف"

    st.markdown("### ✅ جدول نهایی رزومه‌های بررسی‌شده")
    
    if 'score' in display_df.columns:
        styled_df = display_df.style.applymap(color_score_column, subset=['score'])
        st.dataframe(styled_df)
    else:
        st.dataframe(display_df)

    style_excel(RESULT_FILE_PATH)
    with open(RESULT_FILE_PATH, "rb") as f:
        st.download_button("📥 دانلود فایل نهایی", f, file_name="resume_results.xlsx")



