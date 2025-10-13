# DISC Test App (کامل شده با خروجی ۴ رقمی، تحلیل، تایمر و رابط راست‌چین)
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import base64
import time
from pathlib import Path

# تابع تبدیل فونت محلی به CSS
def local_font_css(font_path, font_name):  
    with open(font_path, "rb") as f:  
        encoded_font = base64.b64encode(f.read()).decode('utf-8')  
    return f"""  
    <style>  
    @font-face {{  
        font-family: '{font_name}';  
        src: url(data:font/ttf;base64,{encoded_font}) format('truetype');  
        font-weight: normal;  
        font-style: normal;  
    }}  
  
    /* تمام اجزای صفحه، به جز بخش footer */  
    html, body, * {{  
        font-family: '{font_name}' !important;  
        font-size: 22px !important;  
        direction: rtl !important;  
        text-align: right !important;  
    }}  

    /* تنظیم فونت برای تیترها */  
    h1, h2, h3, h4, h5, h6 {{  
        font-family: '{font_name}' !important;  
        font-size: 20px !important;  
        line-height: 2.2 !important;  
    }}  
  
    h1.main-title {{  
        font-family: '{font_name}' !important;  
        font-size: 52px !important;  
        color: #1a73e8 !important;  
        text-align: center !important;  
        font-weight: bold !important;  
        margin-top: 40px !important;  
        margin-bottom: 30px !important;  
    }}  
  
    /* تنظیم فونت برای دکمه‌ها و ورودی‌ها */  
    .stButton > button,  
    .stDownloadButton > button,  
    .stTextInput input,  
    .stSelectbox div,  
    .stFileUploader,  
    .stFileUploader label,  
    input, select, textarea, button {{  
        font-family: '{font_name}' !important;  
        font-size: 16px !important;  
    }}  
  
    footer {{  
        visibility: hidden;  
    }}  
    </style>  
    """


# تنظیمات صفحه و درج CSS فونت
st.set_page_config(page_title="آزمون شخصیت شناسی DISC", layout="centered")
font_css = local_font_css("0 Nazanin.TTF", "Nazanin")
st.markdown(font_css, unsafe_allow_html=True)

# متغیرهای سراسری
TOTAL_TIME = 20 * 60  # 20 دقیقه بر حسب ثانیه
TOTAL_QUESTIONS = 24

if 'start_time' not in st.session_state:
    st.session_state.start_time = time.time()
if 'responses' not in st.session_state:
    st.session_state.responses = []
    st.session_state.current_q = 0
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# سوالات DISC (پیش‌فرض: از قبل در متغیر questions موجود است)
from random import shuffle
questions = [...]  # این قسمت شامل لیست 24 سؤال فارسی از قبل است
shuffle(questions)

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

# تایمر
elapsed = int(time.time() - st.session_state.start_time)
remaining = TOTAL_TIME - elapsed
minutes = remaining // 60
seconds = remaining % 60
if remaining <= 0:
    st.warning("زمان شما به پایان رسید. آزمون به طور خودکار ثبت شد.")
    st.session_state.current_q = TOTAL_QUESTIONS
else:
    st.info(f"⏳ زمان باقی‌مانده: {minutes} دقیقه و {seconds} ثانیه")

# نوار پیشرفت
progress = int((st.session_state.current_q / TOTAL_QUESTIONS) * 100)
st.progress(progress)

# آزمون
if st.session_state.current_q < TOTAL_QUESTIONS:
    q = questions[st.session_state.current_q]
    st.markdown(f"### سؤال {st.session_state.current_q + 1}: {q['text']}")
    most = st.radio("بیشترین شباهت به من دارد:", q['options'], key=f"most_{st.session_state.current_q}", format_func=lambda x: x['label'], index=None)
    least = st.radio("کمترین شباهت به من دارد:", q['options'], key=f"least_{st.session_state.current_q}", format_func=lambda x: x['label'], index=None)
    if st.button("سؤال بعد"):
        if most is None or least is None:
            st.warning("لطفاً گزینه‌های هر دو بخش را انتخاب کنید.")
        elif most == least:
            st.warning("گزینه‌های بیشترین و کمترین نباید یکسان باشند.")
        else:
            st.session_state.responses.append({"most": most['dimension'], "least": least['dimension']})
            st.session_state.current_q += 1
            st.rerun()
# --- 🎯 تست سریع با انتخاب تیپ DISC از سایدبار ---
st.sidebar.markdown("## 🧪 تست سریع تیپ‌های DISC")

test_type = st.sidebar.selectbox("انتخاب تیپ برای تست:", [
    "High D", "High DI", "DI", "DC",
    "High I", "ID", "IS", "IC",
    "High S", "SD", "SCD", "SI",
    "High C", "CS", "CIS"
])

if st.sidebar.button("🔁 اجرای تست ساختگی"):
    simulated = []

    if test_type == "High D":
        simulated = [{"most": "D", "least": "S"}] * 20
    elif test_type == "High DI":
        simulated = [{"most": "D", "least": "S"}] * 12 + [{"most": "I", "least": "C"}] * 12
    elif test_type == "DI":
        simulated = [{"most": "D", "least": "C"}] * 12 + [{"most": "I", "least": "S"}] * 12
    elif test_type == "DC":
        simulated = [{"most": "D", "least": "I"}] * 12 + [{"most": "C", "least": "S"}] * 12
    elif test_type == "High I":
        simulated = [{"most": "I", "least": "C"}] * 20
    elif test_type == "ID":
        simulated = [{"most": "I", "least": "S"}] * 12 + [{"most": "D", "least": "C"}] * 12
    elif test_type == "IS":
        simulated = [{"most": "I", "least": "D"}] * 12 + [{"most": "S", "least": "C"}] * 12
    elif test_type == "IC":
        simulated = [{"most": "I", "least": "S"}] * 12 + [{"most": "C", "least": "D"}] * 12
    elif test_type == "High S":
        simulated = [{"most": "S", "least": "D"}] * 20
    elif test_type == "SD":
        simulated = [{"most": "S", "least": "I"}] * 12 + [{"most": "D", "least": "C"}] * 12
    elif test_type == "SCD":
        simulated = [{"most": "S", "least": "I"}] * 8 + [{"most": "C", "least": "I"}] * 8 + [{"most": "D", "least": "I"}] * 8
    elif test_type == "SI":
        simulated = [{"most": "S", "least": "C"}] * 12 + [{"most": "I", "least": "D"}] * 12
    elif test_type == "High C":
        simulated = [{"most": "C", "least": "I"}] * 20
    elif test_type == "CS":
        simulated = [{"most": "C", "least": "I"}] * 12 + [{"most": "S", "least": "D"}] * 12
    elif test_type == "CIS":
        simulated = [{"most": "C", "least": "D"}] * 8 + [{"most": "I", "least": "D"}] * 8 + [{"most": "S", "least": "D"}] * 8

    st.session_state.responses = simulated
    st.session_state.current_q = TOTAL_QUESTIONS
    st.rerun()
disc_data = {
  "disc_report": {
    "introduction": "این گزارش بر اساس مدل DISC و ترکیبات آن تهیه شده است تا 15 تیپ شخصیتی را پوشش دهد. مدل استاندارد DISC شامل 4 تیپ اصلی (D, I, S, C) است و سایر تیپ‌ها ترکیبی از این 4 سبک اصلی هستند که ویژگی‌های منحصر به فردی را ایجاد می‌کنند. این گزارش برای استفاده در تحلیل‌های شغلی و تیمی طراحی شده است.",
    "personality_types": [
      {
        "type_name": "High D (Dominance) - راهبر",
        "general_characteristics": [
          "خودمحور و نتیجه‌گرا",
          "رک و صریح",
          "پر جرات و قوی",
          "نافذ و مصمم",
          "خطرپذیر و ماجراجو",
          "عملگرا و سریع",
          "مطمئن به خود",
          "تصمیم‌گیرنده سریع و قاطع",
          "موقعیت‌طلب و جاه‌طلب",
          "منطق غالب بر احساسات",
          "کنترل‌کننده"
        ],
        "leadership_style": "دستوری, قاطع, تمرکز بر روی نتایج و اهداف, انتظار سرعت و عملکرد بالا از تیم, چالش‌برانگیز و الهام‌بخش برای رسیدن به اهداف بزرگ.",
        "challenges": "عدم صبوری, بی‌توجهی به جزئیات و احساسات دیگران, تمایل به کنترل بیش از حد, ایجاد استرس در دیگران به دلیل سرعت بالا.",
        "goals": "کسب قدرت و اختیار, رسیدن به جایگاه‌های بالا, پیروزی و موفقیت, کنترل محیط و شرایط.",
        "body_language": "دست دادن قوی و با اعتماد به نفس, تماس چشمی مستقیم و نافذ, حرکات سریع و هدفمند, بیشتر حرف می‌زند و کمتر گوش می‌کند, استفاده از جملات تأکیدی, تن صدای بالا و قاطع.",
        "needs_and_wants": "فعالیت‌های جدید و متنوع, کنترل و نظارت, فرصت برای پیشرفت, کسب شهرت و اعتبار, قدرت و اختیار, چالش‌های جدید.",
        "motivations": "رقابت, موفقیت, استقلال, رسیدن به نتایج ملموس, رهبری و قدرت.",
        "fears": "از دست دادن کنترل, شکست خوردن, سوءاستفاده دیگران از او, وابستگی به دیگران.",
        "strengths": "رهبری, تصمیم‌گیری قاطع, حل مشکلات, مدیریت بحران, ریسک‌پذیری, انرژی بالا.",
        "areas_for_improvement": "افزایش صبر و شکیبایی, توجه به نظرات و احساسات دیگران, بهبود مهارت گوش دادن, کنترل تمایل به سلطه‌جویی.",
        "positive_team_contributions": "ایجاد انگیزه برای رسیدن به اهداف, پیشبرد سریع پروژه‌ها, ارائه دیدگاه‌های قاطع و راه‌حل‌های عملی.",
        "work_style": "سریع, نتیجه‌گرا, مستقل, چندوظیفه‌ای (Multi-tasking), به دنبال چالش و مسئولیت."
      },
      {
        "type_name": "High I (Influence) - تأثیرگذار",
        "general_characteristics": [
          "اجتماعی و برون‌گرا",
          "متقاعدکننده و خوش‌بین",
          "پرانرژی و مشتاق",
          "خلاق و ایده‌پرداز",
          "روابط عمومی قوی",
          "احساسات غالب بر منطق",
          "توانایی شروع گفتگو",
          "دوست‌داشتنی و خونگرم"
        ],
        "leadership_style": "الهام‌بخش, دموکراتیک, ایجاد محیط کاری شاد و پرانرژی, تشویق خلاقیت و کار تیمی, متقاعد کردن تیم از طریق جذابیت شخصی.",
        "challenges": "بی‌توجهی به جزئیات, عدم پیگیری وظایف تا انتها, تصمیم‌گیری بر اساس احساسات, پرحرفی و سازماندهی ضعیف.",
        "goals": "محبوبیت اجتماعی, شناخته شدن, ایجاد روابط دوستانه, تأیید و تحسین از سوی دیگران.",
        "body_language": "بسیار پویا و پرانرژی, استفاده زیاد از حرکات دست, لبخند زدن, تماس چشمی دوستانه, نزدیک شدن به افراد هنگام صحبت.",
        "needs_and_wants": "محیط کاری دوستانه و اجتماعی, فرصت برای تعامل, آزادی از کنترل و جزئیات, تأیید و تشویق عمومی.",
        "motivations": "شناخته شدن, روابط اجتماعی, کار گروهی, آزادی بیان, محیط‌های شاد و مثبت.",
        "fears": "طرد شدن از سوی دیگران, عدم تأیید اجتماعی, از دست دادن نفوذ و محبوبیت.",
        "strengths": "ایجاد ارتباط, متقاعدسازی, کار تیمی, ایده‌پردازی, ایجاد انگیزه در دیگران, خوش‌بینی.",
        "areas_for_improvement": "افزایش تمرکز بر جزئیات و وظایف, مدیریت زمان, سازماندهی بهتر, واقع‌بینی بیشتر.",
        "positive_team_contributions": "بالا بردن روحیه تیم, ایجاد شبکه و ارتباطات, تسهیل طوفان فکری (Brainstorming), ارائه ایده‌های جدید.",
        "work_style": "مبتنی بر تعامل, خلاق, غیررسمی, به دنبال همکاری و مشارکت."
      },
      {
        "type_name": "High S (Steadiness) - باثبات",
        "general_characteristics": [
          "صبور و آرام",
          "شنونده خوب",
          "وفادار و قابل اعتماد",
          "حامی و مهربان",
          "مقاوم در برابر تغییرات ناگهانی",
          "متواضع و مردم‌دار",
          "عملکرد خوب در تیم",
          "آرام و سنجیده"
        ],
        "leadership_style": "حمایتی, مشارکتی, ایجاد امنیت و ثبات در تیم, تمرکز بر همکاری و هماهنگی, صبور در آموزش و توسعه اعضای تیم.",
        "challenges": "مقاومت در برابر تغییر, عدم قاطعیت, کندی در تصمیم‌گیری, پنهان کردن احساسات و مشکلات, اجتناب از تعارض.",
        "goals": "امنیت و ثبات, حفظ وضعیت موجود, کمک به دیگران, روابط پایدار و عمیق.",
        "body_language": "آرام و کنترل‌شده, حرکات ملایم, تماس چشمی مهربان, گوش دادن فعال با تکان دادن سر, حفظ فاصله راحت.",
        "needs_and_wants": "محیط کاری باثبات و قابل پیش‌بینی, قدردانی صمیمانه, امنیت شغلی, دستورالعمل‌های واضح.",
        "motivations": "کمک به دیگران, امنیت, کار در یک تیم هماهنگ, قدردانی و وفاداری.",
        "fears": "از دست دادن امنیت, تغییرات ناگهانی, ایجاد تعارض و درگیری, ناامید کردن دیگران.",
        "strengths": "همکاری تیمی, پشتیبانی, صبر و شکیبایی, مهارت گوش دادن, قابل اعتماد بودن, ایجاد هماهنگی.",
        "areas_for_improvement": "افزایش انعطاف‌پذیری در برابر تغییر, ابراز وجود و قاطعیت بیشتر, سرعت بخشیدن به تصمیم‌گیری‌ها.",
        "positive_team_contributions": "ایجاد هارمونی و ثبات در تیم, حمایت از اعضای تیم, میانجی‌گری در اختلافات.",
        "work_style": "با دقت, منظم, پیگیر, متمرکز بر یک وظیفه در یک زمان (Single-tasking), نیازمند محیطی آرام."
      },
      {
        "type_name": "High C (Conscientiousness) - وظیفه‌شناس",
        "general_characteristics": [
          "دقیق و تحلیل‌گر",
          "منظم و ساختاریافته",
          "کیفیت‌گرا و استاندارد بالا",
          "محتاط و منطقی",
          "واقع‌بین و حقیقت‌جو",
          "رسمی و درون‌گرا",
          "کمال‌گرا",
          "پیرو قوانین و مقررات"
        ],
        "leadership_style": "مبتنی بر وظیفه و کیفیت, دقیق و منظم, تصمیم‌گیری بر اساس داده‌ها و حقایق, تعیین استانداردهای بالا, تمرکز بر رویه‌ها و قوانین.",
        "challenges": "کندی در تصمیم‌گیری به دلیل تحلیل بیش از حد, انتقاد از خود و دیگران, مقاومت در برابر ایده‌های بدون پشتوانه منطقی, عدم انعطاف‌پذیری.",
        "goals": "دقت و کیفیت بالا, صحت و درستی, رسیدن به دانش و تخصص, کارایی و نظم.",
        "body_language": "رسمی و کنترل‌شده, حرکات کمتر, تماس چشمی محدود و تحلیلی, حفظ فاصله فیزیکی.",
        "needs_and_wants": "اطلاعات دقیق و کامل, استقلال کاری, زمان کافی برای تحلیل, محیط کاری منظم و ساختاریافته, اطمینان از درستی کارها.",
        "motivations": "کیفیت, دقت, منطق, حل مسائل پیچیده, پیروی از استانداردها.",
        "fears": "انتقاد از کارش, اشتباه کردن, بی‌نظمی و هرج‌ومرج, تصمیم‌گیری‌های شتاب‌زده.",
        "strengths": "تحلیل و برنامه‌ریزی, کنترل کیفیت, دقت به جزئیات, حل مسائل پیچیده, سازماندهی, تفکر منطقی.",
        "areas_for_improvement": "افزایش سرعت در تصمیم‌گیری, انعطاف‌پذیری بیشتر, تحمل اشتباهات, بهبود روابط اجتماعی.",
        "positive_team_contributions": "تضمین کیفیت و دقت, ارائه تحلیل‌های عمیق و داده‌محور, سازماندهی پروژه‌ها.",
        "work_style": "سیستماتیک, دقیق, مستقل, متمرکز بر داده و منطق."
      },
      {
        "type_name": "High DI - Achiever (نتیجه‌گرای الهام‌بخش)",
        "general_characteristics": ["جاه‌طلب", "قاطع", "متقاعدکننده", "ماجراجو", "نتیجه‌گرا و در عین حال اجتماعی"],
        "leadership_style": "کاریزماتیک و نتیجه‌گرا. تیم را برای رسیدن به اهداف بلندپروازانه بسیج می‌کند.",
        "challenges": "ممکن است بی‌صبر باشد و افرادی که سرعت کمتری دارند را نادیده بگیرد.",
        "strengths": "توانایی شروع پروژه‌های بزرگ و الهام بخشیدن به دیگران برای پیوستن به آن‌ها.",
        "work_style": "سریع, هدفمند, به دنبال نقش‌های رهبری که در آن بتواند تأثیرگذار باشد."
      },
      {
        "type_name": "ID - Persuader (متقاعدکننده)",
        "general_characteristics": ["خوش‌بین", "اجتماعی", "پرانرژی", "تأثیرگذار", "توانایی بالا در ایجاد شبکه"],
        "leadership_style": "بسیار الهام‌بخش و انگیزه‌دهنده. از طریق ایجاد روابط قوی تیم را رهبری می‌کند.",
        "challenges": "ممکن است بیش از حد خوش‌بین باشد و از جزئیات و مشکلات بالقوه غافل شود.",
        "strengths": "توانایی فوق‌العاده در فروش ایده‌ها, محصولات و ایجاد هیجان در دیگران.",
        "work_style": "مبتنی بر تعامل, به دنبال فرصت‌هایی برای ارائه و متقاعد کردن دیگران."
      },
      {
        "type_name": "IS - Coach (مربی)",
        "general_characteristics": ["حمایتگر", "خونگرم", "مشوق", "صبور", "شنونده عالی"],
        "leadership_style": "رهبر حامی که بر رشد و توسعه فردی اعضای تیم تمرکز دارد.",
        "challenges": "ممکن است در تصمیم‌گیری‌های سخت یا انتقال اخبار بد دچار مشکل شود.",
        "strengths": "ایجاد اعتماد و وفاداری در تیم, توسعه استعدادها.",
        "work_style": "مشارکتی, در محیط‌های تیمی که نیاز به همدلی و حمایت است, بهترین عملکرد را دارد."
      },
      {
        "type_name": "SI - Advisor (مشاور)",
        "general_characteristics": ["وفادار", "قابل اعتماد", "آرام", "شنونده خوب", "ارائه‌دهنده پشتیبانی عملی"],
        "leadership_style": "رهبری باثبات و قابل پیش‌بینی که امنیت و هماهنگی را در اولویت قرار می‌دهد.",
        "challenges": "مقاومت در برابر تغییرات و نیاز به زمان برای سازگاری با ایده‌های جدید.",
        "strengths": "ایجاد روابط بلندمدت و باثبات, ارائه خدمات قابل اعتماد.",
        "work_style": "منظم, پیگیر, در نقش‌هایی که نیاز به صبر و ارائه خدمات مستمر دارند, موفق است."
      },
      {
        "type_name": "SCD - Diplomat (دیپلمات)",
        "general_characteristics": ["متواضع", "دقیق", "صبور", "سیستماتیک", "آرام و با نزاکت"],
        "leadership_style": "رهبری که با ایجاد فرآیندهای پایدار و قابل اعتماد, تیم را به سمت کیفیت هدایت می‌کند.",
        "challenges": "اجتناب از تعارض و کندی در تصمیم‌گیری به دلیل نیاز به قطعیت.",
        "strengths": "تضمین کیفیت و ثبات, میانجی‌گری در اختلافات با آرامش.",
        "work_style": "با دقت, روشمند, در محیط‌های آرام و ساختاریافته بهترین عملکرد را دارد."
      },
      {
        "type_name": "CS - Specialist (متخصص)",
        "general_characteristics": ["تحلیل‌گر", "دقیق", "منظم", "مستقل", "دارای استانداردهای بالا"],
        "leadership_style": "رهبری بر اساس تخصص و دانش. با ارائه داده‌ها و منطق تیم را هدایت می‌کند.",
        "challenges": "ممکن است بیش از حد منتقد باشد و در برقراری ارتباطات اجتماعی ضعیف عمل کند.",
        "strengths": "تخصص فنی, حل مسائل پیچیده, تعهد به کیفیت و دقت.",
        "work_style": "مستقل, وظیفه‌محور, به دنبال فرصت‌هایی برای استفاده از دانش تخصصی خود."
      },
      {
        "type_name": "CIS - Questioner (پرسشگر)",
        "general_characteristics": ["شکاک", "منطقی", "تحلیل‌گر", "قاطع", "به دنبال حقایق و شواهد"],
        "leadership_style": "رهبری که وضعیت موجود را به چالش می‌کشد و به دنبال راه‌حل‌های منطقی و کارآمد است.",
        "challenges": "ممکن است به دلیل شکاکیت و انتقاد زیاد, دیگران را دلسرد کند.",
        "strengths": "ارزیابی عینی, حل مشکلات پیچیده, اطمینان از درستی تصمیمات.",
        "work_style": "تحلیلی, دقیق, در نقش‌هایی که نیاز به تفکر انتقادی و ارزیابی ریسک دارد, موفق است."
      },
      {
        "type_name": "DC - Challenger (چالشگر)",
        "general_characteristics": ["مصمم", "نتیجه‌گرا", "منطقی", "رک", "استانداردهای بالا برای خود و دیگران"],
        "leadership_style": "رهبر قدرتمند که تیم را برای دستیابی به نتایج با کیفیت بالا تحت فشار قرار می‌دهد.",
        "challenges": "ممکن است بی‌صبر, پرتوقع و نسبت به احساسات دیگران بی‌تفاوت به نظر برسد.",
        "strengths": "توانایی دستیابی به نتایج عالی در محیط‌های پرچالش, کارایی و بهره‌وری بالا.",
        "work_style": "سریع, کارآمد, در محیط‌های رقابتی که نیاز به نتایج سریع و دقیق است, بهترین عملکرد را دارد."
      },
      {
        "type_name": "IC - Energizer (انرژی‌بخش)",
        "general_characteristics": ["کاریزماتیک", "اجتماعی", "حامی", "خوش‌بین", "توانایی ایجاد انگیزه و اتحاد"],
        "leadership_style": "رهبری که با انرژی مثبت, توانایی الهام‌بخشی و حمایت از تیم, افراد را متحد می‌کند.",
        "challenges": "ممکن است از تصمیم‌گیری‌های سخت و ایجاد تعارض اجتناب کند.",
        "strengths": "ایجاد روحیه تیمی قوی, شبکه‌سازی, تشویق همکاری.",
        "work_style": "بسیار تعاملی, مناسب برای نقش‌هایی که نیاز به ایجاد انگیزه و هماهنگی تیمی دارد."
      },
      {
        "type_name": "SD - Navigator (ناوبر)",
        "general_characteristics": ["هدفمند", "باثبات", "تحلیل‌گر", "مسئولیت‌پذیر", "ترکیبی از قاطعیت و دقت"],
        "leadership_style": "رهبری که با دیدی استراتژیک, برنامه‌ریزی دقیق و اراده قوی, تیم را به سمت اهداف مشخص هدایت می‌کند.",
        "challenges": "ممکن است در برابر تغییرات سریع یا ایده‌های غیرمنتظره مقاومت نشان دهد.",
        "strengths": "برنامه‌ریزی استراتژیک, مدیریت پروژه, دستیابی به نتایج پایدار و با کیفیت.",
        "work_style": "ساختاریافته, نتیجه‌گرا, در نقش‌های مدیریتی که نیاز به برنامه‌ریزی و اجرا دارد, موفق است."
      },
    ],
    "job_suitability": {
      "برنامه_نویس": ["C", "CS (Specialist)", "SCD (Diplomat)"],
      "تحلیلگر_داده": ["C", "CS (Specialist)", "CIS (Questioner)"],
      "دیتا_ساینتیست": ["C", "CS (Specialist)", "CIS (Questioner)"],
      "مدیر_محصول": ["DI (Achiever)", "ID (Persuader)", "D"],
      "DEVOPS": ["DC (Challenger)", "D/S/C (Navigator)", "CS (Specialist)"],
      "تحلیلگر_فرایند": ["C", "SCD (Diplomat)", "CS (Specialist)"],
      "مدیر_پروژه": ["D", "D/S/C (Navigator)", "DC (Challenger)"],
      "تضمین_کیفیت": ["C", "CS (Specialist)", "SCD (Diplomat)"],
      "پشتیبانی_فنی": ["S", "SI (Advisor)", "IS (Coach)"],
      "UI/UX_کار": ["I", "IS (Coach)", "I/S/C (Collaborator)"],
      "توسعه_نرم_افزار": ["C", "CS (Specialist)", "D/S/C (Navigator)"],
      "مدیریت_شبکه_و_امنیت": ["C", "CS (Specialist)", "CIS (Questioner)"],
      "مهندس_یادگیری_ماشین": ["C", "CS (Specialist)", "CIS (Questioner)"]
    }
  }
}
# تحلیل نهایی
if st.session_state.current_q >= TOTAL_QUESTIONS and not st.session_state.submitted:
    st.session_state.submitted = True
    scores = {'D': 0, 'I': 0, 'S': 0, 'C': 0}
    for resp in st.session_state.responses:
        scores[resp['most']] += 1
        scores[resp['least']] -= 1
    # نرمال‌سازی 1 تا 7
    raw = scores.copy()
    max_raw = max(raw.values())
    min_raw = min(raw.values())
    norm = {k: int(round(1 + 6 * (v - min_raw) / (max_raw - min_raw))) if max_raw != min_raw else 4 for k, v in raw.items()}
    four_digit = f"{norm['D']}{norm['I']}{norm['S']}{norm['C']}"

    # تشخیص تیپ
    # الگوریتم تعیین تیپ ۱۵گانه DISC
    sorted_dims = sorted(norm.items(), key=lambda x: x[1], reverse=True)
    dominant, dom_score = sorted_dims[0]
    second, sec_score = sorted_dims[1]

    # تیپ نهایی بر اساس قواعد تعیین‌شده:
    if dom_score >= 7:
        disc_type = f"High {dominant}"
    elif dom_score >= 6 and sec_score >= 5:
        disc_type = f"High {dominant}{second}"
    elif dom_score >= 5 and sec_score >= 5:
        disc_type = f"{dominant}{second}"
    else:
        disc_type = dominant  # حالت fallback ساده
    # پیدا کردن داده مربوط به تیپ در disc_data
    selected_type_info = next(
        (item for item in disc_data["disc_report"]["personality_types"]
        if disc_type in item["type_name"]), None
    )

    # دیکشنری تفسیر ۱۵ تیپ DISC
    disc_descriptions = {
        "High D": "🔴 High D: فردی بسیار قاطع، جاه‌طلب، ریسک‌پذیر و نتیجه‌محور. تصمیم‌گیری سریع و گرایش به کنترل.",
        "High DI": "🔥 High DI: رهبر کاریزماتیک، همزمان قاطع و اجتماعی. هم انگیزه‌بخش است هم اهل اجرا.",
        "DI": "⚡ DI: پیش‌برنده با شور و شوق. هم جاه‌طلب است هم تعامل‌گرا. سریع اما گاهی بی‌برنامه.",
        "DC": "🔍 DC: فردی منطقی و هدایت‌گر. تصمیم‌گیری بر اساس داده و واقعیت. علاقه‌مند به بهره‌وری و دقت.",
        "High I": "🟡 High I: فردی بسیار اجتماعی، مثبت، تأثیرگذار. اهل گفتگو، ارتباط و الهام‌بخشی.",
        "ID": "🌟 ID: ترکیبی از نفوذ اجتماعی و قاطعیت. به دنبال نتایج بزرگ با ارتباطات قوی.",
        "IS": "😊 IS: فردی اجتماعی، وفادار، خوش‌اخلاق. دوست‌داشتنی در تیم و پشتیبان دیگران.",
        "IC": "🎭 IC: دارای خلاقیت و دقت هم‌زمان. خوش‌صحبت، اما علاقه‌مند به جزئیات و استانداردها.",
        "High S": "🟢 High S: فردی بسیار آرام، قابل اعتماد، شنوا و حامی. تغییرات ناگهانی را نمی‌پسندد.",
        "SD": "🧩 SD: ترکیبی از صبوری و پیش‌برندگی. رهبر آرام، اما پیگیر. حمایت‌گر ولی محکم.",
        "SCD": "🔄 SCD: فردی متعهد، آرام، ساختارمند. هم اهل همکاری است هم رعایت روندها و تحلیل.",
        "SI": "🎈 SI: فردی گرم، مهربان و قابل اعتماد. روابط اجتماعی همراه با تعهد و وفاداری.",
        "High C": "🔵 High C: تحلیل‌گر، منطقی، دقیق، ساختارمند. به استانداردهای بالا پایبند است.",
        "CS": "📐 CS: متخصص در اجراهای دقیق. متواضع، منظم و سیستم‌گرا. ترجیح می‌دهد تعارض را مدیریت کند.",
        "CIS": "🧠 CIS: فردی متفکر، ساختاریافته و وفادار. تحلیل‌گر با روحیه آرام و رفتار مؤدب."
    }


    st.markdown(f"**🔢 کد DISC شما:** `{four_digit}`  \n**🎯 تیپ شخصیتی نهایی:** `{disc_type}`")

    st.success("✅ تحلیل شخصیت شما با موفقیت انجام شد:")

    if selected_type_info:
        st.markdown("### 🧠 تحلیل دقیق تیپ شخصیتی شما:")
        
        st.markdown(f"**🏷 عنوان تیپ:** {selected_type_info['type_name']}")
        
        st.markdown("**🌟 ویژگی‌های کلی:**")
        st.markdown("<ul>" + "".join([f"<li>{trait}</li>" for trait in selected_type_info["general_characteristics"]]) + "</ul>", unsafe_allow_html=True)
        
        st.markdown(f"**👑 سبک رهبری:** {selected_type_info['leadership_style']}")
        st.markdown(f"**🚧 چالش‌ها:** {selected_type_info['challenges']}")
        st.markdown(f"**💼 سبک کاری:** {selected_type_info['work_style']}")
        st.markdown(f"**✅ نقاط قوت:** {selected_type_info['strengths']}")

        # نمایش مشاغل مناسب
        st.markdown("### 🧩 مشاغل مناسب برای تیپ شما:")

        job_map = disc_data["disc_report"]["job_suitability"]

        matching_jobs = [
            job.replace("_", " ")
            for job, types in job_map.items()
            if disc_type in types or selected_type_info["type_name"] in types
        ]

        if matching_jobs:
            st.markdown("<ul>" + "".join([f"<li>{job}</li>" for job in matching_jobs]) + "</ul>", unsafe_allow_html=True)
        else:
            st.info("🔎 شغلی به‌طور خاص برای این تیپ تعریف نشده است.")
    else:
        st.warning("❗ تفسیر کامل این تیپ فعلاً در سامانه موجود نیست.")


    # نمودار خطی
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=['D', 'I', 'S', 'C'], y=[norm['D'], norm['I'], norm['S'], norm['C']], mode='lines+markers', name='DISC'))
    fig.update_layout(title='DISC Profile (1-7 Scale)', yaxis=dict(range=[1, 7]))
    st.plotly_chart(fig, use_container_width=True)

    # --- 🎨 خروجی HTML زیبا ---
    html_result = f"""
    <div style="border: 2px solid #ddd; padding: 20px; border-radius: 15px; direction: RTL; font-family: IranSans, sans-serif; background-color: #f9f9f9;">
        <h3 style="color: #2c3e50;">🔢 کد DISC شما: <span style="color:#2980b9">{four_digit}</span></h3>
        <h3 style="color: #2c3e50;">🎯 تیپ شخصیتی نهایی: <span style="color:#16a085">{disc_type}</span></h3>
        <h4 style="color: #8e44ad; margin-top: 20px;">📘 تفسیر تیپ شخصیتی شما:</h4>
        <p style="font-size: 16px; line-height: 2;">{disc_descriptions.get(disc_type, 'تفسیر این تیپ در سامانه موجود نیست.')}</p>
    </div>
    """

    st.markdown(html_result, unsafe_allow_html=True)
