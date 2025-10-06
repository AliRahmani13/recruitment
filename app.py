import streamlit as st
import pandas as pd
import os
import base64

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

# Load Nazanin fonts if available
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
