import streamlit as st
import pandas as pd
import os
from google.generativeai import types as genai_types
import google.generativeai as genai
import requests
from pathlib import Path
import base64

def local_font_css(font_path, font_name="BNazanin"):
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

    html, body, [class*="css"], label, h1, h2, h3, h4, h5, h6, p, div, span {{
        font-family: '{font_name}', Tahoma, sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
        font-size: 20px !important;
    }}

    .qnum {{
        display: inline-block;
        min-width: 36px;
        text-align: center;
        color: #fff;
        background: #228be6;
        border-radius: 30px;
        margin-left: 12px;
        font-size: 30px;
        font-weight: bold;
        box-shadow: 1px 1px 4px #cce7ff;
        font-family: '{font_name}' !important;
    }}
    </style>
    """

PDFSHIFT_API_KEY = "sk_314d5016e37848b36847307c7135d14f6909173d"

# === حتماً اولین دستور بعد از import ها ===
st.set_page_config(
    page_title="آزمون کلیفتون - فارسی",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- تنظیم پراکسی در صورت نیاز ----------
PROXY_URL = os.getenv("APP_HTTP_PROXY", "http://172.16.217.234:33525")
if PROXY_URL:
    os.environ['HTTP_PROXY'] = PROXY_URL
    os.environ['HTTPS_PROXY'] = PROXY_URL

font_css = local_font_css("D:/AliRahmani/fonts/0 Nazanin.TTF", "BNazanin")
st.markdown(font_css, unsafe_allow_html=True)


# ---------- کلید Gemini ----------
GEMINI_API_KEY = "AIzaSyBEZ9d7p008FjBDcw_bLWL-328AX7rAng0"

# ---------- بارگذاری داده‌ها ----------
@st.cache_data
def load_questions():
    df = pd.read_csv("clifton_questions_cleaned.csv")
    return df

questions_df = load_questions()

# ---------- تیتر و توضیح ----------
st.markdown("""
<h1 style='font-size: 32px; color:#222; font-family: BNazanin;'>🧠 آزمون نقاط قوت کلیفتون (CliftonStrengths)</h1>
<p style='font-size: 22px; font-family: BNazanin;'>به هر جمله از -۲ (کاملاً مخالفم) تا +۲ (کاملاً موافقم) پاسخ دهید.</p>
""", unsafe_allow_html=True)


# ---------- گزینه‌ها با اعداد فارسی ----------
options = [-2, -1, 0, 1, 2]
option_labels = ['-۲', '-۱', '۰', '۱', '۲']

# ---------- ذخیره پاسخ‌ها در session_state ----------
if "responses" not in st.session_state:
    st.session_state.responses = {}

# ---------- نمایش سوالات راست‌چین و مرتب ----------
for i, row in questions_df.iterrows():
    question_number = i + 1
    st.session_state.responses[row["question_id"]] = st.radio(
        label=f"**{question_number}.** {row['question_text']}",   # اینجا کاما
        options=options,
        format_func=lambda x: option_labels[options.index(x)],
        index=2,
        key=f"q_{row['question_id']}"
    )

# ---------- ساخت پرامپت برای Gemini ----------
def generate_gemini_prompt(top_5_factors):
     prompt = f"""
شما نقش یک روانشناس و تحلیل‌گر ارشد استعدادهای انسانی را دارید و باید برای نتایج یک آزمون کلیفتون (CliftonStrengths) گزارش تهیه کنید.

🔹 پنج نقطه قوت برتر این فرد عبارتند از:
{"، ".join(top_5_factors)}

"""
def generate_gemini_prompt(top_5_factors, worst_5_factors=None):
    prompt = f"""
شما نقش یک روانشناس و تحلیل‌گر ارشد استعدادهای انسانی را دارید و باید برای نتایج یک آزمون کلیفتون (CliftonStrengths) گزارش تهیه کنید.

🔹 پنج نقطه قوت برتر این فرد عبارتند از:
{"، ".join(top_5_factors)}

"""
    if worst_5_factors:
        prompt += f"🔸 پنج نقطه ضعف (یا کم‌استعدادترین زمینه‌ها) فرد نیز به ترتیب زیر است:\n{'، '.join(worst_5_factors)}\n"
    prompt += """
گزارش خروجی باید ساختاری دقیق، تحلیلی و بسیار حرفه‌ای داشته باشد، به گونه‌ای که:
- اول، حوزه (Domain) هر نقطه قوت و ضعف را شناسایی و ذکر کنید (از بین حوزه‌های: استراتژیک، اجرایی، ارتباطی، تأثیرگذار).
- برای هر حوزه، یک توضیح رنگی و جداگانه بدهید و جمع‌بندی آن حوزه را بر اساس نقاط قوت و ضعف شخص بنویس.
- برای هر نقطه قوت:
    * نام فارسی و انگلیسی توانمندی را بنویس.
    * توضیح روان‌شناختی تحلیلی و مفصل، نه فقط توصیف ساده.
    * کاربردها و توصیه‌های شغلی، تحصیلی و شخصی مرتبط با آن قوت.
    * پیشنهادات برای رشد بیشتر و تبدیل آن به برتری رقابتی.
- برای هر نقطه ضعف نیز:
    * نام فارسی و انگلیسی آن را بنویس.
    * توضیح روان‌شناختی ضعف یا زمینه کم‌استعداد و تأثیر آن بر رفتار فرد.
    * پیشنهادات علمی و راهبردی برای مدیریت یا بهبود این نقاط ضعف.
- نقاط قوت و ضعف را کاملاً از هم جدا و دسته‌بندی کن و برای هر گروه رنگ و سبک جداگانه در خروجی رعایت کن (استایل Markdown یا HTML).
- در پایان، یک جمع‌بندی شخصی‌سازی‌شده درباره پتانسیل‌ها و اولویت‌های رشدی این فرد، متناسب با الگوی قوت و ضعفش، اضافه کن.

نکته مهم: لحن کاملاً حرفه‌ای، تحلیلی، علمی و انگیزشی باشد. 
از ذکر جملات کلیشه‌ای یا ترجمه ماشینی پرهیز کن و جملات خروجی کاملاً شبیه کارنامه رسمی و دقیق بنویس.

# مثال قالب مورد انتظار:
۱. **حوزه استراتژیک:**  
توضیح درباره این حوزه و تاثیر نقاط قوت مربوطه...

۲. **نقطه قوت اول:**  
نام: "آینده‌نگر" (Futuristic)  
توضیح روان‌شناختی مفصل...  
پیشنهادات شغلی و توسعه فردی...

۳. **نقطه ضعف اول:**  
نام: "ایده‌آل‌گرا" (Maximizer)  
توضیح روان‌شناختی...  
راهبردهای بهبود و مدیریت...

در انتها: جمع‌بندی و توصیه‌های شخصی‌سازی‌شده (اختصاصی این فرد).

# توجه:  
گزارش خروجی باید کامل، مفصل، و از نظر ساختار و گرافیک (Markdown یا HTML) مشابه نمونه کارنامه‌های رسمی سنجمان و کلیفتون باشد و هر حوزه یا بخش، جدا و رنگی باشد.
    """
    return prompt

# ---------- تحلیل با Gemini ----------
def analyze_with_gemini(prompt, model="models/gemini-1.5-flash"):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(model)
    response = model.generate_content(prompt)
    return response.text.strip()

def html_template(top_5, worst_5, analysis, talent_fa):
    html = f"""
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ direction: rtl; font-family: Tahoma, IRANSans, Arial; background: #fcfcfc; color:#222; }}
            .section {{ background:#f5faff; border-radius:14px; margin:20px 0; padding:18px; border:1.5px solid #a0cfd6; }}
            .score-list {{ font-size:17px; }}
            .score-list span.fa {{ color: #0a7286; font-weight:bold; }}
            .score-list span.en {{ color: #888; font-size:15px; margin-left:6px; }}
        </style>
    </head>
    <body>
        <div class="section">
            <b>پنج نقطه قوت برتر شما:</b>
            <ul class="score-list">
                {''.join([f"<li>{i+1}. <span class='fa'>{talent_fa.get(f, f)}</span> (<span class='en'>{f}</span>) — امتیاز: {s}</li>" for i,(f,s) in enumerate(top_5)])}
            </ul>
        </div>
        <div class="section">
            <b>پنج نقطه ضعف (کم‌استعدادترین):</b>
            <ul class="score-list">
                {''.join([f"<li>{i+1}. <span class='fa'>{talent_fa.get(f, f)}</span> (<span class='en'>{f}</span>) — امتیاز: {s}</li>" for i,(f,s) in enumerate(worst_5)])}
            </ul>
        </div>
        <div class="section">{analysis}</div>
    </body>
    </html>
    """
    return html

def generate_pdf_from_html(html_content):
    response = requests.post(
        'https://api.pdfshift.io/v3/convert/pdf',
        auth=(PDFSHIFT_API_KEY, "sk_314d5016e37848b36847307c7135d14f6909173d"),
        json={
            "source": html_content,
            "landscape": False,
            "use_print": True,
        }
    )
    if response.status_code == 200:
        return response.content
    else:
        st.error(f"خطا در ساخت PDF. وضعیت: {response.status_code}")
        return None


# ---------- دکمه تحلیل نتایج ----------
if st.button("🔍 تحلیل نتایج", use_container_width=True):
    factor_scores = {}
    for i, row in questions_df.iterrows():
        factor = row["factor"]
        score = st.session_state.responses[row["question_id"]]
        factor_scores[factor] = factor_scores.get(factor, 0) + score

    sorted_factors = sorted(factor_scores.items(), key=lambda x: x[1], reverse=True)
    top_5 = [factor for factor, _ in sorted_factors[:5]]
    worst_5 = [factor for factor, _ in sorted_factors[-5:]]

    st.subheader("💡 پنج نقطه قوت برتر شما:")
    for i, (factor, score) in enumerate(sorted_factors[:5], 1):
        st.write(f"{i}. {factor}  —  امتیاز: {score}")

    st.subheader("🟠 پنج نقطه ضعف (زمینه کم‌استعداد):")
    for i, (factor, score) in enumerate(sorted_factors[-5:], 1):
        st.write(f"{i}. {factor}  —  امتیاز: {score}")

    prompt = generate_gemini_prompt(top_5, worst_5)

    with st.spinner("در حال تولید تحلیل ..."):
        try:
            analysis = analyze_with_gemini(prompt)
            st.markdown(analysis, unsafe_allow_html=True)

        # دیکشنری کامل ترجمه استعدادها را اینجا تعریف کن
            talent_fa = {
                "belief": "اعتقاد",
                "positivity": "مثبت‌گرا",
                "command": "قاطعیت",
                "restorative": "ترمیم‌گر",
                "individualization": "فردنگر",
                "input": "درون‌دادگرا",
                "arranger": "هماهنگ‌کننده",
                "maximizer": "کمال‌گرا",
                "analytical": "تحلیلی",
                "harmony": "هماهنگی"
                # ... (کاملش کن!)
            }

            top_5_list = [(factor, score) for factor, score in sorted_factors[:5]]
            worst_5_list = [(factor, score) for factor, score in sorted_factors[-5:]]

            html_report = html_template(top_5_list, worst_5_list, analysis, talent_fa)

            pdf_data = generate_pdf_from_html(html_report)
            if pdf_data:
                st.download_button(
                    label="📥 دانلود PDF تحلیل",
                    data=pdf_data,
                    file_name="clifton_report.pdf",
                    mime="application/pdf"
                )

        except Exception as e:
            st.error(f"❌ خطا در ارتباط با Gemini: {e}")
