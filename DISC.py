import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import base64
import time
from pathlib import Path
from random import shuffle

# ================== تنظیمات صفحه ==================
st.set_page_config(
    page_title="آزمون شخصیت‌شناسی DISC",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ================== استایل مدرن فارسی ==================
def apply_modern_style():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Vazirmatn', sans-serif !important;
    }
    
    html, body, [class*="css"] {
        direction: rtl;
        text-align: right;
    }
    
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .main-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 30px;
        padding: 40px;
        margin: 20px auto;
        max-width: 1000px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        backdrop-filter: blur(10px);
    }
    
    .header-title {
        text-align: center;
        font-size: 3.5em;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .header-subtitle {
        text-align: center;
        font-size: 1.3em;
        color: #666;
        margin-bottom: 40px;
        font-weight: 300;
    }
    
    .question-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 20px;
        padding: 30px;
        margin: 20px 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        border: 2px solid #e0e0e0;
        transition: all 0.3s ease;
    }
    
    .question-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(0,0,0,0.15);
    }
    
    .question-text {
        font-size: 1.8em;
        font-weight: 600;
        color: #1a1a1a;
        margin-bottom: 20px;
        text-align: center;
    }
    
    .timer-box {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        font-size: 1.5em;
        font-weight: 600;
        color: white;
        margin: 20px 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    .progress-container {
        background: white;
        border-radius: 15px;
        padding: 15px;
        margin: 20px 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 15px 40px;
        font-size: 1.2em;
        font-weight: 600;
        border-radius: 50px;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        width: 100%;
        margin: 10px 0;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.3);
    }
    
    .stRadio > label {
        font-size: 1.2em;
        font-weight: 600;
        color: #1a1a1a;
        margin-bottom: 15px;
    }
    
    .stRadio > div {
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
    }
    
    .stRadio > div > label {
        color: #1a1a1a !important;
        font-size: 1.1em !important;
        padding: 15px !important;
        margin: 8px 0 !important;
        background: #f8f9fa !important;
        border-radius: 10px !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
        border: 2px solid transparent !important;
    }
    
    .stRadio > div > label:hover {
        background: #e3f2fd !important;
        border-color: #667eea !important;
        transform: translateX(-5px) !important;
    }
    
    .stRadio > div > label > div {
        color: #1a1a1a !important;
        font-weight: 500 !important;
    }
    
    .stRadio > div > label[data-checked="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border-color: #667eea !important;
    }
    
    .stRadio > div > label[data-checked="true"] > div {
        color: white !important;
    }
    
    .result-card {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        border-radius: 20px;
        padding: 30px;
        margin: 20px 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    }
    
    .disc-badge {
        display: inline-block;
        padding: 10px 25px;
        border-radius: 50px;
        font-size: 1.5em;
        font-weight: 700;
        margin: 10px 5px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    .badge-d {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
    }
    
    .badge-i {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        color: #333;
    }
    
    .badge-s {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        color: #333;
    }
    
    .badge-c {
        background: linear-gradient(135deg, #96fbc4 0%, #f9f586 100%);
        color: #333;
    }
    
    .feature-box {
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        border-right: 5px solid #667eea;
    }
    
    .feature-title {
        font-size: 1.3em;
        font-weight: 600;
        color: #667eea;
        margin-bottom: 10px;
    }
    
    .feature-content {
        font-size: 1.1em;
        color: #1a1a1a;
        line-height: 1.8;
    }
    
    /* حذف فوتر استریملیت */
    footer {
        visibility: hidden;
    }
    
    /* انیمیشن */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animated {
        animation: fadeIn 0.5s ease-out;
    }
    </style>
    """, unsafe_allow_html=True)

apply_modern_style()

# ================== متغیرهای سراسری ==================
TOTAL_TIME = 20 * 60
TOTAL_QUESTIONS = 24

if 'start_time' not in st.session_state:
    st.session_state.start_time = time.time()
if 'responses' not in st.session_state:
    st.session_state.responses = []
    st.session_state.current_q = 0
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# ================== سوالات DISC ==================
questions = [
    {
        "text": "در یک جلسه کاری ترجیح می‌دهم:",
        "options": [
            {"label": "کنترل جلسه را به‌دست بگیرم", "dimension": "D"},
            {"label": "با افراد جدید ارتباط برقرار کنم", "dimension": "I"},
            {"label": "شنونده خوبی باشم و فضای آرام حفظ شود", "dimension": "S"},
            {"label": "مطمئن شوم همه‌چیز طبق برنامه پیش می‌رود", "dimension": "C"},
        ]
    },
    {
        "text": "وقتی با یک چالش سخت مواجه می‌شوم:",
        "options": [
            {"label": "سریع تصمیم می‌گیرم و عمل می‌کنم", "dimension": "D"},
            {"label": "از دیگران الهام می‌گیرم یا نظرشان را می‌پرسم", "dimension": "I"},
            {"label": "صبر می‌کنم تا شرایط بهتر شود", "dimension": "S"},
            {"label": "اطلاعات دقیق جمع‌آوری می‌کنم و با تحلیل جلو می‌روم", "dimension": "C"},
        ]
    },
    {
        "text": "در پروژه‌های تیمی معمولاً من:",
        "options": [
            {"label": "نقش رهبری را برعهده می‌گیرم", "dimension": "D"},
            {"label": "باعث انگیزه‌بخشی به تیم می‌شوم", "dimension": "I"},
            {"label": "با همه هماهنگ و همراه هستم", "dimension": "S"},
            {"label": "روی روند و دقت تمرکز می‌کنم", "dimension": "C"},
        ]
    },
    {
        "text": "وقتی برنامه‌ای تغییر می‌کند:",
        "options": [
            {"label": "سعی می‌کنم کنترل شرایط را حفظ کنم", "dimension": "D"},
            {"label": "به دیگران انگیزه می‌دهم تا هماهنگ شوند", "dimension": "I"},
            {"label": "خونسردی خودم را حفظ می‌کنم", "dimension": "S"},
            {"label": "دلایل تغییر را بررسی می‌کنم", "dimension": "C"},
        ]
    },
    {
        "text": "در مواجهه با ضرب‌العجل کاری:",
        "options": [
            {"label": "به‌سرعت تصمیم می‌گیرم", "dimension": "D"},
            {"label": "دیگران را تشویق به همکاری می‌کنم", "dimension": "I"},
            {"label": "با آرامش عمل می‌کنم", "dimension": "S"},
            {"label": "برنامه‌ریزی دقیق انجام می‌دهم", "dimension": "C"},
        ]
    },
    {
        "text": "در برخورد با همکاران جدید:",
        "options": [
            {"label": "مستقیم و صریح هستم", "dimension": "D"},
            {"label": "خیلی زود صمیمی می‌شوم", "dimension": "I"},
            {"label": "با احترام و آرامش برخورد می‌کنم", "dimension": "S"},
            {"label": "سعی می‌کنم دقیق و حرفه‌ای باشم", "dimension": "C"},
        ]
    },
    {
        "text": "وقتی در جلسه‌ای مخالفتی مطرح می‌شود:",
        "options": [
            {"label": "نقطه‌نظر خود را محکم بیان می‌کنم", "dimension": "D"},
            {"label": "سعی می‌کنم فضا را آرام و مثبت نگه دارم", "dimension": "I"},
            {"label": "به حرف همه گوش می‌دهم", "dimension": "S"},
            {"label": "مستند و منطقی پاسخ می‌دهم", "dimension": "C"},
        ]
    },
    {
        "text": "در پروژه‌های چندمرحله‌ای:",
        "options": [
            {"label": "مرحله به مرحله پیش می‌روم اما سریع", "dimension": "D"},
            {"label": "در هر مرحله با اعضای تیم مشورت می‌کنم", "dimension": "I"},
            {"label": "روند را آرام و منظم پیش می‌برم", "dimension": "S"},
            {"label": "برای هر مرحله مستندات دقیق تهیه می‌کنم", "dimension": "C"},
        ]
    },
    {
        "text": "در مواجهه با مسئولیت جدید:",
        "options": [
            {"label": "بلافاصله آن را می‌پذیرم و شروع می‌کنم", "dimension": "D"},
            {"label": "با دیگران در مورد آن صحبت می‌کنم", "dimension": "I"},
            {"label": "سعی می‌کنم به آرامی وارد کار شوم", "dimension": "S"},
            {"label": "ابتدا همه جزئیات را بررسی می‌کنم", "dimension": "C"},
        ]
    },
    {
        "text": "برای تعطیلات آخر هفته:",
        "options": [
            {"label": "برنامه‌ای فعال و ماجراجویانه انتخاب می‌کنم", "dimension": "D"},
            {"label": "دورهمی با دوستان را ترجیح می‌دهم", "dimension": "I"},
            {"label": "تفریح آرام مثل کتاب یا طبیعت‌گردی را ترجیح می‌دهم", "dimension": "S"},
            {"label": "برنامه‌ریزی دقیق برای همه جزئیات دارم", "dimension": "C"},
        ]
    },
    {
        "text": "در مواجهه با اشتباه دیگران:",
        "options": [
            {"label": "با قاطعیت تذکر می‌دهم", "dimension": "D"},
            {"label": "به شیوه‌ای مثبت آن را مطرح می‌کنم", "dimension": "I"},
            {"label": "سعی می‌کنم شرایط را درک کنم", "dimension": "S"},
            {"label": "جزئیات اشتباه را مستند می‌کنم", "dimension": "C"},
        ]
    },
    {
        "text": "وقتی کار جدیدی شروع می‌شود:",
        "options": [
            {"label": "فوراً وارد عمل می‌شوم", "dimension": "D"},
            {"label": "درباره آن با اشتیاق صحبت می‌کنم", "dimension": "I"},
            {"label": "با هماهنگی و صبر کار را شروع می‌کنم", "dimension": "S"},
            {"label": "ابتدا مراحل را بررسی و تحلیل می‌کنم", "dimension": "C"},
        ]
    },
    {
        "text": "در مواجهه با فردی با نظر مخالف:",
        "options": [
            {"label": "قاطعانه از موضع خودم دفاع می‌کنم", "dimension": "D"},
            {"label": "سعی می‌کنم او را با شوخی و لبخند آرام کنم", "dimension": "I"},
            {"label": "با احترام گوش می‌دهم و نظر می‌دهم", "dimension": "S"},
            {"label": "پاسخ مستند و منطقی می‌دهم", "dimension": "C"},
        ]
    },
    {
        "text": "در شرایط بحرانی چگونه واکنش نشان می‌دهم:",
        "options": [
            {"label": "سریع کنترل اوضاع را به‌دست می‌گیرم", "dimension": "D"},
            {"label": "به دیگران امید و انگیزه می‌دهم", "dimension": "I"},
            {"label": "سعی می‌کنم آرامش را حفظ کنم", "dimension": "S"},
            {"label": "اطلاعات و قوانین مربوط را بررسی می‌کنم", "dimension": "C"},
        ]
    },
    {
        "text": "وقتی پروژه‌ای شکست می‌خورد:",
        "options": [
            {"label": "علت را بررسی کرده و راه‌حل پیشنهاد می‌دهم", "dimension": "D"},
            {"label": "تیم را به ادامه دادن تشویق می‌کنم", "dimension": "I"},
            {"label": "با همدلی از اعضای تیم حمایت می‌کنم", "dimension": "S"},
            {"label": "مستندات را تحلیل می‌کنم تا اشتباهات را بفهمم", "dimension": "C"},
        ]
    },
    {
        "text": "در شرایط عدم قطعیت:",
        "options": [
            {"label": "با جسارت تصمیم می‌گیرم", "dimension": "D"},
            {"label": "سعی می‌کنم نگرانی دیگران را کم کنم", "dimension": "I"},
            {"label": "منتظر شفاف‌تر شدن شرایط می‌مانم", "dimension": "S"},
            {"label": "اطلاعات بیشتری جمع‌آوری می‌کنم", "dimension": "C"},
        ]
    },
    {
        "text": "در شروع همکاری جدید:",
        "options": [
            {"label": "به‌سرعت مسئولیت‌ها را مشخص می‌کنم", "dimension": "D"},
            {"label": "روابط دوستانه برقرار می‌کنم", "dimension": "I"},
            {"label": "اعتمادسازی می‌کنم و صبورم", "dimension": "S"},
            {"label": "قوانین و انتظارات را دقیق بررسی می‌کنم", "dimension": "C"},
        ]
    },
    {
        "text": "در زمان تصمیم‌گیری‌های مهم:",
        "options": [
            {"label": "با قاطعیت تصمیم می‌گیرم", "dimension": "D"},
            {"label": "تأثیر آن بر دیگران را در نظر می‌گیرم", "dimension": "I"},
            {"label": "با مشورت گروهی به نتیجه می‌رسم", "dimension": "S"},
            {"label": "تمام جوانب را تحلیلی بررسی می‌کنم", "dimension": "C"},
        ]
    },
    {
        "text": "در زمان شروع کار جدید:",
        "options": [
            {"label": "سریع اقدام می‌کنم", "dimension": "D"},
            {"label": "با هیجان وارد تیم می‌شوم", "dimension": "I"},
            {"label": "سعی می‌کنم هماهنگ با محیط جدید باشم", "dimension": "S"},
            {"label": "فرآیندها و روش‌ها را یادداشت می‌کنم", "dimension": "C"},
        ]
    },
    {
        "text": "وقتی کسی عملکرد ضعیفی دارد:",
        "options": [
            {"label": "مستقیم به او بازخورد می‌دهم", "dimension": "D"},
            {"label": "با گفتار مثبت تلاشش را تحسین می‌کنم", "dimension": "I"},
            {"label": "به او کمک می‌کنم پیشرفت کند", "dimension": "S"},
            {"label": "جزئیات را بررسی می‌کنم و راهنمایی دقیق می‌دهم", "dimension": "C"},
        ]
    },
    {
        "text": "در کارهای تیمی:",
        "options": [
            {"label": "وظایف را تقسیم می‌کنم و جلو می‌برم", "dimension": "D"},
            {"label": "جو را شاد و پرانرژی نگه می‌دارم", "dimension": "I"},
            {"label": "باعث هماهنگی و همدلی می‌شوم", "dimension": "S"},
            {"label": "روی کیفیت و دقت کار تمرکز دارم", "dimension": "C"},
        ]
    },
    {
        "text": "اگر لازم باشد کاری تکراری انجام دهم:",
        "options": [
            {"label": "سریع انجام می‌دهم تا به سراغ کار بعدی بروم", "dimension": "D"},
            {"label": "سعی می‌کنم آن را سرگرم‌کننده کنم", "dimension": "I"},
            {"label": "با حوصله و نظم انجامش می‌دهم", "dimension": "S"},
            {"label": "در هر بار انجام، دقت بیشتری به خرج می‌دهم", "dimension": "C"},
        ]
    },
    {
        "text": "در صورت بروز اشتباه از جانب من:",
        "options": [
            {"label": "مسئولیت را می‌پذیرم و جبران می‌کنم", "dimension": "D"},
            {"label": "با صراحت و مهربانی عذرخواهی می‌کنم", "dimension": "I"},
            {"label": "سعی می‌کنم تنش ایجاد نکنم", "dimension": "S"},
            {"label": "علت اشتباه را دقیق تحلیل می‌کنم", "dimension": "C"},
        ]
    },
    {
        "text": "در انتخاب شغل جدید، اولویت من:",
        "options": [
            {"label": "امکان پیشرفت سریع و مسئولیت‌پذیری است", "dimension": "D"},
            {"label": "محیط کاری مثبت و اجتماعی است", "dimension": "I"},
            {"label": "ثبات شغلی و همکاری دوستانه است", "dimension": "S"},
            {"label": "شفافیت نقش‌ها و ساختار سازمانی است", "dimension": "C"},
        ]
    }
]

shuffle(questions)

# ================== هدر ==================
st.markdown('<div class="main-container animated">', unsafe_allow_html=True)
st.markdown('<h1 class="header-title">🧠 آزمون شخصیت‌شناسی DISC</h1>', unsafe_allow_html=True)
st.markdown('<p class="header-subtitle">شناخت بهتر خود برای زندگی بهتر</p>', unsafe_allow_html=True)

# ================== تایمر ==================
elapsed = int(time.time() - st.session_state.start_time)
remaining = TOTAL_TIME - elapsed
minutes = remaining // 60
seconds = remaining % 60

if remaining <= 0:
    st.markdown('<div class="timer-box">⏰ زمان شما به پایان رسید</div>', unsafe_allow_html=True)
    st.session_state.current_q = TOTAL_QUESTIONS
else:
    st.markdown(f'<div class="timer-box">⏳ زمان باقی‌مانده: {minutes:02d}:{seconds:02d}</div>', unsafe_allow_html=True)

# ================== نوار پیشرفت ==================
progress = int((st.session_state.current_q / TOTAL_QUESTIONS) * 100)
st.markdown('<div class="progress-container">', unsafe_allow_html=True)
st.markdown(f'<p style="text-align:center; font-size:1.2em; color:#667eea; font-weight:600;">پیشرفت: {progress}٪</p>', unsafe_allow_html=True)
st.progress(progress / 100)
st.markdown(f'<p style="text-align:center; color:#999;">سؤال {st.session_state.current_q} از {TOTAL_QUESTIONS}</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ================== آزمون ==================
if st.session_state.current_q < TOTAL_QUESTIONS:
    q = questions[st.session_state.current_q]
    
    # اگر پاسخ قبلی برای این سؤال وجود ندارد
    if f'most_choice_{st.session_state.current_q}' not in st.session_state:
        st.session_state[f'most_choice_{st.session_state.current_q}'] = None
    if f'least_choice_{st.session_state.current_q}' not in st.session_state:
        st.session_state[f'least_choice_{st.session_state.current_q}'] = None

    st.markdown('<div class="question-card animated">', unsafe_allow_html=True)
    st.markdown(f'<p class="question-text">❓ {q["text"]}</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 💚 بیشترین شباهت")
        most = st.radio(
            "بیشترین:",
            q['options'],
            key=f"most_radio_{st.session_state.current_q}",
            format_func=lambda x: x['label'],
            index=None
        )

    with col2:
        st.markdown("### 💔 کمترین شباهت")
        least = st.radio(
            "کمترین:",
            q['options'],
            key=f"least_radio_{st.session_state.current_q}",
            format_func=lambda x: x['label'],
            index=None
        )

    st.markdown('</div>', unsafe_allow_html=True)

    # دکمه با کلید یکتا بر اساس شماره سؤال
    if st.button("⬅️ سؤال بعد", key=f"next_btn_{st.session_state.current_q}"):
        if most is None or least is None:
            st.error("⚠️ لطفاً گزینه‌های هر دو بخش را انتخاب کنید.")
        elif most == least:
            st.error("⚠️ گزینه‌های بیشترین و کمترین نباید یکسان باشند.")
        else:
            # ذخیره فقط هنگام کلیک
            st.session_state[f'most_choice_{st.session_state.current_q}'] = most
            st.session_state[f'least_choice_{st.session_state.current_q}'] = least

            st.session_state.responses.append({
                "most": most['dimension'],
                "least": least['dimension']
            })
            st.session_state.current_q += 1
            st.rerun()

    
    # دریافت انتخاب‌های ذخیره شده
    saved_most = st.session_state[f'most_choice_{st.session_state.current_q}']
    saved_least = st.session_state[f'least_choice_{st.session_state.current_q}']
    
    if st.button("⬅️ سؤال بعد"):
        if saved_most is None or saved_least is None:
            st.error("⚠️ لطفاً گزینه‌های هر دو بخش را انتخاب کنید.")
        elif saved_most == saved_least:
            st.error("⚠️ گزینه‌های بیشترین و کمترین نباید یکسان باشند.")
        else:
            st.session_state.responses.append({"most": saved_most['dimension'], "least": saved_least['dimension']})
            st.session_state.current_q += 1
            st.rerun()

# ================== تحلیل نهایی ==================
if st.session_state.current_q >= TOTAL_QUESTIONS and not st.session_state.submitted:
    st.session_state.submitted = True
    
    scores = {'D': 0, 'I': 0, 'S': 0, 'C': 0}
    for resp in st.session_state.responses:
        scores[resp['most']] += 1
        scores[resp['least']] -= 1
    
    raw = scores.copy()
    max_raw = max(raw.values())
    min_raw = min(raw.values())
    norm = {k: int(round(1 + 6 * (v - min_raw) / (max_raw - min_raw))) if max_raw != min_raw else 4 for k, v in raw.items()}
    four_digit = f"{norm['D']}{norm['I']}{norm['S']}{norm['C']}"
    
    sorted_dims = sorted(norm.items(), key=lambda x: x[1], reverse=True)
    dominant, dom_score = sorted_dims[0]
    second, sec_score = sorted_dims[1]
    
    if dom_score >= 7:
        disc_type = f"High {dominant}"
    elif dom_score >= 6 and sec_score >= 5:
        disc_type = f"High {dominant}{second}"
    elif dom_score >= 5 and sec_score >= 5:
        disc_type = f"{dominant}{second}"
    else:
        disc_type = dominant
    
    # ================== نمایش نتایج ==================
    st.markdown('<div class="result-card animated">', unsafe_allow_html=True)
    st.markdown('<h2 style="text-align:center; color:#2c3e50; font-size:2.5em;">🎉 نتایج آزمون شما</h2>', unsafe_allow_html=True)
    
    st.markdown(f'''
    <div style="text-align:center; margin:30px 0;">
        <p style="font-size:1.5em; color:#666; margin-bottom:20px;">کد شخصیتی DISC شما:</p>
        <div>
            <span class="disc-badge badge-d">D: {norm['D']}</span>
            <span class="disc-badge badge-i">I: {norm['I']}</span>
            <span class="disc-badge badge-s">S: {norm['S']}</span>
            <span class="disc-badge badge-c">C: {norm['C']}</span>
        </div>
        <p style="font-size:3em; font-weight:700; color:#667eea; margin:20px 0;">{four_digit}</p>
        <p style="font-size:2em; font-weight:600; color:#764ba2;">تیپ شخصیتی: {disc_type}</p>
    </div>
    ''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ================== نمودار ==================
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[norm['D'], norm['I'], norm['S'], norm['C']],
        theta=['قاطعیت (D)', 'تأثیرگذاری (I)', 'ثبات (S)', 'وظیفه‌شناسی (C)'],
        fill='toself',
        name='پروفایل شما',
        line=dict(color='#667eea', width=3),
        fillcolor='rgba(102, 126, 234, 0.3)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 7],
                showticklabels=True,
                ticks='outside',
                tickfont=dict(size=14, family='Vazirmatn')
            ),
            angularaxis=dict(
                tickfont=dict(size=16, family='Vazirmatn')
            )
        ),
        showlegend=False,
        title=dict(
            text='نمودار شخصیتی DISC شما',
            font=dict(size=24, family='Vazirmatn'),
            x=0.5,
            xanchor='center'
        ),
        font=dict(family='Vazirmatn'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ================== تفسیر تیپ ==================
    disc_interpretations = {
        "High D": {
            "title": "🔴 قاطع و رهبر",
            "desc": "شما فردی بسیار قاطع، جاه‌طلب و نتیجه‌محور هستید. تصمیم‌گیری سریع و کنترل محیط از ویژگی‌های برجسته شماست.",
            "strengths": ["رهبری قوی", "تصمیم‌گیری سریع", "ریسک‌پذیری", "هدف‌گرایی"],
            "challenges": ["صبر و شکیبایی", "توجه به احساسات دیگران", "گوش دادن فعال"],
            "jobs": ["مدیر اجرایی", "کارآفرین", "مدیر پروژه", "مدیر فروش"]
        },
        "High I": {
            "title": "🟡 اجتماعی و الهام‌بخش",
            "desc": "شما فردی بسیار اجتماعی، خوش‌بین و تأثیرگذار هستید. ایجاد ارتباط و الهام بخشیدن به دیگران از توانایی‌های برجسته شماست.",
            "strengths": ["ارتباطات عالی", "متقاعدسازی", "خلاقیت", "انگیزه‌بخشی"],
            "challenges": ["تمرکز بر جزئیات", "مدیریت زمان", "پیگیری وظایف"],
            "jobs": ["فروش و بازاریابی", "روابط عمومی", "مربیگری", "سخنرانی"]
        },
        "High S": {
            "title": "🟢 باثبات و حمایتگر",
            "desc": "شما فردی صبور، قابل اعتماد و حمایتگر هستید. ایجاد ثبات و هماهنگی در تیم از ویژگی‌های بارز شماست.",
            "strengths": ["کار تیمی", "وفاداری", "شنونده خوب", "صبر و حوصله"],
            "challenges": ["مقاومت به تغییر", "قاطعیت", "سرعت تصمیم‌گیری"],
            "jobs": ["مشاوره", "پشتیبانی مشتری", "منابع انسانی", "آموزش"]
        },
        "High C": {
            "title": "🔵 دقیق و تحلیلگر",
            "desc": "شما فردی دقیق، تحلیل‌گر و کیفیت‌گرا هستید. تمرکز بر جزئیات و استانداردهای بالا از ویژگی‌های منحصر به فرد شماست.",
            "strengths": ["دقت بالا", "تحلیل عمیق", "سازماندهی", "کیفیت‌گرایی"],
            "challenges": ["انعطاف‌پذیری", "سرعت تصمیم‌گیری", "روابط اجتماعی"],
            "jobs": ["برنامه‌نویس", "تحلیلگر داده", "حسابدار", "محقق"]
        },
        "DI": {
            "title": "🔥 پیشرو و الهام‌بخش",
            "desc": "ترکیبی از قاطعیت و مهارت‌های اجتماعی. شما می‌توانید هم رهبری کنید و هم دیگران را الهام بخشید.",
            "strengths": ["رهبری کاریزماتیک", "نفوذ اجتماعی", "انرژی بالا", "نوآوری"],
            "challenges": ["صبر و دقت", "پیگیری جزئیات", "گوش دادن به نقدها"],
            "jobs": ["مدیر محصول", "کارآفرین", "مدیر بازاریابی", "مشاور کسب‌وکار"]
        },
        "DC": {
            "title": "⚡ چالشگر و تحلیلگر",
            "desc": "ترکیبی از قاطعیت و دقت. شما به دنبال نتایج عالی با استانداردهای بالا هستید.",
            "strengths": ["کارایی بالا", "تحلیل استراتژیک", "حل مشکلات پیچیده", "هدف‌گرایی"],
            "challenges": ["انعطاف‌پذیری", "توجه به احساسات", "صبر با دیگران"],
            "jobs": ["مدیر پروژه فنی", "DevOps", "مهندس ارشد", "تحلیلگر سیستم"]
        },
        "IS": {
            "title": "🌟 مربی و حمایتگر",
            "desc": "ترکیبی از مهارت‌های اجتماعی و حمایتگری. شما می‌توانید دیگران را الهام بخشیده و از آن‌ها حمایت کنید.",
            "strengths": ["همدلی بالا", "ایجاد انگیزه", "کار تیمی", "ارتباطات مؤثر"],
            "challenges": ["قاطعیت", "تصمیم‌گیری سخت", "مواجهه با تعارض"],
            "jobs": ["مربی", "مشاور", "UI/UX دیزاینر", "مدیر منابع انسانی"]
        },
        "IC": {
            "title": "🎨 خلاق و دقیق",
            "desc": "ترکیبی از خلاقیت و دقت. شما می‌توانید ایده‌های نو با کیفیت بالا ارائه دهید.",
            "strengths": ["خلاقیت", "توجه به جزئیات", "ارتباطات", "کیفیت‌گرایی"],
            "challenges": ["مدیریت زمان", "تصمیم‌گیری سریع", "اولویت‌بندی"],
            "jobs": ["طراح گرافیک", "معمار", "تولید محتوا", "برنامه‌نویس فرانت‌اند"]
        },
        "SD": {
            "title": "🧭 هدایتگر باثبات",
            "desc": "ترکیبی از ثبات و قاطعیت. شما می‌توانید با برنامه‌ریزی دقیق به اهداف برسید.",
            "strengths": ["برنامه‌ریزی استراتژیک", "پایداری", "مسئولیت‌پذیری", "تعهد"],
            "challenges": ["انعطاف‌پذیری", "سرعت بالا", "تغییرات سریع"],
            "jobs": ["مدیر عملیات", "مدیر اجرایی", "مدیر پروژه", "سرپرست تیم"]
        },
        "SC": {
            "title": "📋 متخصص باثبات",
            "desc": "ترکیبی از دقت و ثبات. شما در انجام کارهای تخصصی با کیفیت بالا عالی هستید.",
            "strengths": ["تخصص فنی", "قابل اعتماد", "دقت", "سازماندهی"],
            "challenges": ["انعطاف‌پذیری", "ارتباطات اجتماعی", "سرعت تصمیم‌گیری"],
            "jobs": ["برنامه‌نویس", "تحلیلگر داده", "حسابدار", "مهندس کیفیت"]
        },
        "CS": {
            "title": "🔬 متخصص تحلیلگر",
            "desc": "ترکیبی از دقت بالا و ثبات. شما در کارهای تخصصی که نیاز به تحلیل دارند عالی هستید.",
            "strengths": ["تحلیل عمیق", "تخصص", "دقت", "صبر و حوصله"],
            "challenges": ["ارتباطات", "سرعت", "انعطاف‌پذیری"],
            "jobs": ["محقق", "دانشمند داده", "برنامه‌نویس بک‌اند", "تحلیلگر امنیت"]
        }
    }
    
    # پیدا کردن نزدیک‌ترین تفسیر
    interpretation = disc_interpretations.get(disc_type, disc_interpretations.get(f"High {dominant}", disc_interpretations["High D"]))
    
    st.markdown('<div class="feature-box animated">', unsafe_allow_html=True)
    st.markdown(f'<h3 class="feature-title">{interpretation["title"]}</h3>', unsafe_allow_html=True)
    st.markdown(f'<p class="feature-content">{interpretation["desc"]}</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="feature-box animated">', unsafe_allow_html=True)
        st.markdown('<h3 class="feature-title">💪 نقاط قوت</h3>', unsafe_allow_html=True)
        for strength in interpretation["strengths"]:
            st.markdown(f'<p class="feature-content">✓ {strength}</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="feature-box animated">', unsafe_allow_html=True)
        st.markdown('<h3 class="feature-title">🎯 زمینه‌های رشد</h3>', unsafe_allow_html=True)
        for challenge in interpretation["challenges"]:
            st.markdown(f'<p class="feature-content">→ {challenge}</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="feature-box animated">', unsafe_allow_html=True)
    st.markdown('<h3 class="feature-title">💼 مشاغل پیشنهادی</h3>', unsafe_allow_html=True)
    jobs_html = " • ".join(interpretation["jobs"])
    st.markdown(f'<p class="feature-content" style="font-size:1.2em;">{jobs_html}</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # دکمه شروع مجدد
    if st.button("🔄 شروع مجدد آزمون"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ================== سایدبار تست سریع ==================
with st.sidebar:
    st.markdown("## 🧪 تست سریع")
    st.markdown("برای توسعه‌دهندگان:")
    
    test_type = st.selectbox("انتخاب تیپ:", [
        "High D", "High I", "High S", "High C",
        "DI", "DC", "IS", "IC", "SD", "SC", "CS"
    ])
    
    if st.button("🔁 اجرای تست"):
        simulated = []
        
        if test_type == "High D":
            simulated = [{"most": "D", "least": "S"}] * 20 + [{"most": "D", "least": "C"}] * 4
        elif test_type == "High I":
            simulated = [{"most": "I", "least": "C"}] * 20 + [{"most": "I", "least": "D"}] * 4
        elif test_type == "High S":
            simulated = [{"most": "S", "least": "D"}] * 20 + [{"most": "S", "least": "I"}] * 4
        elif test_type == "High C":
            simulated = [{"most": "C", "least": "I"}] * 20 + [{"most": "C", "least": "D"}] * 4
        elif test_type == "DI":
            simulated = [{"most": "D", "least": "C"}] * 12 + [{"most": "I", "least": "S"}] * 12
        elif test_type == "DC":
            simulated = [{"most": "D", "least": "I"}] * 12 + [{"most": "C", "least": "S"}] * 12
        elif test_type == "IS":
            simulated = [{"most": "I", "least": "D"}] * 12 + [{"most": "S", "least": "C"}] * 12
        elif test_type == "IC":
            simulated = [{"most": "I", "least": "S"}] * 12 + [{"most": "C", "least": "D"}] * 12
        elif test_type == "SD":
            simulated = [{"most": "S", "least": "I"}] * 12 + [{"most": "D", "least": "C"}] * 12
        elif test_type == "SC":
            simulated = [{"most": "S", "least": "D"}] * 12 + [{"most": "C", "least": "I"}] * 12
        elif test_type == "CS":
            simulated = [{"most": "C", "least": "I"}] * 12 + [{"most": "S", "least": "D"}] * 12
        
        st.session_state.responses = simulated
        st.session_state.current_q = TOTAL_QUESTIONS
        st.rerun()


