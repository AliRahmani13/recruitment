import streamlit as st
import fitz  # PyMuPDF
import requests
import json
import os
import re
from datetime import datetime
import pandas as pd
import openpyxl
from google import genai
from google.genai import types
import google.generativeai as genai
from pathlib import Path

# --- تنظیمات اولیه ---
proxy_url = "http://172.16.217.234:33525"
os.environ['HTTP_PROXY'] = proxy_url
os.environ['HTTPS_PROXY'] = proxy_url

# ================== تنظیمات API ==================
genai.configure(api_key="AIzaSyBLcYcWcytb-KAHkGg5e_9tvSoKkogAQ9s")

# --- لیست شناسنامه‌های شغلی ---
JOB_PROFILES = {
    "کارشناس تحلیلگر داده": "job_analysis_01",
    "کارشناس تحقیق و توسعه سامانه ها": "job_rnd_01",
    "کارشناس تحقیق و توسعه": "job_research_01",
    "توسعه راهکارهای مبتنی بر هوش مصنوعی": "job_ai_01",
    "توسعه راهکارهای تحلیل اطلاعات مکانی": "job_spatial_01"
}

# تابع استخراج آرایه JSON از متن

def extract_json_array(text):
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    else:
        raise ValueError("JSON array not found in the response.")

# تابع پاکسازی متن برای ذخیره در Excel

def clean_excel_text(text):
    return ''.join(c for c in text if c.isprintable())

# ========== تنظیمات صفحه ==========
st.set_page_config(page_title="تحلیل رزومه و مصاحبه", layout="centered")

# استایل راست‌چین و فونت فارسی
st.markdown("""
<style>
body, .reportview-container, .main, .block-container {
    direction: rtl;
    text-align: right;
    font-family: IRANSans, Tahoma, sans-serif;
}
</style>
""", unsafe_allow_html=True)

st.title("🤖 به جلسه مصاحبه خوش آمدید")

# ========== مدیریت وضعیت ==========
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""

if "interview_mode" not in st.session_state:
    st.session_state.interview_mode = False

if "interview_questions" not in st.session_state:
    st.session_state.interview_questions = []

if "current_question" not in st.session_state:
    st.session_state.current_question = 0

if "answers" not in st.session_state:
    st.session_state.answers = []

if "user_id" not in st.session_state:
    st.session_state.user_id = "unknown"

# ============ شناسه یا رزومه ============
st.markdown("#### لطفاً شناسه خود را وارد کنید یا در صورت نداشتن، رزومه آپلود نمایید.")

user_id = st.text_input("🔐 شناسه کاربری شما:")
st.session_state.user_id = user_id
no_id = st.checkbox("شناسه ندارم، می‌خواهم رزومه آپلود کنم")

if not no_id:
    if user_id and st.button("🎤 شروع مصاحبه"):
        try:
            with open("data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            if user_id in data:
                st.session_state.resume_text = data[user_id]["resume"]
                st.session_state.interview_mode = True
            else:
                st.error("❌ شناسه یافت نشد.")
        except:
            st.error("⚠️ خطا در خواندن فایل اطلاعات.")
else:
    uploaded_file = st.file_uploader("📤 لطفاً رزومه خود را آپلود کنید (.pdf یا .txt)", type=["pdf", "txt"])
    job_options = list(JOB_PROFILES.keys())

    selected_job = st.selectbox("🧭 لطفاً یکی از موقعیت‌های شغلی زیر را انتخاب نمایید:", job_options)
    st.session_state.selected_job = selected_job
    st.session_state.selected_job_id = JOB_PROFILES[selected_job]

    if uploaded_file:
        text = ""
        if uploaded_file.name.endswith(".txt"):
            text = uploaded_file.read().decode("utf-8")
        elif uploaded_file.name.endswith(".pdf"):
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            for page in doc:
                text += page.get_text()
        st.session_state.resume_text = text
        st.success("✅ رزومه با موفقیت بارگذاری شد.")
        if st.button("🎤 شروع مصاحبه"):
            st.session_state.interview_mode = True

# ========== مصاحبه ==========
if st.session_state.interview_mode:
    if not st.session_state.interview_questions:
        with st.spinner("در حال آماده‌سازی سوالات مصاحبه بر اساس رزومه و موقعیت شغلی..."):
            iq_prompt = f"""
            با توجه به رزومه زیر و موقعیت شغلی انتخاب‌شده ({st.session_state.get('selected_job', 'نامشخص')}):

            - اگر فرد خانم باشد یا وضعیت سربازی او "اتمام خدمت" یا "معاف دائم" باشد، سوالی درباره خدمت سربازی نپرس.
            - اگر فرد آقا و دارای معافیت تحصیلی باشد، سوالی بپرس با مضمون: "برنامه‌تان برای سربازی چیست؟ (قصد امریه یا پروژه نخبگی و ... دارید؟)"
            - اگر فرد دانشجو است، سوالاتی بپرس با مضمون:
              "در هفته چند ساعت امکان حضور در محل کار را ندارید؟ این وضعیت تا چه زمانی ادامه دارد؟ چند واحد درسی باقی‌مانده دارید؟"
            - اگر فرد فارغ‌التحصیل است، بپرس که "آیا قصد ادامه تحصیل دارید؟"
            - ۳ سوال روانشناختی یا عمومی برای سنجش شخصیت و مهارت‌های نرم شامل چالش در کار تیمی یا برخورد با مدیر
            - فقط یک سوال تحلیلی بپرس که نیاز به عدد و سپس استدلال دارد (مثل مصرف شکر یا وزن کامیون یا سوالات خلاقانه مشابه)
            - ۳ سوال فنی و تخصصی دقیق مرتبط با موقعیت شغلی انتخاب‌شده طراحی کن بر اساس شرح شغل و مهارت‌های تخصصی مورد نیاز آن

            خروجی باید آرایه‌ای از سوالات باشد و هر سوال دارای فیلد زیر باشد:
            - question

            رزومه:
            {st.session_state.resume_text}
            """

            try:
                model = genai.GenerativeModel("gemini-2.0-flash")
                response = model.generate_content(iq_prompt)

                questions_json = response.text
                try:
                    parsed = extract_json_array(questions_json)
                    st.session_state.interview_questions = parsed
                except Exception as e:
                    st.error(f"❌ خطا در تبدیل متن به JSON: {e}")
                    st.write(questions_json)
                    st.stop()
            except Exception as e:
                st.error(f"❌ خطا در تولید سوالات مصاحبه: {e}")

    if st.session_state.interview_questions:
        q_idx = st.session_state.current_question
        if q_idx < len(st.session_state.interview_questions):
            q = st.session_state.interview_questions[q_idx]["question"]
            st.markdown(f"### ❓ سوال {q_idx + 1}: {q}")
            user_answer = st.text_input("✍️ پاسخ شما:", key=f"answer_{q_idx}")

            if st.button("➡️ ثبت پاسخ", key=f"submit_{q_idx}"):
                st.session_state.answers.append({"question": q, "answer": user_answer})
                st.session_state.current_question += 1
        else:
            st.success("🎉 مصاحبه به پایان رسید. در حال تحلیل پاسخ‌ها و رزومه شما هستیم...")

            summary = "\n\n".join([f"سوال: {a['question']}\nپاسخ: {a['answer']}" for a in st.session_state.answers])
            
            # ✅ This is the fixed final_prompt that was missing
            final_prompt = f"""
            شما یک تحلیلگر منابع انسانی هستید.
            با توجه به رزومه، موقعیت شغلی انتخاب شده و پاسخ‌های فرد به سوالات مصاحبه، یک تحلیل کامل ارائه دهید.

            موقعیت شغلی: {st.session_state.get('selected_job', 'نامشخص')}

            رزومه:
            {st.session_state.resume_text}

            سوالات و پاسخ‌های مصاحبه:
            {summary}

            ---
            تحلیل خود را در چند بخش ارائه دهید:
            1.  📝 خلاصه کلی از فرد و تناسب او با شغل.
            2.  🔧 تحلیل مهارت‌های فنی و تخصصی.
            3.  🧠 تحلیل مهارت‌های نرم و جنبه‌های شخصیتی (بر اساس سوالات روانشناختی).
            4.  🎯 نقاط قوت اصلی.
            5.  📌 نقاط ضعف یا مواردی که نیاز به بررسی بیشتر دارد.
            6.  🏆 پیشنهاد نهایی (مثلاً: پیشنهاد برای مصاحبه حضوری، مناسب برای موقعیت، رد).
            """

            try:
        # تحلیل پاسخ‌ها
                model = genai.GenerativeModel("gemini-1.5-pro")
                response = model.generate_content(final_prompt)
                analysis = response.text


            # ذخیره در فایل
                downloads_folder = Path.home() / "Downloads" / "chatbotResult"
                downloads_folder.mkdir(parents=True, exist_ok=True)

                excel_path = downloads_folder / "results.xlsx"

                if os.path.exists(excel_path):
                    df = pd.read_excel(excel_path)
                else:
                    df = pd.DataFrame(columns=["user_id", "resume_text", "selected_job", "answers", "full_analysis"])

                def format_full_analysis(raw_text):
                    lines = raw_text.split("\n")
                    formatted_lines = []
                    for line in lines:
                        if any(line.strip().startswith(tag) for tag in ["📝", "🔧", "💼", "🎓", "🧠", "🎯", "📌", "✅", "🏆"]):
                            formatted_lines.append(f"**{line.strip()}**")
                        else:
                            formatted_lines.append(line.strip())
                    return "\n".join(formatted_lines)

                new_row = {
                    "user_id": clean_excel_text(st.session_state.get("user_id", "unknown")),
                    "selected_job": clean_excel_text(st.session_state.get("selected_job", "نامشخص")),
                    "resume_text": clean_excel_text(st.session_state.resume_text),
                    "answers": clean_excel_text(json.dumps(st.session_state.answers, ensure_ascii=False)),
                    "full_analysis": clean_excel_text(format_full_analysis(analysis))
                }

                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_excel(excel_path, index=False)

                st.success("✅ اطلاعات برای شرکت ارسال شد و نتیجه به زودی به شما اطلاع رسانی میگردد.")

            except Exception as e:
                st.error(f"❌ خطا در تحلیل نهایی یا ذخیره فایل: {e}")
