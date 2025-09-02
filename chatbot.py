import streamlit as st
import fitz  # PyMuPDF
import json
import os
import re
from datetime import datetime
import pandas as pd
from google.generativeai import types as genai_types
import google.generativeai as genai
from pathlib import Path

# --- Global Configurations & Constants ---
PROXY_URL = os.getenv("APP_HTTP_PROXY", "http://172.16.217.234:33525")
if PROXY_URL:
    os.environ['HTTP_PROXY'] = PROXY_URL
    os.environ['HTTPS_PROXY'] = PROXY_URL

# --- CORRECTED API KEY HANDLING ---
# The API key is now assigned directly to the variable.
# This is the simplest way to get the application running for testing.
GEMINI_API_KEY = "AIzaSyBEZ9d7p008FjBDcw_bLWL-328AX7rAng0"

DEFAULT_REQUEST_OPTIONS = {
    "generation_config": {
        "temperature": 0.6,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 1024
    }
}

JOB_PROFILES = {
    "کارشناس تحلیلگر داده": "job_analysis_01",
    "کارشناس تحقیق و توسعه سامانه ها": "job_rnd_01",
    "کارشناس تحقیق و توسعه": "job_research_01",
    "توسعه راهکارهای مبتنی بر هوش مصنوعی": "job_ai_01",
    "توسعه راهکارهای تحلیل اطلاعات مکانی": "job_spatial_01"
}
DOWNLOADS_DIR_NAME = "chatbotResult_v3"
DEFAULT_USER_NAME = "کاربر محترم"
MAX_DYNAMIC_QUESTIONS = os.getenv("MAX_DYNAMIC_QUESTIONS", 7)
SALARY_THRESHOLD = 60000000

# --- Helper Functions ---

def configure_api():
    """
    Configures the Google Generative AI client with the API key.
    Reads the key from the global variable 'GEMINI_API_KEY'.
    Returns True on success, False on failure.
    """
    if GEMINI_API_KEY and len(GEMINI_API_KEY) > 30: # Basic check for a valid-looking key
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            # st.success("✅ پیکربندی API با موفقیت انجام شد.") # Optional: uncomment for successful confirmation
            return True
        except Exception as e:
            st.error(f"❌ خطای پیکربندی API: کلید وارد شده نامعتبر به نظر می‌رسد. {e}")
            return False
    else:
        st.error("❌ کلید API (GEMINI_API_KEY) در کد تنظیم نشده یا نامعتبر است.")
        st.markdown("لطفاً یک کلید معتبر در خط ۲۱ فایل کد وارد کنید.")
        return False

def generate_screening_question(q_id: str, resume_text: str) -> str:
    if q_id == "salary":
        salary, _ = extract_salary_range(resume_text)
        if salary:
            return f"در رزومه شما حقوق درخواستی «{salary}» ثبت شده. درسته؟ همچنین لطفاً حداقل حقوق مدنظرتان را هم بنویسید."
        return "حقوق درخواستی شما در رزومه ذکر نشده. حدود حداقلی مدنظرتان را بفرمایید."
    elif q_id == "military":
        status = extract_military_status(resume_text)
        if status:
            return f"در رزومه نوشته شده وضعیت نظام وظیفه شما «{status}» است. اگر درسته تأیید بفرمایید، وگرنه اصلاح کنید."
        return "لطفاً وضعیت نظام وظیفه خود را مشخص کنید (مثلاً: پایان خدمت، معافیت، مشمول و...)"
    elif q_id == "availability":
        level = extract_education_level(resume_text)
        student = extract_student_status(resume_text)
        parts = []
        if level: parts.append(f"مدرک تحصیلی: «{level}»")
        if student: parts.append(f"وضعیت دانشجویی: «{student}»")
        if parts:
            return "در رزومه " + " و ".join(parts) + " آمده است. اگر صحیح است تأیید کنید و اگر توضیح بیشتری هست بفرمایید."
        return "لطفاً وضعیت تحصیلی و تعداد روزهایی که می‌توانید در هفته حضور داشته باشید را بنویسید."
    return "لطفاً پاسخ این سوال را بفرمایید."

def extract_salary_range(resume_text: str) -> tuple[str | None, str]:
    match = re.search(r'(\d{1,3}(?:[,،]?\d{3})*)\s*(?:تا|-|~)\s*(\d{1,3}(?:[,،]?\d{3})*)\s*(?:تومان|ريال)?', resume_text)
    if match:
        min_val = match.group(1).replace(',', '').replace('،', '')
        max_val = match.group(2).replace(',', '').replace('،', '')
        return f"{int(min_val):,} تا {int(max_val):,} تومان", ""
    return None, "در رزومه ذکر نشده."

def extract_military_status(resume_text: str) -> str | None:
    options = ["پایان خدمت", "معافیت", "مشمول", "در حال خدمت", "امریه"]
    for opt in options:
        if opt in resume_text: return opt
    return None

def extract_education_level(resume_text: str) -> str | None:
    for degree in ["دیپلم", "فوق دیپلم", "کاردانی", "کارشناسی", "کارشناسی ارشد", "دکتری"]:
        if degree in resume_text: return degree
    return None

def extract_student_status(resume_text: str) -> str | None:
    if "دانشجو" in resume_text:
        presence_match = re.search(r"(?:\d{1,2})\s*(?:روز|ساعت)", resume_text)
        return presence_match.group(0) if presence_match else "اطلاعات ناقص"
    return None

def extract_age(resume_text: str) -> str | None:
    match = re.search(r"(?:سن\s*[:\-]?\s*)(\d{2})", resume_text)
    return match.group(1) if match else None

def extract_structured_response(text: str, default_feedback: str = "متشکرم.", default_question: str = None) -> dict:
    json_text = ""
    try:
        code_block_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, re.DOTALL)
        if code_block_match: json_text = code_block_match.group(1)
        else:
            object_match = re.search(r"(\{[\s\S]*?\})", text, re.DOTALL)
            if object_match: json_text = object_match.group(1)
            else:
                if len(text.splitlines()) <= 2 and "?" in text: return {"feedback": None, "next_question": text.strip()}
                return {"feedback": text.strip(), "next_question": default_question, "error": "Non-JSON response"}

        if not json_text: return {"feedback": text.strip() if text.strip() else default_feedback, "next_question": default_question, "error":"Empty JSON extracted"}
        parsed_json = json.loads(json_text)
        if not isinstance(parsed_json, dict): return {"feedback": f"پاسخ غیرمنتظره: {str(parsed_json)}", "next_question": default_question, "error":"JSON is not a dict"}

        feedback = parsed_json.get("feedback")
        next_q = parsed_json.get("next_question")

        if next_q is None and not parsed_json.get("end_interview"):
            return {"feedback": feedback or default_feedback, "next_question": None, "error": "LLM provided null next_question without ending interview.", "end_interview": True}

        return {"feedback": feedback, "next_question": next_q, "end_interview": parsed_json.get("end_interview", False)}
    except Exception as e:
        return {"feedback": f"خطا در پردازش پاسخ (ساختار مورد انتظار: JSON): {str(e)[:100]}...", "next_question": default_question, "error": f"Exception: {str(e)}", "end_interview": True}

def clean_excel_text(text) -> str:
    text_str = str(text) if isinstance(text, (list, dict)) else str(text)
    return ''.join(c for c in text_str if c.isprintable())

def extract_name_from_resume(resume_text: str) -> str:
    lines = resume_text.strip().splitlines()
    if not lines:
        return DEFAULT_USER_NAME

    for line in lines[:5]:
        clean_line = line.strip()
        if 3 < len(clean_line) < 40 and all(c.isalpha() or c.isspace() or c in "آابپتثجچحخدذرزسشصضطظعغفقکگلمنوهی‌ " for c in clean_line):
            return clean_line
    return DEFAULT_USER_NAME

FIXED_SCREENING_QUESTIONS = [
    {"id": "salary", "text": "حقوق درخواستی مد نظر شما برای این موقعیت شغلی حدوداً چقدر است؟ (به تومان)"},
    {"id": "availability", "text": "آیا در حال حاضر دانشجو هستید؟ در صورت مثبت بودن، لطفاً در مورد وضعیت تحصیلی و میزان ساعت حضور در هفته که امکان همکاری دارید، توضیح دهید."},
    {"id": "military", "text": "وضعیت نظام وظیفه شما چگونه است؟ (پایان خدمت، معافیت دائم، معافیت تحصیلی، در حال خدمت، مشمول و غیره)"}
]

def initialize_session_state():
    defaults = {
        "user_name": DEFAULT_USER_NAME, "user_id": None,
        "resume_text": "", "selected_job": None, "selected_job_id": None,
        "interview_stage": "initial_setup",
        "conversation_history": [],
        "screening_questions_list": FIXED_SCREENING_QUESTIONS.copy(),
        "current_screening_q_idx": 0,
        "screening_answers": [],
        "screening_passed": None,
        "dynamic_question_count": 0,
        "max_dynamic_questions": int(MAX_DYNAMIC_QUESTIONS),
        "ai_is_processing": False,
        "screening_conversation": [],
        "current_screening_question": None,
        "awaiting_screening_answer": False

    }
    for key, value in defaults.items():
        if key not in st.session_state: st.session_state[key] = value

def reset_for_new_interview():
    current_user_name = st.session_state.get("user_name", DEFAULT_USER_NAME)
    st.session_state.clear(); initialize_session_state()
    if current_user_name != DEFAULT_USER_NAME: st.session_state.user_name = current_user_name

def process_uploaded_file(uploaded_file_obj) -> str:
    if not uploaded_file_obj: return ""
    if uploaded_file_obj.size == 0: st.warning("⚠️ فایل آپلود شده خالی است."); return ""
    text_content = ""
    try:
        if uploaded_file_obj.name.endswith(".txt"): text_content = uploaded_file_obj.read().decode("utf-8")
        elif uploaded_file_obj.name.endswith(".pdf"):
            doc = fitz.open(stream=uploaded_file_obj.read(), filetype="pdf")
            for page in doc: text_content += page.get_text("text")
            if not text_content.strip() and doc.page_count > 0: st.warning("⚠️ رزومه PDF پردازش نشد (ممکن است اسکن شده باشد).")
        return text_content.strip()
    except Exception as e: st.error(f"❌ خطا در پردازش فایل رزومه: {e}")
    return ""

def run_initial_screening(answers_list: list) -> tuple[bool, str]:
    salary_answer_text = ""; availability_answer_text = ""; military_answer_text = ""
    for item in answers_list:
        q_id = item['question_id']; ans_text = item['answer'].lower()
        if q_id == "salary": salary_answer_text = ans_text
        elif q_id == "availability": availability_answer_text = ans_text
        elif q_id == "military": military_answer_text = ans_text
    try:
        salary_numbers = [int(s) for s in re.findall(r'\d+', salary_answer_text.replace(',', '').replace('تومان','').strip())]
        if salary_numbers and max(salary_numbers) > SALARY_THRESHOLD:
            return False, f"با سپاس، فعلاً شرایط همکاری با حقوق درخواستی شما (بیش از {SALARY_THRESHOLD:,} تومان) فراهم نیست."
    except: pass
    if "دانشجو هستم" in availability_answer_text or "دانشجوام" in availability_answer_text:
        if any(word in availability_answer_text for word in ["سه روز", "چهار روز", "بیشتر از دو", "محدودیت زیاد", "نمی‌توانم تمام وقت", "نصف روز"]):
            return False, "با سپاس، فعلاً امکان همکاری با توجه به محدودیت حضور شما (دانشجویی) فراهم نیست."
    if any(word in military_answer_text for word in ["امریه", "مشمول", "سربازم", "در حال خدمت", "سربازی نرفتم"]):
        resume_lower = st.session_state.get("resume_text", "").lower()
        if not any(exc in resume_lower for exc in ["پایان خدمت", "معافیت دائم", "معافیت پزشکی"]):
            return False, "با سپاس، متاسفانه شرکت امکان جذب نیروی امریه یا مشمول را ندارد."
    return True, "غربالگری اولیه با موفقیت انجام شد. به مرحله بعدی گفتگوی تخصصی‌تر می‌رویم."

def get_next_ai_turn(conversation_history, resume_text, job_profile, user_name) -> dict:
    st.session_state.ai_is_processing = True
    persona_definition = f"""
    شما نماینده‌ی رسمی شرکت «داده‌پردازان بنیان آوا» هستید. وظیفه‌ی شما انجام یک مصاحبه حرفه‌ای منابع انسانی با جناب {user_name} برای موقعیت شغلی «{job_profile}» می‌باشد.
    این مصاحبه با تمرکز بر ارزیابی مهارت‌های نرم و شایستگی‌های رفتاری نامبرده انجام می‌گیرد.
    شما باید مصاحبه را به شکلی روان، محترمانه، انسانی و همدلانه پیش ببرید تا شناخت دقیقی از ویژگی‌های فردی، نگرش‌ها، توانمندی‌ها و سبک تعامل ایشان به‌دست آورید.

    شما نه‌تنها مصاحبه‌گر هستید، بلکه نقش ناظر منابع انسانی را نیز بر عهده دارید و باید هر مرحله از گفتگو را با دقت تحلیل و هدایت کنید.
    از کلمات فنی و ادبی مناسب استفاده کنید و در برخورد با کاربر، احترام، دقت، و رفتار حرفه‌ای را حفظ نمایید.
    """
    core_instructions = """\
وظایف شما در هر نوبت گفتگو:
1.  **تحلیل پاسخ قبلی:** پاسخ آخر کاربر را به دقت تحلیل کنید. (اگر اولین سوال شما پس از غربالگری است، از این مرحله صرف نظر کرده و مستقیماً به طرح سوال بروید).
2.  **ارائه بازخورد (کوتاه و طبیعی):** یک بازخورد کوتاه، دوستانه و مرتبط به پاسخ کاربر بدهید. مثلاً: "متوجه شدم."، "نکته جالبی بود."، "ممنون از توضیحتون." یا تاییدی کوتاه بر محتوای پاسخ. (اگر اولین سوال پس از غربالگری است، این بخش را با یک جمله خوشامدگویی و معرفی شروع گفتگو جایگزین کنید، مثلا: "عالی بود که از مرحله غربالگری عبور کردید! حالا می‌خواهیم کمی عمیق‌تر در مورد تجربیات و رویکردهای شما صحبت کنیم.").
3.  **طرح سوال بعدی (هوشمندانه و عمیق):**
    * یک سوال باز و مرتبط با پاسخ قبلی کاربر یا جنبه‌ای جدید از مهارت‌های نرم او طراحی کنید. سوالات باید به گونه‌ای باشند که کاربر را به فکر وادار کرده و او را تشویق به ارائه مثال‌های واقعی از تجربیاتش کند.
    * **مهارت‌های نرم کلیدی برای ارزیابی (متناسب با شغل '{job_profile}'):** تمرکز بر روی (اما نه محدود به):
        * **حل مسئله و تفکر انتقادی:** نحوه مواجهه با چالش‌ها، تحلیل موقعیت، تصمیم‌گیری.
        * **مهارت‌های ارتباطی:** وضوح کلام، فن بیان، شنیدن فعال، همدلی.
        * **کار تیمی و همکاری:** تجربیات کار با دیگران، مدیریت تعارض، نقش در تیم.
        * **انطباق‌پذیری و مدیریت تغییر:** واکنش به شرایط جدید، انعطاف‌پذیری.
        * **ابتکار و خودانگیختگی:** مسئولیت‌پذیری، ارائه راهکار، اشتیاق به بهبود.
        * **مدیریت استرس و تاب‌آوری:** نحوه برخورد با فشار و شکست.
        * **یادگیری و کنجکاوی:** تمایل به رشد، یادگیری از بازخورد.
        * **اخلاق حرفه‌ای و مسئولیت‌پذیری:** تعهد به کار، صداقت.
    * از پرسیدن سوالات تکراری یا سوالاتی که پاسخ کوتاه "بله/خیر" دارند، اکیداً خودداری کنید.
    * لحن شما باید حرفه‌ای، بسیار دوستانه، کنجکاو، همدلانه و روانشناسانه باشد. نام کاربر ({user_name}) را گاهی در صحبت‌های خود به کار ببرید.
محدودیت‌ها و نحوه پایان دادن:
* تعداد کل سوالات پویا در این بخش ({st.session_state.max_dynamic_questions - st.session_state.dynamic_question_count} سوال دیگر باقی مانده). شما تصمیم می‌گیرید چه زمانی اطلاعات کافی برای ارزیابی اولیه کسب کرده‌اید.
* اگر تشخیص دادید که به اندازه کافی اطلاعات کسب شده یا به سقف سوالات رسیده‌اید، مصاحبه این بخش را با یک پیام تشکر مناسب پایان دهید.
خروجی الزامی (فرمت JSON دقیقاً به این شکل):
```json
{{
  "feedback": "بازخورد شما در اینجا یا null اگر اولین سوال پس از غربالگری است",
  "next_question": "سوال بعدی شما در اینجا، یا null اگر مصاحبه این بخش تمام شده باشد",
  "end_interview": false
}}
```
مثال برای اولین سوال پس از غربالگری: {{"feedback": "خب {user_name} عزیز، از اینکه تا این مرحله همراه ما بودید ممنونم. حالا می‌خواهیم کمی عمیق‌تر در مورد تجربیات و نحوه رویکرد شما به مسائل صحبت کنیم.", "next_question": "برای شروع، می‌توانید یکی از چالش‌برانگیزترین پروژه‌هایی که در آن نقش کلیدی داشتید را توصیف کنید و بگویید چگونه با موانع آن مقابله کردید؟", "end_interview": false}}
مثال برای ادامه گفتگو: {{"feedback": "درک می‌کنم که مدیریت ذینفعان در آن پروژه چقدر می‌توانسته پیچیده باشه.", "next_question": "حالا اگر در موقعیتی قرار بگیرید که با یکی از همکارانتان اختلاف نظر جدی در مورد نحوه انجام یک کار داشته باشید، معمولاً چگونه این مسئله را مدیریت می‌کنید؟", "end_interview": false}}
مثال برای پایان دادن: {{"feedback": "از پاسخ‌های کامل و شفاف شما بسیار سپاسگزارم {user_name}. اطلاعات خوبی به دست آوردم و به نظرم تصویر روشنی از شما پیدا کردم.", "next_question": null, "end_interview": true}}
"""
    resume_summary = ("خلاصه رزومه کاربر:\n" + resume_text[:1500] + "...\n" if resume_text else "کاربر رزومه‌ای ارائه نکرده است.\n")
    history_for_prompt = []
    if conversation_history and conversation_history[0]["speaker"] == "ai" and conversation_history[0].get("question","").endswith("شروع کنیم؟"):
        entry = conversation_history[0]; feedback_text = entry.get('feedback','') or ""; question_text = entry.get('question','') or ""
        history_for_prompt.append(f" (مصاحبه‌گر): {feedback_text} {question_text}".strip())
    for entry in conversation_history[1:]:
        speaker_tag = f"{user_name} (کاربر)" if entry["speaker"] == "user" else " (مصاحبه‌گر)"
        content = "";
        if entry["speaker"] == "user": content = entry.get("content", "")
        else: feedback_text = entry.get('feedback','') or ""; question_text = entry.get('question','') or ""; content = f"{feedback_text} {question_text}".strip()
        history_for_prompt.append(f"{speaker_tag}: {content}")
    conversation_log_str = "\n".join(history_for_prompt)
    if not conversation_log_str and not (len(conversation_history) == 1 and conversation_history[0]["speaker"] == "ai"):
        conversation_log_str = "کاربر از مرحله غربالگری عبور کرده و این اولین سوال شما برای سنجش مهارت‌های نرم است."
    final_prompt = f"{persona_definition}\n\n{resume_summary}\nتاریخچه گفتگوی فعلی با {user_name}:\n{conversation_log_str}\n\n{core_instructions}"
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(final_prompt, **DEFAULT_REQUEST_OPTIONS) # Corrected variable name
        structured_output = extract_structured_response(response.text, default_question=None)
        if structured_output.get("error"):
            st.warning(f"خطا در پردازش پاسخ LLM: {structured_output.get('error')}.")
            if "?" in response.text and len(response.text.splitlines()) < 3 : return {"feedback": "متشکرم.", "next_question": response.text.strip(), "end_interview": False}
            return {"feedback": "مشکلی در پردازش پاسخ پیش آمد.", "next_question": None, "end_interview": True}
        if structured_output.get("end_interview") and not structured_output.get("feedback"):
            structured_output["feedback"] = f"بسیار خب {user_name} عزیز، به پایان سوالات این بخش رسیدیم. متشکرم."
        return structured_output
    except Exception as e:
        st.error(f"❌ خطا در ارتباط با API: {e}")
        return {"feedback": "متاسفانه مشکلی پیش آمد.", "next_question": None, "end_interview": True}
    finally: st.session_state.ai_is_processing = False

def display_initial_options():
    with st.container():
        st.markdown("#### لطفاً اطلاعات خود را برای شروع مصاحبه وارد کنید.")
        login_type = st.radio("انتخاب روش ورود:", ("ورود با شناسه کاربری (در صورت وجود)", "آپلود رزومه و مشخصات جدید"), key="login_type_radio", horizontal=True)
        if login_type == "ورود با شناسه کاربری (در صورت وجود)": handle_id_login_input()
        else: handle_resume_upload_input()

def load_user_from_excel(user_id: str, excel_path: str = "D:\AliRahmani\complete\recruitment.xlsx") -> dict | None:
    try:
        df = pd.read_excel(excel_path)
        df.columns = df.columns.str.strip()

        user_row = df[df['شناسه'].astype(str) == str(user_id)]
        if not user_row.empty:
            row = user_row.iloc[0]
            full_resume_text = f"""
🧾 نام و نام خانوادگی: {row.get("نام", "")} {row.get("نام خانوادگی", "")}
👤 جنسیت: {row.get("جنسیت", "")}
🎓 تحصیلات: {row.get("مقطع تحصیلی", "")} در رشته {row.get("رشته تحصیلی", "")} ({row.get("گرایش تحصیلی", "")}) از {row.get("دانشگاه محل تحصیل", "")} ({row.get("نوع دانشگاه تحصیلی", "")})
📍 محل سکونت: {row.get("محل سکونت", "")} | سن: {row.get("سن", "")} | تولد: {row.get("سال تولد", "")}
🧠 مهارت‌های نرم‌افزاری: {row.get("مهارت‌های نرم افزاری", "")}
💼 سوابق کاری: {row.get("سوابق کاری", "")}
🪖 وضعیت خدمت سربازی: {row.get("وضعیت خدمت سربازی", "")}
💬 درباره من: {row.get("درباره من", "")}
💰 حقوق درخواستی: {row.get("حداقل حقوق ماهیانه", "")} تا {row.get("حداکثر حقوق ماهیانه", "")} تومان
""".strip()

            return {
                "name": row.get("نام", DEFAULT_USER_NAME),
                "last_name": row.get("نام خانوادگی", ""),
                "gender": row.get("جنسیت", ""),
                "selected_job": row.get("موقعیت شغلی", None),
                "resume": full_resume_text
            }
        return None
    except Exception as e:
        st.error(f"❌ خطا در بارگذاری فایل اکسل یا یافتن کاربر: {e}")
        return None

def handle_id_login_input():
    user_id_input = st.text_input("🔐 شناسه کاربری شما:", key="user_id_input_main")

    if st.button("جستجو و شروع مصاحبه با شناسه", key="start_with_id_button"):
        if not user_id_input:
            st.warning("لطفاً شناسه کاربری خود را وارد کنید.")
            return

        st.session_state.user_id = user_id_input
        user_data = load_user_from_excel(user_id_input)

        if user_data and user_data.get("resume"):
            st.session_state.user_name = user_data.get("name", DEFAULT_USER_NAME)
            st.session_state.last_name = user_data.get("last_name", "")
            st.session_state.gender = user_data.get("gender", "")
            st.session_state.resume_text = user_data["resume"]
            st.session_state.selected_job = user_data.get("selected_job")

            if st.session_state.selected_job and st.session_state.selected_job in JOB_PROFILES:
                st.session_state.selected_job_id = JOB_PROFILES[st.session_state.selected_job]
            else:
                st.session_state.selected_job_id = None
                job_options = list(JOB_PROFILES.keys())
                selected_job_key = st.selectbox("لطفاً موقعیت شغلی را انتخاب کنید:", job_options, key="job_selection_id_path", index=None, placeholder="انتخاب کنید...")
                if selected_job_key:
                    st.session_state.selected_job = selected_job_key
                    st.session_state.selected_job_id = JOB_PROFILES[selected_job_key]
                else:
                    st.error("برای ادامه باید یک موقعیت شغلی انتخاب شود.")
                    return

            st.session_state.interview_stage = "initial_greeting"
            st.rerun()
        else:
            st.error(f"❌ شناسه «{user_id_input}» یافت نشد یا رزومه ناقص است.")

def handle_resume_upload_input():
    st.session_state.user_id = "resume_" + datetime.now().strftime("%Y%m%d%H%M%S")

    uploaded_file = st.file_uploader("📤 رزومه (.pdf یا .txt):", type=["pdf", "txt"], key="resume_uploader")

    job_options = list(JOB_PROFILES.keys())
    current_job_idx = job_options.index(st.session_state.selected_job) if st.session_state.selected_job in job_options else 0
    selected_job_key = st.selectbox("🧭 موقعیت شغلی:", job_options, index=current_job_idx, key="job_selection_upload", placeholder="انتخاب کنید...")

    if selected_job_key:
        st.session_state.selected_job = selected_job_key
        st.session_state.selected_job_id = JOB_PROFILES[selected_job_key]

    if uploaded_file:
        st.session_state.resume_text = process_uploaded_file(uploaded_file)
        st.session_state.user_name = extract_name_from_resume(st.session_state.resume_text)

    if st.session_state.resume_text and uploaded_file:
        st.success("✅ رزومه بارگذاری شد.")

    if st.button("🎤 شروع مصاحبه با رزومه و مشخصات", key="start_with_resume_button"):
        if not st.session_state.resume_text:
            st.warning("لطفاً یک فایل رزومه معتبر آپلود کنید.")
        elif not st.session_state.selected_job_id:
            st.warning("لطفاً یک موقعیت شغلی انتخاب کنید.")
        else:
            st.session_state.interview_stage = "initial_greeting"
            st.rerun()

def display_screening_questions():
    # This function seems to have some logical issues in the original code.
    # I've simplified it to be more robust.
    st.info("مرحله غربالگری اولیه: لطفاً به سوالات زیر پاسخ دهید.")

    # Display conversation history for this stage
    for entry in st.session_state.screening_conversation:
        with st.chat_message(entry["sender"], avatar="🤖" if entry["sender"] == "bot" else "👤"):
            st.write(entry["message"])

    # Check if all screening questions are answered
    if st.session_state.current_screening_q_idx >= len(st.session_state.screening_questions_list):
        st.session_state.interview_stage = "dynamic_soft_skill" # Move to next stage
        # You might want to run the screening check here
        passed, reason = run_initial_screening(st.session_state.screening_answers)
        st.session_state.screening_passed = passed
        if not passed:
            st.error(f"مصاحبه در این مرحله متوقف شد. دلیل: {reason}")
            st.session_state.interview_stage = "finished"
        else:
            st.success("غربالگری اولیه با موفقیت انجام شد. به مرحله بعدی می‌رویم.")
            # Add a starting message for the next stage
            st.session_state.conversation_history.append({
                "speaker": "ai",
                "feedback": "بسیار عالی!",
                "question": "از اینکه تا این مرحله همراه ما بودید ممنونم. حالا می‌خواهیم کمی عمیق‌تر در مورد تجربیات و نحوه رویکرد شما به مسائل صحبت کنیم. برای شروع، می‌توانید یکی از چالش‌برانگیزترین پروژه‌هایی که در آن نقش کلیدی داشتید را توصیف کنید و بگویید چگونه با موانع آن مقابله کردید؟"
            })
            st.session_state.dynamic_question_count += 1
        st.rerun()
        return

    # If we are not waiting for an answer, post the next question
    if not st.session_state.awaiting_screening_answer:
        q = st.session_state.screening_questions_list[st.session_state.current_screening_q_idx]
        st.session_state.current_screening_question = q
        bot_message = generate_screening_question(q['id'], st.session_state.resume_text)
        st.session_state.screening_conversation.append({"sender": "bot", "message": bot_message})
        st.session_state.awaiting_screening_answer = True
        st.rerun()

    # Get user input only if we are waiting for an answer
    if st.session_state.awaiting_screening_answer:
        user_input = st.chat_input("پاسخ شما...")
        if user_input:
            st.session_state.screening_conversation.append({"sender": "user", "message": user_input})

            # Simple validation
            if len(user_input.strip()) < 3:
                st.session_state.screening_conversation.append({
                    "sender": "bot",
                    "message": "ممنونم، ولی لطفاً پاسخ را کامل‌تر و دقیق‌تر بنویسید."
                })
                st.rerun()
                return

            # Store the answer and move to the next question
            q = st.session_state.current_screening_question
            st.session_state.screening_answers.append({
                "question_id": q["id"],
                "question_text": q["text"],
                "answer": user_input.strip()
            })
            st.session_state.current_screening_q_idx += 1
            st.session_state.awaiting_screening_answer = False
            st.rerun()

def display_interview_interface():
    current_stage = st.session_state.interview_stage
    if current_stage == "initial_greeting":
        last_name = st.session_state.user_name.strip().split()[-1]
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(
                f"""سلام آقای {last_name}، از آشنایی با شما خوشحالم!
        کمی در مورد خودم بگویم — من مصاحبه‌گر هوش مصنوعی شرکت داده پردازان بنیان آوا هستم.
        شما می‌توانید رویکرد حل مسئله خود را با من در میان بگذارید و هر وقت به مشکلی برخوردید از من سوال بپرسید.
        یادتان باشد که به برقراری ارتباط با من ادامه دهید.

        ما برای موقعیت شغلی **{st.session_state.selected_job}** با شما گفتگو خواهیم کرد."""
            )

            if st.button("🚀 ادامه و شروع سوالات اولیه", key="begin_screening_button"):
                st.session_state.interview_stage = "screening"; st.rerun()
        return
    if current_stage == "screening": display_screening_questions(); return

    if current_stage == "dynamic_soft_skill":
        for entry in st.session_state.conversation_history:
            avatar_icon = "🤖" if entry["speaker"] == "ai" else "👤"
            with st.chat_message(entry["speaker"], avatar=avatar_icon):
                if entry.get("feedback"): st.write(f"*{entry['feedback']}*")
                main_content = entry.get("question") if entry["speaker"] == "ai" else entry.get("content")
                if main_content: st.write(main_content)

        if (not st.session_state.conversation_history or st.session_state.conversation_history[-1]["speaker"] == "user") and not st.session_state.ai_is_processing:
            if st.session_state.dynamic_question_count < st.session_state.max_dynamic_questions:
                with st.spinner("کمی صبر کنید..."):
                    ai_response = get_next_ai_turn(st.session_state.conversation_history, st.session_state.resume_text, st.session_state.selected_job, st.session_state.user_name)
                ai_feedback, ai_question, is_ending = ai_response.get("feedback"), ai_response.get("next_question"), ai_response.get("end_interview", False)
                st.session_state.conversation_history.append({"speaker": "ai", "feedback": ai_feedback, "question": ai_question})
                if ai_question: st.session_state.dynamic_question_count += 1
                if is_ending or not ai_question: st.session_state.interview_stage = "final_analysis"
                st.rerun()
            else:
                st.session_state.conversation_history.append({"speaker": "ai", "feedback": "به تعداد سوالات مورد نظر برای این بخش رسیده‌ایم.", "question": "از وقتی که گذاشتید ممنونم. در حال آماده سازی تحلیل نهایی هستم."})
                st.session_state.interview_stage = "final_analysis"; st.rerun()

        if st.session_state.conversation_history and st.session_state.conversation_history[-1]["speaker"] == "ai" and \
           st.session_state.conversation_history[-1].get("question") and current_stage == "dynamic_soft_skill":
            user_answer = st.chat_input("پاسخ شما...", key=f"dynamic_ans_input_{st.session_state.dynamic_question_count}")
            if user_answer:
                st.session_state.conversation_history.append({"speaker": "user", "content": user_answer.strip()})
                st.rerun()

    elif current_stage == "final_analysis":
        with st.container():
            perform_final_analysis()
    elif current_stage == "finished":
        with st.container():
            if st.session_state.get("screening_passed", True): st.balloons()
            st.success("مصاحبه شما به پایان رسید. از وقتی که گذاشتید سپاسگزاریم!")
            offer_reset_confirmation()

def perform_final_analysis():
    st.info("در حال آماده سازی تحلیل نهایی مصاحبه شما...")
    user_id_for_file = clean_excel_text(st.session_state.get("user_id", "unknown_user"))
    history_for_prompt = []
    if st.session_state.get("screening_answers"):
        history_for_prompt.append("\n--- پاسخ به سوالات غربالگری اولیه ---")
        for sa in st.session_state.screening_answers: history_for_prompt.append(f"سوال: {sa['question_text']}\nپاسخ شما: {sa['answer']}")
        history_for_prompt.append("--- پایان بخش غربالگری ---\n")
    for e in st.session_state.conversation_history:
        actor = "شرکت داده پردازان بنیان آوا (مصاحبه‌گر)" if e['speaker'] == 'ai' else f"{st.session_state.user_name} (کاربر)"
        text = "";
        if e['speaker'] == 'ai':
            if e.get('feedback'): text += f"[بازخورد : {e['feedback']}] "
            if e.get('question'): text += e['question']
        else: text = e.get('content', '')
        history_for_prompt.append(f"{actor}: {text.strip()}")
    analysis_prompt_template = f"""
شما یک مدیر ارشد منابع انسانی در شرکت «فاما» هستید و باید یک گزارش کامل تحلیلی از کاندیدا ({st.session_state.user_name}) برای موقعیت شغلی ({st.session_state.selected_job}) ارائه دهید.
رزومه (خلاصه): {st.session_state.resume_text[:1500] + "..." if st.session_state.resume_text else "ارائه نشده"}
---
تاریخچه کامل مصاحبه (شامل سوالات غربالگری، بازخوردهای سوالات و پاسخ‌های کاربر):
{"\n".join(history_for_prompt)}
---
گزارش تحلیلی خود را در بخش‌های زیر ارائه دهید:
1.  📝 **خلاصه کلی:** (حدود ۵۰-۱۰۰ کلمه) یک پاراگراف در مورد کاندیدا و تناسب کلی او با موقعیت شغلی با توجه به مهارت‌های نرم ارزیابی شده.
2.  🧠 **تحلیل مهارت‌های نرم کلیدی:** بر اساس کل گفتگو، مهارت‌های نرم اصلی مانند حل مسئله، ارتباطات، کار تیمی، انطباق‌پذیری، ابتکار، مدیریت استرس، یادگیری و اخلاق حرفه‌ای را تحلیل کنید. برای هر مهارت، شواهد مثبت یا منفی از گفتگو ذکر کنید.
3.  🎯 **نقاط قوت اصلی:** ۳ تا ۵ نقطه قوت اصلی فرد در زمینه مهارت‌های نرم که به وضوح در مصاحبه مشاهده شد را لیست کنید.
4.  🤔 **موارد قابل تامل یا ریسک‌ها:** موارد نگران‌کننده، پاسخ‌های مبهم، یا نقاطی که نیاز به بررسی بیشتر در مصاحبه حضوری دارند را مشخص کنید.
5.  🏆 **پیشنهاد نهایی و دلیل:** به طور واضح مشخص کنید که آیا این فرد را برای مرحله بعد (مصاحبه تخصصی حضوری) پیشنهاد می‌کنید یا خیر. دلیل اصلی پیشنهاد یا عدم پیشنهاد خود را در یک یا دو جمله بیان کنید.
"""
    try:
        with st.spinner("در حال انجام تحلیل نهایی توسط هوش مصنوعی..."):
            model_analyzer = genai.GenerativeModel("gemini-2.0-flash")
            generation_config = genai.types.GenerationConfig(
                temperature=0.6,
                top_p=0.95,
                top_k=40,
                max_output_tokens=1024
            )
            response_analysis = model_analyzer.generate_content(
                analysis_prompt_template,
                generation_config=generation_config
            )
            analysis_text = response_analysis.text
        st.markdown("---"); st.markdown("### 📊 تحلیل نهایی مصاحبه:"); st.markdown(analysis_text)
        save_interview_results(user_id_for_file, analysis_text, st.session_state.screening_answers, st.session_state.conversation_history)
        st.session_state.interview_stage = "finished"; st.rerun()
    except genai_types.BlockedPromptException as e: st.error(f"❌ درخواست تحلیل توسط API مسدود شد: {e}")
    except Exception as e: st.error(f"❌ خطا در تحلیل نهایی: {e}")
    st.session_state.interview_stage = "finished"

def save_interview_results(user_id_str: str, analysis_report: str, screening_log: list, conversation_log: list):
    downloads_folder = Path.home() / "Downloads" / DOWNLOADS_DIR_NAME
    downloads_folder.mkdir(parents=True, exist_ok=True)
    general_excel_path = downloads_folder / "all_interview_results_v3.xlsx"
    data_to_save = {
        "user_id": user_id_str, "user_name": clean_excel_text(st.session_state.user_name),
        "selected_job": clean_excel_text(st.session_state.selected_job),
        "resume_summary": clean_excel_text(st.session_state.resume_text[:700] + "..." if st.session_state.resume_text else ""),
        "screening_answers": clean_excel_text(json.dumps(screening_log, ensure_ascii=False, indent=2)),
        "conversation_history": clean_excel_text(json.dumps(conversation_log, ensure_ascii=False, indent=2)),
        "full_analysis": clean_excel_text(analysis_report)
    }
    new_row_df = pd.DataFrame([data_to_save])
    try:
        df_to_save = new_row_df
        if general_excel_path.exists():
            try: existing_df = pd.read_excel(general_excel_path); df_to_save = pd.concat([existing_df, new_row_df], ignore_index=True)
            except Exception as read_err: st.warning(f"خطا در خواندن فایل اکسل موجود، فایل جدید ایجاد می‌شود: {read_err}")
        df_to_save.to_excel(general_excel_path, index=False, engine='openpyxl')
        st.success(f"✅ اطلاعات مصاحبه در '{general_excel_path.name}' (پوشه Downloads/{DOWNLOADS_DIR_NAME}) ذخیره شد.")
    except Exception as e: st.error(f"❌ خطا در ذخیره فایل Excel: {e}")
    analysis_bytes = analysis_report.encode('utf-8')
    st.download_button(label="📄 دانلود تحلیل این مصاحبه (متن)",data=analysis_bytes,
        file_name=f"analysis_{user_id_str}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", mime="text/plain")

def offer_reset_confirmation():
    if "confirm_reset" not in st.session_state: st.session_state.confirm_reset = False
    if st.button("شروع مصاحبه جدید", key="reset_initial"): st.session_state.confirm_reset = True; st.rerun()
    if st.session_state.confirm_reset:
        st.warning("**آیا مطمئن هستید؟** شروع مصاحبه جدید اطلاعات فعلی را از صفحه پاک می‌کند (اما در فایل Excel ذخیره شده است).")
        col1, col2, _ = st.columns([1,1,3])
        if col1.button("بله، پاک کن", key="reset_yes", type="primary"): reset_for_new_interview(); st.rerun()
        if col2.button("نه، منصرف شدم", key="reset_no"): st.session_state.confirm_reset = False; st.rerun()

# --- Main Application Flow ---
def main():
    st.set_page_config(
        page_title="مصاحبه‌گر هوشمند شرکت داده پردازان بنیان آوا",
        layout="centered",
        initial_sidebar_state="collapsed",
    )

    primary_color = "#2563EB"
    background_color = "#F3F4F6"
    card_background_color = "#FFFFFF"
    text_color = "#1F2937"
    button_text_color = "#FFFFFF"
    border_color_soft = "#E5E7EB"
    ai_chat_bubble_color = "#DBEAFE" # Tailwind blue-100 (Light Blue for AI)
    user_chat_bubble_color = "#E0E7FF" # Tailwind indigo-100 (Light Indigo for User)


    custom_css = f"""
    <style>
        /* --- Base Theme Application --- */
        body, .main {{
            direction: rtl;
            text-align: right;
            font-family: 'IRANSans', 'Tahoma', sans-serif !important;
            background-color: {background_color} !important;
            color: {text_color};
            line-height: 1.6; /* Improved default line height */
        }}
        .block-container {{
            direction: rtl;
            text-align: right;
            font-family: 'IRANSans', 'Tahoma', sans-serif !important;
            color: {text_color};
            max-width: 800px;
            padding: 1.5rem;
            margin: 1rem auto;
            border-radius: 0.75rem;
            background-color: {card_background_color};
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }}

        /* --- Input Fields General Styling --- */
        textarea, input, .stTextInput > div > div > input, .stTextArea > div > div > textarea {{
            font-family: 'IRANSans', 'Tahoma', sans-serif !important;
            border-radius: 0.375rem;
            border: 1px solid {border_color_soft};
            background-color: #FFFFFF;
            padding: 0.5rem 0.75rem; /* Added padding to input fields */
        }}
        textarea:focus, input:focus,
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus,
        div[data-testid="stSelectbox"] > div:focus-within {{ /* For selectbox focus */
            border-color: {primary_color} !important;
            box-shadow: 0 0 0 0.2rem {primary_color}40 !important;
            outline: none !important;
        }}

        /* Selectbox specific styling for consistency */
        div[data-testid="stSelectbox"] > div {{
            border-radius: 0.375rem;
            border: 1px solid {border_color_soft};
            background-color: #FFFFFF;
        }}
        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {{ /* Target inner part for padding */
             padding-top: 0.1rem;
             padding-bottom: 0.1rem;
        }}


        /* --- Headings --- */
        div[data-testid="stAppViewContainer"] h1 {{ /* Main page title (st.title) */
            color: {primary_color};
            text-align: center;
            padding-bottom: 0.75rem;
            margin-bottom: 1.5rem;
            font-size: 2rem; /* Slightly reduced for balance */
        }}
        .block-container h3, .block-container h4 {{
            color: {primary_color};
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
            border-bottom: 1px solid {primary_color}55;
            padding-bottom: 0.25rem;
            font-size: 1.25rem; /* Slightly larger sub-headers */
        }}

        /* --- Button Styling (General) --- */
        .stButton > button {{
            background-color: {primary_color};
            color: {button_text_color};
            border: none;
            padding: 0.5rem 1rem; /* Slightly adjusted padding */
            border-radius: 0.375rem; /* Consistent with inputs */
            font-weight: 500;
            transition: background-color 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); /* Softer shadow */
        }}
        .stButton > button:hover {{
            background-color: #1D4ED8;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); /* Lift on hover */
        }}
        .stButton > button:active {{
            background-color: #1E40AF;
            box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06); /* Inset shadow on active */
        }}

        /* --- Specific container styling for cards (if used internally) --- */
        .custom-card {{
            background-color: {card_background_color};
            padding: 1.5rem; /* More padding for internal cards */
            border-radius: 0.5rem;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -1px rgba(0,0,0,0.04); /* Softer shadow for internal cards */
            margin-bottom: 1.5rem;
        }}

        /* Progress Bar styling */
        .stProgress > div > div > div > div {{ background-color: {primary_color}; }}

        /* Radio button styling */
        .stRadio > label {{ /* The label for the radio group */
            font-size: 1.1rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
        }}
        .stRadio > div {{ /* The container for radio options */
            padding: 0.25rem;
        }}

        /* Chat input area */
        div[data-testid="stChatInputForm"] {{ /* Target the form around chat input */
            border-top: 1px solid {border_color_soft};
            padding-top: 0.75rem;
            margin-top: 0.75rem;
        }}
        div[data-testid="stChatInput"] > div > div > textarea {{
             background-color: {background_color}; /* Lighter background for chat input textarea */
             border: 1px solid {border_color_soft};
        }}
        div[data-testid="stChatInput"] {{ background-color: {card_background_color}; }} /* Ensure chat input bar matches card */

        /* --- Chat Message Styling --- */
        div[data-testid="stChatMessage"] {{ margin-bottom: 1rem; }}

        /* User messages styling */
        div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {{
            display: flex;
            flex-direction: row-reverse; /* Avatar on the right for user in RTL */
        }}
        div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) div[data-testid="stChatMessageContent"] {{
            background-color: {user_chat_bubble_color};
            border-radius: 1rem 1rem 0.25rem 1rem; /* Custom shape for user */
            padding: 0.75rem 1rem;
            max-width: 75%;
            color: {text_color};
        }}

        /* AI (assistant) messages styling */
         div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {{
            display: flex;
            flex-direction: row; /* Avatar on the left for AI in RTL (default) */
        }}
        div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) div[data-testid="stChatMessageContent"] {{
            background-color: {ai_chat_bubble_color};
            border-radius: 1rem 1rem 1rem 0.25rem; /* Custom shape for AI */
            padding: 0.75rem 1rem;
            max-width: 75%;
            color: {text_color};
        }}
        /* Avatar icon containers */
        div[data-testid="chatAvatarIcon-assistant"] > div,
        div[data-testid="chatAvatarIcon-user"] > div {{
            color: white; /* Emoji color */
            font-size: 1.5rem; /* Adjust emoji size */
        }}
        div[data-testid="stChatMessageContent"] p {{ margin-bottom: 0.25rem; line-height: 1.6; }}
        div[data-testid="stChatMessageContent"] em {{
            display: block; margin-bottom: 0.5rem;
            font-size: 0.95em; opacity: 0.9; font-style: italic;
        }}

    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

    initialize_session_state()
    # --- Main Check ---
    # Call configure_api() at the beginning. If it returns False, stop the app.
    if not configure_api():
        # The error message is already displayed inside the configure_api function
        return

    current_stage = st.session_state.interview_stage 
    if current_stage == "initial_setup": 
        st.title("🤖 به مصاحبه‌گر هوشمند شرکت داده پردازان بنیان آوا خوش آمدید") 
        st.markdown("---") 
        display_initial_options() 

        # 🧪 شبیه‌سازی کامل مصاحبه
        if st.button("🧪 شبیه‌سازی کامل مصاحبه (LLM پاسخ دهد)", key="simulate_llm_test"): 
            st.session_state.resume_text = "مهندس نرم‌افزار با ۵ سال سابقه در پروژه‌های ERP و توسعه اپلیکیشن‌های مبتنی بر هوش مصنوعی." 
            st.session_state.user_name = "محمد امینی" 
            st.session_state.selected_job = "کارشناس تحلیلگر داده" 
            st.session_state.selected_job_id = JOB_PROFILES[st.session_state.selected_job] 
            st.session_state.screening_answers = [ 
                {"question_id": "salary", "question_text": "حقوق چقدر؟", "answer": "۲۵ میلیون تومان"}, 
                {"question_id": "availability", "question_text": "دانشجویی؟", "answer": "فارغ‌التحصیل و تمام وقت"}, 
                {"question_id": "military", "question_text": "وضعیت نظام وظیفه؟", "answer": "پایان خدمت"}, 
            ] 
            st.session_state.conversation_history = [] 
            st.session_state.dynamic_question_count = 0 
            st.session_state.interview_stage = "dynamic_soft_skill" 

            def simulate_full_conversation(): 
                for _ in range(int(MAX_DYNAMIC_QUESTIONS)): 
                    ai_turn = get_next_ai_turn( 
                        st.session_state.conversation_history, 
                        st.session_state.resume_text, 
                        st.session_state.selected_job, 
                        st.session_state.user_name 
                    ) 
                    st.session_state.conversation_history.append({ 
                        "speaker": "ai", 
                        "feedback": ai_turn.get("feedback", ""), 
                        "question": ai_turn.get("next_question", "") 
                    }) 
                    if ai_turn.get("end_interview") or not ai_turn.get("next_question"): 
                        st.session_state.interview_stage = "final_analysis" 
                        break 

                    # پاسخ شبیه‌سازی‌شده توسط مدل
                    user_response = genai.GenerativeModel("gemini-2.0-flash").generate_content( 
                        f"به عنوان یک کارجوی حرفه‌ای، به این سوال پاسخ دهید: {ai_turn['next_question']}", 
                        generation_config=genai.types.GenerationConfig(temperature=0.7, max_output_tokens=256) 
                    ).text.strip() 
                    st.session_state.conversation_history.append({"speaker": "user", "content": user_response}) 
                st.session_state.interview_stage = "final_analysis"
                st.rerun()

            simulate_full_conversation()
            
                 

    elif current_stage in ["initial_greeting", "screening", "dynamic_soft_skill", "final_analysis", "finished"]:
        job_title_display = f" (برای موقعیت: {st.session_state.selected_job or 'نامشخص'})" if st.session_state.selected_job else ""
        first_name = st.session_state.user_name.strip().split()[0]
        last_name = st.session_state.user_name.strip().split()[-1]
        full_name_fixed = f"{first_name} {last_name}"

        st.title(f" مصاحبه با {full_name_fixed}{job_title_display}")
        st.markdown("---");
        display_interview_interface()
    
if __name__ == "__main__":
    main()



 