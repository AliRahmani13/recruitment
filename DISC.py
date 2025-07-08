# DISC Test App - Streamlit Version (24 questions - Persian)

import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import base64

# Initialize session state
if 'responses' not in st.session_state:
    st.session_state.responses = []
    st.session_state.current_q = 0

# Questions list (24 Persian DISC questions)
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
    }
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

# Scoring dictionary
scores = {"D": 0, "I": 0, "S": 0, "C": 0}

# Render one question at a time
q_index = st.session_state.current_q
if q_index < len(questions):
    st.subheader(f"سؤال {q_index + 1} از {len(questions)}")
    q = questions[q_index]
    st.write(q["text"])

    most = st.radio("بیشترین شباهت به من دارد:", q["options"], key=f"most_{q_index}", format_func=lambda x: x["label"])
    least = st.radio("کمترین شباهت به من دارد:", q["options"], key=f"least_{q_index}", format_func=lambda x: x["label"])

    if st.button("ثبت و رفتن به سؤال بعد"):
        if most == least:
            st.warning("لطفاً گزینه‌های متفاوت برای بیشترین و کمترین انتخاب کنید.")
        else:
            st.session_state.responses.append({"most": most["dimension"], "least": least["dimension"]})
            st.session_state.current_q += 1
            st.experimental_rerun()

# Process results
if q_index >= len(questions):
    for resp in st.session_state.responses:
        scores[resp["most"]] += 1
        scores[resp["least"]] -= 1

    # Normalize
    total = sum([abs(v) for v in scores.values()])
    perc = {k: int((v / total) * 100) if total != 0 else 0 for k, v in scores.items()}

    st.subheader("نتایج آزمون DISC شما:")
    df = pd.DataFrame.from_dict(perc, orient='index', columns=['Score'])
    st.dataframe(df)
    fig = px.bar(df, x=df.index, y='Score', title="DISC Dimensions")
    st.plotly_chart(fig)

    # Determine personality type
    sorted_traits = sorted(perc.items(), key=lambda x: x[1], reverse=True)
    disc_type = sorted_traits[0][0] + (sorted_traits[1][0] if sorted_traits[1][1] > 25 else "")
    st.markdown(f"### Your DISC Type: **{disc_type}**")

    # Generate PDF
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, 'DISC Personality Test Result', ln=True, align='C')

    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f'DISC Type: {disc_type}', ln=True)
    for k, v in perc.items():
        pdf.cell(0, 10, f'{k}: {v}%', ln=True)

    pdf_file = f"disc_result.pdf"
    pdf.output(pdf_file)
    
    with open(pdf_file, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="disc_result.pdf">📄 دانلود گزارش PDF</a>'
        st.markdown(href, unsafe_allow_html=True)

    st.success("آزمون کامل شد! می‌توانید فایل PDF نتیجه را دانلود کنید.")
