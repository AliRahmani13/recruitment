import streamlit as st
import fitz  # PyMuPDF
import json
import os
import re
from pathlib import Path
import pandas as pd
import google.generativeai as genai

# --- تنظیمات اولیه ---
# اطمینان حاصل کنید که پراکسی شما در صورت نیاز به درستی تنظیم شده است
proxy_url = "http://172.16.217.234:33525"
os.environ['HTTP_PROXY'] = proxy_url
os.environ['HTTPS_PROXY'] = proxy_url

# ================== تنظیمات API ==================
# کلید API خود را اینجا قرار دهید
genai.configure(api_key="AIzaSyBLcYcWcytb-KAHkGg5e_9tvSoKkogAQ9s")

# --- لیست شناسنامه‌های شغلی ---
JOB_PROFILES = {
    "کارشناس تحلیلگر داده": "job_analysis_01",
    "کارشناس تحقیق و توسعه سامانه ها": "job_rnd_01",
    "کارشناس تحقیق و توسعه": "job_research_01",
    "توسعه راهکارهای مبتنی بر هوش مصنوعی": "job_ai_01",
    "توسعه راهکارهای تحلیل اطلاعات مکانی": "job_spatial_01"
}

# --- توابع کمکی ---
def extract_json_array(text):
    # این تابع برای استخراج یک آرایه JSON از پاسخ مدل طراحی شده است
    # برای جلوگیری از خطا در صورتی که مدل متن اضافی ارسال کند
    text = text.strip()
    match = re.search(r"```json\s*(\[.*\])\s*```", text, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        match = re.search(r"(\[.*\])", text, re.DOTALL)
        if match:
            json_str = match.group(0)
        else:
            raise ValueError("JSON array not found in the response.")
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to decode JSON: {e}\nResponse text was: {json_str}")


def clean_excel_text(text):
    return ''.join(c for c in str(text) if c.isprintable())

# ========== تنظیمات صفحه ==========
st.set_page_config(page_title="تحلیل رزومه و مصاحبه", layout="centered")

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

# ========== مدیریت وضعیت چند مرحله‌ای ==========
if "interview_mode" not in st.session_state:
    st.session_state.interview_mode = False
if "interview_stage" not in st.session_state:
    st.session_state.interview_stage = "part1_general" # مراحل: part1_general, part2_psychological, part3_technical, final_analysis, finished
if "screening_passed" not in st.session_state:
    st.session_state.screening_passed = None

# متغیرهای مربوط به هر مرحله
if "questions" not in st.session_state:
    st.session_state.questions = []
if "current_q_idx" not in st.session_state:
    st.session_state.current_q_idx = 0
if "answers" not in st.session_state:
    st.session_state.answers = []

if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "user_id" not in st.session_state:
    st.session_state.user_id = "unknown"
current_stage = st.session_state.get("interview_stage", "part1_general")


# ============ بخش ورودی کاربر (رزومه یا شناسه) ============
if not st.session_state.interview_mode:
    st.markdown("#### لطفاً شناسه خود را وارد کنید یا در صورت نداشتن، رزومه آپلود نمایید.")
    user_id = st.text_input("🔐 شناسه کاربری شما:")
    st.session_state.user_id = user_id
    no_id = st.checkbox("شناسه ندارم، می‌خواهم رزومه آپلود کنم")

    if no_id:
        uploaded_file = st.file_uploader("📤 لطفاً رزومه خود را آپلود کنید (.pdf یا .txt)", type=["pdf", "txt"])
        job_options = list(JOB_PROFILES.keys())
        selected_job = st.selectbox("🧭 لطفاً یکی از موقعیت‌های شغلی زیر را انتخاب نمایید:", job_options)
        
        if uploaded_file and selected_job:
            st.session_state.selected_job = selected_job
            st.session_state.selected_job_id = JOB_PROFILES[selected_job]
            text = ""
            if uploaded_file.name.endswith(".txt"):
                text = uploaded_file.read().decode("utf-8")
            elif uploaded_file.name.endswith(".pdf"):
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                for page in doc:
                    text += page.get_text()
            st.session_state.resume_text = text
            st.text_area("📄 رزومه استخراج‌شده:", value=text, height=200)
            st.success("✅ رزومه با موفقیت بارگذاری شد.")
            if st.button("🎤 شروع مصاحبه"):
                st.session_state.interview_mode = True
                st.rerun()
                st.write("🔄 حالت مصاحبه فعال شد.")

# ========== تابع غربالگری اولیه ==========
def run_initial_screening(answers):
    """
    این تابع پاسخ‌های مرحله اول را برای شرایط کلیدی بررسی می‌کند.
    """
    # این یک پیاده‌سازی ساده است. می‌توان آن را با تحلیل هوشمندتر جایگزین کرد.
    salary_answer = ""
    availability_answer = ""
    military_answer = ""

    for item in answers:
        q = item['question']
        a = item['answer'].lower()
        if "حقوق" in q:
            salary_answer = a
        elif "دانشجو" in q or "حضور" in q:
            availability_answer = a
        elif "سربازی" in q:
            military_answer = a
    
    # شرط حقوق: استخراج عدد از پاسخ
    try:
        salary_numbers = [int(s) for s in re.findall(r'\d+', salary_answer)]
        if salary_numbers and max(salary_numbers) > 60000000:
            return False, "با سپاس از شما، در حال حاضر شرایط همکاری با توجه به حقوق درخواستی شما فراهم نمی‌باشد."
    except:
        pass # اگر پاسخی نبود یا عدد نداشت، رد نمی‌کنیم

    # شرط دانشجویی: اگر کلمه "بیشتر از دو روز" یا "سه روز" و ... بود
    if any(word in availability_answer for word in ["سه روز", "چهار روز", "بیشتر از دو"]):
        return False, "با سپاس از شما، در حال حاضر امکان همکاری با توجه به محدودیت حضور شما فراهم نمی‌باشد."

    # شرط سربازی: اگر به دنبال امریه بود یا مشمول بود
    if any(word in military_answer for word in ["امریه", "مشمول هستم", "دنبال امریه"]):
        return False, "با سپاس از شما، متاسفانه در حال حاضر شرکت امکان جذب نیروی امریه یا مشمول را ندارد."
        
    return True, "غربالگری اولیه با موفقیت انجام شد."


# ========== موتور اصلی مصاحبه ==========
if st.session_state.interview_mode:

    # --- تابع تولید سوالات ---
    def generate_questions(stage, resume_text, job_title, past_answers=None):
        prompt = ""
        if stage == "part1_general":
            prompt = f"""
            شما یک متخصص منابع انسانی هستید. وظیفه شما پرسیدن سوالات اولیه و عمومی برای غربالگری کاندیدا است.
            با توجه به رزومه زیر، چند سوال شخصی‌سازی شده بپرس.
            - حتما در مورد "حقوق مد نظر" سوال بپرس.
            - اگر فرد دانشجو است، در مورد "وضعیت تحصیلی و میزان ساعت حضور در هفته" سوال بپرس.
            - اگر آقا است و وضعیت سربازی مشخص نیست، در مورد "وضعیت نظام وظیفه" سوال بپرس. (اگر نوشته معاف یا پایان خدمت، نپرس)
            - سوالات باید دوستانه و محترمانه باشند.
            خروجی باید یک آرایه JSON از اشیاء با یک کلید "question" باشد.

            رزومه:
            {resume_text}
            """
        elif stage == "part2_psychological":
            prompt = f"""
            شما یک روانشناس سازمانی و متخصص ارزیابی منابع انسانی هستید.
            کاندیدا مرحله اول را گذرانده. حالا باید شخصیت و مهارت‌های نرم او را با سوالات بسیار حرفه‌ای و غیرمستقیم به چالش بکشید.
            با توجه به رزومه و موقعیت شغلی، 3 سوال چالشی طراحی کن.
            هدف: ارزیابی وظیفه‌شناسی، سازگاری، برونگرایی، قدرت تحلیل و تفکر انتقادی (مفاهیم BIG5 و DISC).
            سوالات نباید مستقیم باشند. مثلا به جای "آیا شما فرد وظیفه‌شناسی هستید؟"، بپرس: "موقعیتی را توصیف کنید که در آن با یک همکار بی‌مسئولیت در یک پروژه مشترک قرار گرفتید. چه کردید و نتیجه چه شد؟"

            موقعیت شغلی: {job_title}
            رزومه:
            {resume_text}

            خروجی باید یک آرایه JSON از اشیاء با یک کلید "question" باشد.
            """
        elif stage == "part3_technical":
            prompt = f"""
            شما یک مدیر فنی ارشد برای موقعیت شغلی "{job_title}" هستید.
            با توجه به مهارت‌ها و نرم‌افزارهای لیست شده در رزومه، 2 سوال فنی خلاقانه و عمیق بپرس تا سطح تسلط واقعی فرد مشخص شود.
            سوالات نباید تعریف ساده باشند. باید کاربردی و چالشی باشند.
            مثال: به جای "SQL بلدید؟"، بپرسید: "فرض کنید دو جدول دارید: Users و Orders. چطور لیستی از کاربرانی که تا به حال هیچ سفارشی ثبت نکرده‌اند را استخراج می‌کنید؟"

            رزومه:
            {resume_text}

            خروجی باید یک آرایه JSON از اشیاء با یک کلید "question" باشد.
            """
        
        if prompt:
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            return extract_json_array(response.text)
        return []

    def evaluate_answer_and_decide_next_question(question, answer, resume_text, job_title, stage, user_name="کاندیدا"):
        """
        بررسی پاسخ و تولید بازخورد تعاملی: تایید، توضیح خواستن، یا رفتن به سوال بعد.
        """
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = f"""
        شما یک مصاحبه‌گر حرفه‌ای منابع انسانی هستید. وظیفه شما تحلیل پاسخ کاندیدا به سوال مصاحبه است.

        سوال: "{question}"
        پاسخ کاربر: "{answer}"

        رزومه کاندیدا:
        {resume_text}

        موقعیت شغلی: {job_title}
        مرحله مصاحبه: {stage}

        حالا دقیق و طبیعی بررسی کن:
        - اگر پاسخ خوب، کامل و مرتبط بود، یک بازخورد دوستانه فارسی بده مثل: «خیلی خوب بود، بریم سوال بعدی.»
        - اگر پاسخ ناقص یا گنگ بود، به‌طور طبیعی از کاربر بخواه دقیق‌تر توضیح بده. بگو کدام قسمت مشخص نیست. مثلا: «{user_name} عزیز، لطفاً در مورد نقش خودتون در اون پروژه بیشتر توضیح بدید.»
        - اگر کاربر پاسخ غیرمرتبط داده یا عمداً نخواسته پاسخ بده، با احترام بگو: «اگر دوست ندارید به این سوال پاسخ بدید، می‌تونیم بریم سوال بعد.»

        فقط یکی از این بازخوردها رو خیلی کوتاه و صمیمی بنویس.
        """
    
        response = model.generate_content(prompt).text.strip()
        return response



    # --- منطق نمایش و پیشرفت مصاحبه ---
        current_stage = st.session_state.interview_stage

        if current_stage != "finished" and current_stage != "final_analysis":
        # اگر برای مرحله فعلی سوالی ایجاد نشده، ایجاد کن
            if not st.session_state.questions:
                st.warning("⏳ در انتظار تولید سوالات...")
                with st.spinner(f"در حال آماده‌سازی سوالات مرحله «{current_stage}»..."):
                    try:
                        questions = generate_questions(
                            current_stage,
                            st.session_state.resume_text,
                            st.session_state.get("selected_job", "")
                        )
                        st.write("📋 سوالات تولیدشده:", questions)  # نمایش برای دیباگ
                        st.session_state.questions = questions
                        st.session_state.current_q_idx = 0
                    except Exception as e:
                        st.error("❌ خطا در تولید سوالات:")
                        st.exception(e)
                        st.stop()

        
       # نمایش سوال فعلی
            q_idx = st.session_state.current_q_idx
            if q_idx < len(st.session_state.questions):
                q = st.session_state.questions[q_idx]["question"]
                st.markdown(f"### {q}")
                user_answer = st.text_input("✍️ پاسخ شما:", key=f"ans_{current_stage}_{q_idx}")

                if st.button("➡️ ثبت پاسخ و ادامه", key=f"submit_{current_stage}_{q_idx}"):
                    if user_answer:
                        with st.spinner("در حال بررسی پاسخ شما..."):
                            feedback = evaluate_answer_and_decide_next_question(
                                question=q,
                                answer=user_answer,
                                resume_text=st.session_state.resume_text,
                                job_title=st.session_state.get("selected_job", ""),
                                stage=current_stage,
                                user_name=st.session_state.get("user_name", "کاندیدا")
                            )

            # --- پردازش بازخورد و به‌روزرسانی وضعیت ---
            if "بریم سوال بعد" in feedback or "خوب بود" in feedback or "عالی" in feedback or "ممنون" in feedback:
                st.success(feedback)
                st.session_state.answers.append({
                    "stage": current_stage,
                    "question": q,
                    "answer": user_answer
                })
                st.session_state.current_q_idx += 1
                st.rerun()

            elif "توضیح" in feedback or "بیشتر بفرمایید" in feedback or "مشخص نیست" in feedback:
                st.warning(feedback)
                # در این حالت، چون شماره سوال زیاد نمی‌شود، همین سوال دوباره نمایش داده می‌شود

            else: # حالتی که کاربر از پاسخ طفره رفته است
                st.info(feedback)
                st.session_state.answers.append({
                    "stage": current_stage,
                    "question": q,
                    "answer": user_answer + " (پاسخ ناقص/نامشخص)"
                })
                st.session_state.current_q_idx += 1
                st.rerun()
        else:
            # این بخش اصلاح شد: اگر کاربر پاسخی وارد نکرده بود، این هشدار نمایش داده می‌شود
            st.warning("لطفاً به سوال پاسخ دهید.")

else:
    # این مرحله تمام شد، به مرحله بعد برو
    st.session_state.questions = []  # پاک کردن سوالات برای مرحله بعد
    st.session_state.current_q_idx = 0

    if current_stage == "part1_general":
        # اجرای غربالگری
        passed, message = run_initial_screening(st.session_state.answers)
        if passed:
            st.session_state.interview_stage = "part2_psychological"
            st.success("✅ مرحله اول با موفقیت تمام شد. به بخش سوالات تخصصی‌تر می‌رویم.")
        else:
            st.error(f"⚠️ {message}")
            st.info("با تشکر از وقتی که گذاشتید. فرآیند مصاحبه در اینجا به پایان می‌رسد.")
            st.session_state.interview_stage = "finished"
        st.rerun()

    elif current_stage == "part2_psychological":
        st.session_state.interview_stage = "part3_technical"
        st.success("✅ مرحله دوم با موفقیت تمام شد. اکنون چند سوال فنی پرسیده می‌شود.")
        st.rerun()
    
    elif current_stage == "part3_technical":
        st.session_state.interview_stage = "final_analysis"
        st.rerun()
    # --- بخش تحلیل نهایی و ذخیره‌سازی ---
    elif current_stage == "final_analysis":
        if not st.session_state.resume_text.strip():
            st.stop()

        if not st.session_state.answers:
            st.stop()

        with st.spinner("🎉 مصاحبه به پایان رسید. در حال تحلیل نهایی پاسخ‌ها و رزومه شما هستیم..."):
            summary = "\n\n".join([f"مرحله: {a['stage']}\nسوال: {a['question']}\nپاسخ: {a['answer']}" for a in st.session_state.answers])
            
            final_prompt = f"""
            شما یک مدیر ارشد منابع انسانی هستید و باید یک گزارش کامل تحلیلی از کاندیدا ارائه دهید.
            با توجه به رزومه، موقعیت شغلی، و مجموعه پاسخ‌های فرد به سوالات در مراحل مختلف، یک تحلیل جامع ارائه دهید.

            موقعیت شغلی: {st.session_state.get('selected_job', 'نامشخص')}
            رزومه:
            {st.session_state.resume_text}
            ---
            سوالات و پاسخ‌های مصاحبه:
            {summary}
            ---
            گزارش تحلیلی خود را در بخش‌های زیر ارائه دهید:
            1.  📝 **خلاصه کلی:** یک پاراگراف در مورد کاندیدا و تناسب کلی او با موقعیت شغلی.
            2.  🧠 **تحلیل روانشناختی و شخصیتی:** بر اساس پاسخ‌های مرحله دوم، تحلیل خود از وظیفه‌شناسی، سازگاری، تفکر انتقادی و سایر ویژگی‌های شخصیتی او را بنویسید.
            3.  🔧 **تحلیل فنی:** بر اساس پاسخ‌های مرحله سوم، میزان تسلط فنی او را ارزیابی کنید.
            4.  🎯 **نقاط قوت کلیدی:** 3 نقطه قوت اصلی فرد را لیست کنید.
            5.  📌 **نقاط ضعف یا ریسک‌ها:** موارد نگران‌کننده یا نقاطی که نیاز به بررسی بیشتر در مصاحبه حضوری دارند را مشخص کنید.
            6.  🏆 **پیشنهاد نهایی:** به طور واضح مشخص کنید که آیا این فرد را برای مرحله بعد (مثلاً مصاحبه حضوری) پیشنهاد می‌کنید یا خیر. (مثال: پیشنهاد برای مصاحبه فنی / پیشنهاد برای مصاحبه با مدیر واحد / عدم پیشنهاد)
            """
            
            try:
                model = genai.GenerativeModel("gemini-2.0-flash")
                analysis_report = model.generate_content(final_prompt).text

                # ذخیره در فایل Excel
                downloads_folder = Path.home() / "Downloads" / "chatbotResult"
                downloads_folder.mkdir(parents=True, exist_ok=True)
                excel_path = downloads_folder / "results.xlsx"

                if os.path.exists(excel_path):
                    df = pd.read_excel(excel_path)
                else:
                    df = pd.DataFrame(columns=["user_id", "selected_job", "resume_text", "answers", "full_analysis"])

                new_row = {
                    "user_id": clean_excel_text(st.session_state.get("user_id", "unknown")),
                    "selected_job": clean_excel_text(st.session_state.get("selected_job", "نامشخص")),
                    "resume_text": clean_excel_text(st.session_state.resume_text),
                    "answers": clean_excel_text(json.dumps(st.session_state.answers, ensure_ascii=False)),
                    "full_analysis": clean_excel_text(analysis_report)
                }
                
                new_df = pd.DataFrame([new_row])
                df = pd.concat([df, new_df], ignore_index=True)
                df.to_excel(excel_path, index=False)

                st.success("✅ تحلیل شما با موفقیت انجام و ذخیره شد.")
                st.markdown("---")
                st.markdown("### گزارش تحلیلی نهایی:")
                st.markdown(analysis_report)
                st.session_state.interview_stage = "finished"

            except Exception as e:
                st.error(f"❌ خطا در تحلیل نهایی یا ذخیره فایل: {e}")