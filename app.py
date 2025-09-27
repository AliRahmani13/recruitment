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
    "AIzaSyAQ1Z8HmIZm-eNvohxoM4ZNFM8JsZsxDII",  #GptSavaran14
    "AIzaSyAQhK01WbSxiXUdXqe5xEvJA3feUiQCL0E",  #GptSavaran14
    "AIzaSyAhMXCXIfat3NQqsyWk-S8gdOzTRZLc_bA",  #GptSavaran14
    "AIzaSyCBH-nSuALuLBerOBn2JS-z3yBYuvPXTPw",  #GptSavaran14
    "AIzaSyClzhUwWrUyI_dEjaYO4d4mijfBFGw1his",  #GptSavaran14
    "AIzaSyCWZVz-ciOp91vKr2u7J87IktK2skygOro",  #GptSavaran14
    "AIzaSyB11u1-TTuvIRNhSAp44PgWWpoK9kq1mAo",  #GptSavaran14
    "AIzaSyBxusefsMEbKv6HAoYxECpOIqbKO-pCs2g",  #GptSavaran14
    "AIzaSyDIAYd4QdTBQO4MVOnAvoA5tNEozVYdflE",  #GptSavaran14
    "AIzaSyBw6zUcIsp5t4QZxI_BRiPphYJzf7mq8p4",  #GptSavaran14
    "AIzaSyC3EpZaqKLQwxCGUxKLzuwzvtKT2EjYTEA",  #GptSavaran14
    "AIzaSyAkXdS9nAA35pdOX4kZQaFOgOznjU9MlDs",  #GptSavaran14
    "AIzaSyBZqnpTMHL8Zap2CIrqifqXVA5YB30Apuw",  #GptKaran14
    "AIzaSyBqTtltNANsAhbodnxfFJOFq8vaGszJPqQ",  #GptKaran14
    "AIzaSyCC2RTsg8ArBgXj8t82-w-agFE82s0CUHw",  #GptKaran14
    "AIzaSyDvtLtNuVVlgNBvzwPRl42RyWZJqRsCI4Q",  #GptKaran14
    "AIzaSyATYlQN6L7SJz7mY7wScnyB8G_DqRsJQT4",  #GptKaran14
    "AIzaSyBW8Q1amjzs0_XLHaKaecyZuQJe0U5qhZU",  #GptKaran14
    "AIzaSyA7YtWUSsljlQuWOuy3fSBajot2rI5D3e8",  #GptKaran14
    "AIzaSyAsFagF5Z-A_o2pvUiAwpzqXpDpRNjhwfM",  #GptKaran14
    "AIzaSyDG8LTKH4NGqQcaGAz76z4hKAQ95jVjz4c",  #GptKaran14
    "AIzaSyDwB9W3SJjG5qkTd58L8ToX0xmi57Kh8d4",  #GptKaran14
    "AIzaSyBNAb6TSR4mhq82WtW2wHSCOUDK73IDbfs",  #GptKaran14
    "AIzaSyB51i5YnENFBE8aYncinPtwLk1dThl2CuA"  #GptKaran14
]


font_css = """
<style>
  @font-face {
    font-family: 'BNazanin';
    src: url('fonts/0 Nazanin.TTF') format('truetype');
    font-weight: normal;
    font-style: normal;
  }

  @font-face {
    font-family: 'BNazanin';
    src: url('fonts/0 Nazanin Bold.TTF') format('truetype');
    font-weight: bold;
    font-style: normal;
  }

  html, body, [class^="st-"], [class*=" st-"], .block-container {
    font-family: 'BNazanin', sans-serif !important;
    direction: rtl !important;
    text-align: right !important;
  }
</style>
"""
st.markdown(font_css, unsafe_allow_html=True)


def style_excel(path): 
    wb = openpyxl.load_workbook(path) 
    ws = wb.active 

    # --- رنگ‌ها ---
    header_fill = PatternFill(start_color="B7DEE8", end_color="B7DEE8", fill_type="solid")  # تیتر
    row_fill_odd = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")  # ردیف‌های فرد
    row_fill_even = PatternFill(start_color="EAF3FA", end_color="EAF3FA", fill_type="solid")  # ردیف‌های زوج

    # --- فونت و تراز ---
    header_font = Font(bold=True, name='B Nazanin', size=14)
    row_font = Font(name='B Nazanin', size=12)
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # --- حاشیه دور سلول‌ها ---
    border = Border(
        left=Side(border_style="thin", color="CCCCCC"),
        right=Side(border_style="thin", color="CCCCCC"),
        top=Side(border_style="thin", color="CCCCCC"),
        bottom=Side(border_style="thin", color="CCCCCC"),
    )

    # --- تیتر (ردیف اول) ---
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align
        cell.border = border

    # --- سطرهای داده ---
    for idx, row in enumerate(ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=ws.max_column), start=2):
        fill = row_fill_even if idx % 2 == 0 else row_fill_odd
        for cell in row:
            cell.fill = fill
            cell.font = row_font
            cell.alignment = center_align
            cell.border = border

    # --- تنظیم wrap text برای "تحلیل نهایی" ---
    for col in ws.columns:
        if col[0].value == "تحلیل نهایی":
            for cell in col:
                cell.alignment = Alignment(wrap_text=True, vertical="top", horizontal="center")

    # --- تنظیم خودکار عرض ستون‌ها ---
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

    # --- Freeze اولین ردیف ---
    ws.freeze_panes = ws["A2"] 

    wb.save(path)


class RotatingGeminiLLM:
    def __init__(self, api_keys, model="gemini-2.5-flash"):
        self.api_keys = api_keys
        self.model = model
        self.idx = 0  # شروع از اولین کلید

    def invoke(self, messages):
        # سعی می‌کنیم با هر کلید تا موفقیت یا رسیدن به انتها
        num_keys = len(self.api_keys)
        start_idx = self.idx
        for i in range(num_keys):
            api_key = self.api_keys[self.idx]
            llm = ChatGoogleGenerativeAI(model=self.model, google_api_key=api_key)
            try:
                result = llm.invoke(messages)
                return result  # موفقیت
            except Exception as e:
                print(f"⚠️ خطا با API {api_key[:10]}...: {str(e)}")
                self.idx = (self.idx + 1) % num_keys  # برو سراغ کلید بعدی
                if self.idx == start_idx:
                    # یعنی همه کلیدها امتحان شد و خطا دادند
                    raise RuntimeError("❌ تمام API Keyها با خطا مواجه شدند.")
        raise RuntimeError("❌ تمام API Keyها با خطا مواجه شدند.")

# استفاده:
rotating_llm = RotatingGeminiLLM(API_KEYS)
# --- تابع هوشمند برای استفاده از APIها ---
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


# --- حذف فایل خروجی قبلی ---
RESULT_FILE_PATH = Path("resume_results.xlsx")
if RESULT_FILE_PATH.exists():
    RESULT_FILE_PATH.unlink()

# --- پاک‌سازی session در هر بار اجرای جدید ---
#for key in ['final_df', 'live_results']:
    #if key in st.session_state:
        #del st.session_state[key]

# --- گواهی SSL ---
os.environ['SSL_CERT_FILE'] = certifi.where()

# --- تنظیم پراکسی ---
proxy_url = "http://172.16.217.234:33525"
os.environ['HTTP_PROXY'] = proxy_url
os.environ['HTTPS_PROXY'] = proxy_url

# --- تست اتصال ---
test_url = "https://generativelanguage.googleapis.com/v1beta/models"
try:
    response = requests.get(test_url, proxies={"http": proxy_url, "https": proxy_url}, timeout=5)
    if response.status_code == 200:
        print("✅ اتصال برقرار است.")
    else:
        print(f"⚠️ کد وضعیت: {response.status_code}")
except Exception as e:
    print(f"❌ خطا در اتصال پراکسی: {e}")

# --- تنظیمات اولیه ---
pd.set_option('display.max_rows', None)
OUTPUT_ALL_PATH = Path("recruitment_score.xlsx")
ID_COLUMN = 'شناسه'
BATCH_SIZE = 10
RESULT_FILE_PATH = Path("resume_results.xlsx")

if 'live_results' not in st.session_state:
    st.session_state['live_results'] = []


# --- تم گرافیکی ---



# --- لیست شناسنامه‌های شغلی ---
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
# --- لیست دانشگاه‌های معتبر و نوع دانشگاه برای استفاده در EducationAgent ---
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
        return 30  # مقدار پیش‌فرض در صورت خالی بودن 

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
        return round(max(0.0, min(1.0, score)) * 100, 2)  # تبدیل به مقیاس 100
    except: 
        return 30  # پیش‌فرض در صورت خطا
# --- توابع کمکی ---
def process_batch(batch_df, prompt_text):
    payload = {
        "employer requirements": prompt_text,
        "applicant information": [
            {"resume": " ".join([str(row[col]) for col in batch_df.columns]), "id": str(row[ID_COLUMN])}
            for _, row in batch_df.iterrows()
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
            "check_id": str(row[ID_COLUMN]),
            "why": "خطا در پردازش - اطلاعات کافی نیست"
        } for _, row in batch_df.iterrows()])

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
                return None  # شکست خورده

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

# اگر دلیل هنوز خالیه، سعی کن خط بعد از امتیاز رو به عنوان دلیل در نظر بگیری
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

    for _, row in batch_df.iterrows():
        resume_text = " ".join([str(row[col]) for col in batch_df.columns])
        match_df = evaluate_resume_against_all_jobs(resume_text, JOB_PROFILES)

        # اطلاعات هر فرد رو اضافه کن به خروجی
        match_df["شناسه رزومه"] = row.get("شناسه", "")
        match_df["نام"] = row.get("نام", "")
        match_df["نام خانوادگی"] = row.get("نام خانوادگی", "")

        all_results.append(match_df)

    # همه خروجی‌ها رو به یک جدول بزرگ تبدیل کن
    final_df = pd.concat(all_results, ignore_index=True)
    return final_df

# --- تابع اصلاح نمره بر اساس معیارهای اضافه ---
top_universities = ['دانشگاه صنعتی شریف', 'دانشگاه تهران', 'دانشگاه صنعتی امیرکبیر', 'دانشگاه علم و صنعت ایران']
public_keywords = ['صنعتی', 'تهران', 'امیرکبیر', 'علم و صنعت', 'فردوسی', 'تبریز', 'اصفهان', 'دولتی']

def is_public_university(univ_name):
    return any(keyword in str(univ_name) for keyword in public_keywords)

def is_top_university(univ_name):
    return any(top in str(univ_name) for top in top_universities)

def color_score_column(val):
    if val >= 9:
        color = '#00C853'  # سبز پررنگ
    elif val >= 8:
        color = '#AEEA00'  # لیمویی سبز
    elif val >= 7:
        color = '#FFD600'  # زرد
    elif val >= 6:
        color = '#FF9100'  # نارنجی
    elif val >= 5:
        color = '#FF3D00'  # نارنجی-قرمز
    else:
        color = '#D50000'  # قرمز تیره
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
    """
    Agent برای ارزیابی مهارت‌های نرم‌افزاری
    """
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
    # استخراج امتیاز و دلیل (ساده)
    lines = [l.strip() for l in text.splitlines() if l.strip()]  # ✅ درست
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
    """
    Agent برای ارزیابی تجربه کاری
    """
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
    # استخراج امتیاز و دلیل (ساده)
    lines = [l.strip() for l in text.splitlines() if l.strip()]  
    score, reason = 0, ""
    for line in lines:
        if line.startswith("امتیاز"):
            score = int("".join(filter(str.isdigit, line)))
        if line.startswith("دلیل"):
            reason = line.replace("دلیل:", "").strip()
    return score, reason


def education_agent(resume, universities_info, major_list, job_profile_title):
    """
    Agent برای ارزیابی تحصیلات دانشگاهی با ذکر نوع دانشگاه
    """
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
    # استخراج امتیاز و دلیل
    lines = [l.strip() for l in text.splitlines() if l.strip()]  
    score, reason = 0, ""
    for line in lines:
        if line.startswith("امتیاز"):
            score = int("".join(filter(str.isdigit, line)))
        if line.startswith("دلیل"):
            reason = line.replace("دلیل:", "").strip()
    return score, reason

def volunteering_agent(resume, volunteering_field=None):
    """
    Agent برای ارزیابی فعالیت داوطلبانه
    volunteering_field: فقط قسمت مرتبط از رزومه یا None برای کل رزومه
    """
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
    """
    Agent برای ارزیابی مهارت‌های نرم و شایستگی فردی (مانند کار تیمی، مسئولیت‌پذیری و ...)
    about_me_field: فقط قسمت 'درباره من' یا None برای کل رزومه
    """
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

    # فراخوانی هر Agent و ذخیره نمره و دلیل
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

    # ✅ نمره‌دهی هوشمند برای بخش‌های متنی
    results["VolunteeringAgent"]["score"] = score_text_section(vol_reason)
    results["SoftSkillsAgent"]["score"] = score_text_section(soft_reason)

    # میانگین وزنی نهایی
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

def process_resume_row(row):
    resume_text = " ".join([str(row[col]) for col in row.index])
    title, reason, log = match_resume_to_job(resume_text, JOB_PROFILES)

    # گرفتن امتیاز اولیه از Gemini
    gemini_df = process_batch(pd.DataFrame([row]), prompt_text="ارزیابی عمومی رزومه")
    initial_score = gemini_df.iloc[0]['score']

    # سپس اصلاح امتیاز بر اساس شرایط خاص
    score = adjust_score({**row.to_dict(), 'score': initial_score})

    # اطلاعات اصلی رزومه + نتایج تحلیل را ترکیب کن
    new_data = row.to_dict()
    new_data.update({
        "score": score,
        "دلیل": gemini_df.iloc[0]['why'],
        "موقعیت شغلی پیشنهادی": title,
        "دلیل انتخاب موقعیت شغلی": reason,
        "گزارش بررسی شناسنامه‌ها": log
    })

    # ذخیره در فایل
    if RESULT_FILE_PATH.exists():
        existing = pd.read_excel(RESULT_FILE_PATH)
        updated = pd.concat([existing, pd.DataFrame([new_data])], ignore_index=True)
    else:
        updated = pd.DataFrame([new_data])

    updated.to_excel(RESULT_FILE_PATH, index=False)

    # ذخیره در حافظه‌ی session
    st.session_state['live_results'].append(new_data)
    return new_data

# --- رابط کاربری ---
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

with st.sidebar:
    st.markdown("## 📊 وضعیت سیستم")
    st.markdown("### ⏳ پردازش رزومه‌ها")
    status_placeholder = st.empty()
    progress_placeholder = st.empty()

if uploaded_file and ('live_results' not in st.session_state or len(st.session_state['live_results']) == 0):
    status_placeholder.info("✅ فایل آپلود شده. آماده برای شروع ارزیابی...")
    progress_placeholder.progress(0)
elif not uploaded_file:
    status_placeholder.info("⏳ منتظر آپلود فایل رزومه باشید.")
    progress_placeholder.progress(0)

# Example inside your loop:
# for idx, (_, row) in enumerate(df.iterrows()):
#     ... your logic ...
#     # Update stats here:
#     live_df = pd.DataFrame(st.session_state['live_results'])
#     total = len(df)
#     checked = len(live_df)
#     accepted = (live_df['تایید و رد اولیه'] == 'تایید').sum() if 'تایید و رد اولیه' in live_df.columns else 0
#     failed = (live_df['تایید و رد اولیه'] != 'تایید').sum() if 'تایید و رد اولیه' in live_df.columns else 0
#     status_placeholder.success(f"بررسی شده: {checked} / {total}")
#     status_placeholder.markdown(f"🟢 قبول‌شده: {accepted}")
#     status_placeholder.markdown(f"🔴 رد‌شده: {failed}")
#     progress_placeholder.progress(checked / total)


with st.sidebar:
    if st.button("🔄 ریست کامل اطلاعات"):
        for key in ['final_df', 'live_results']:
            if key in st.session_state:
                del st.session_state[key]
        if RESULT_FILE_PATH.exists():
            RESULT_FILE_PATH.unlink()
        st.success("✅ اطلاعات با موفقیت ریست شد.")

# استخراج عناوین شغلی از JOB_PROFILES
job_titles = [job['title'] for job in JOB_PROFILES]

# ۱. multiselect برای انتخاب چندتایی
selected_job_titles = st.multiselect(
    "عنوان شغلی مورد نظر را انتخاب کنید (امکان انتخاب چندتایی):",
    options=job_titles,
    default=None
)

# ۲. ورودی متنی برای عنوان شغلی جدید
custom_job_title = st.text_input("در صورتی که عنوان شغلی مورد نظر شما در لیست نبود، اینجا وارد کنید:")

# ۳. ترکیب نهایی عناوین انتخاب‌شده
all_selected_titles = selected_job_titles.copy()
if custom_job_title.strip() != "":
    all_selected_titles.append(custom_job_title.strip())

# اگر می‌خواهی نمایش بدهی یا به کد بعدی پاس دهی:
# st.write("عناوین انتخاب شده:", all_selected_titles)
# فرض بر اینکه متغیر all_selected_titles لیست عناوین شغلی انتخاب‌شده است

# استخراج تمام مهارت‌های مرتبط با عناوین انتخاب‌شده
selected_skills = []
for job in JOB_PROFILES:
    if job["title"] in all_selected_titles:
        selected_skills.extend([c['name'] for c in job.get('competencies_technical', [])])

# حذف تکراری‌ها
selected_skills = list(sorted(set(selected_skills)))
# ۱. نمایش مهارت‌های مرتبط با عناوین انتخاب شده (به صورت multiselect)
edited_skills = st.multiselect(
    "مهارت‌های مورد نیاز را بررسی و ویرایش کنید:",
    options=selected_skills,
    default=selected_skills
)

# ۲. امکان افزودن مهارت جدید (دلخواه)
custom_skill = st.text_input("در صورت نیاز، مهارت جدید وارد کنید:")

# ۳. ترکیب مهارت‌های انتخاب‌شده و مهارت جدید
all_skills = edited_skills.copy()
if custom_skill.strip() and custom_skill.strip() not in all_skills:
    all_skills.append(custom_skill.strip())

# برای استفاده در ادامه کد:
# st.write("لیست مهارت‌های نهایی:", all_skills)

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    stage = st.radio("🧩 مرحله موردنظر را انتخاب کنید:", ["امتیازدهی", "تطبیق با شناسنامه‌های شغلی"])
    done_ids = []

    if RESULT_FILE_PATH.exists():
        done_ids = pd.read_excel(RESULT_FILE_PATH)['شناسه'].tolist()

    if stage == "امتیازدهی": 
        st.markdown("### 🚀 مرحله امتیازدهی رزومه‌ها") 
        if st.button("شروع امتیازدهی"): 
            results_placeholder = st.empty() 
            progress_bar = st.progress(0) 
            rows = [] 
            for idx, (_, row) in enumerate(df.iterrows()): 
                if row[ID_COLUMN] in done_ids: 
                    continue

                resume = " ".join([str(row[col]) for col in row.index]) 
                skills = all_skills
                required_experience_desc = "سابقه مرتبط با عنوان شغلی" 
                universities = universities_info 
                major_list = []  # بر اساس عنوان شغل انتخابی کاربر مقداردهی کن 
                job_profile_title = ""  # بر اساس UI مقداردهی کن 
                volunteering_field = row.get("فعالیت داوطلبانه", "") 
                about_me_field = row.get("درباره من", "")

                results = scoring_chain(
                    resume, 
                    skills, 
                    required_experience_desc, 
                    universities, 
                    major_list, 
                    job_profile_title, 
                    volunteering_field, 
                    about_me_field
                )

                row_data = row.to_dict() 
                for agent, detail in results.items():
                    if agent != "FinalScore":
                        row_data[f"{agent}_score"] = detail['score']
                        row_data[f"{agent}_reason"] = detail['reason']
                row_data['final_score'] = results['FinalScore']

                row_data['تایید و رد اولیه'] = "تایید" if row_data['final_score'] >= 70 else "رد"
                rows.append(row_data)

                progress_bar.progress((idx + 1) / len(df))

            # ذخیره DataFrame نهایی یا نمایش خروجی کامل 
            results_df = pd.DataFrame(rows)
            results_placeholder.dataframe(results_df)
            results_df.to_excel("resume_scoring.xlsx", index=False)
            style_excel("resume_scoring.xlsx")

            # ----- Dynamic sidebar updates ----- 
            live_df = results_df
            total = len(df)
            checked = len(live_df)
            accepted = (live_df['تایید و رد اولیه'] == 'تایید').sum() if 'تایید و رد اولیه' in live_df.columns else 0
            failed = (live_df['تایید و رد اولیه'] != 'تایید').sum() if 'تایید و رد اولیه' in live_df.columns else 0

            status_placeholder.success(f"بررسی شده: {checked} / {total}")
            status_placeholder.markdown(f"🟢 قبول‌شده: {accepted}")
            status_placeholder.markdown(f"🔴 رد‌شده: {failed}")
            progress_placeholder.progress(checked / total)
            # -----------------------------------

            progress_bar.progress((idx + 1) / len(df))
            time.sleep(1.5)

            # فقط اینجا پیام موفقیت امتیازدهی نمایش داده شود:
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

        if st.button("🚀 شروع تطبیق با شناسنامه‌های شغلی"):
            try:
                # پردازش رزومه‌ها
                match_results = apply_matching_to_batch(df.copy())

                # ساخت خروجی خلاصه‌شده
                def make_sentence(row):
                    return f"میزان انطباق با موقعیت شغلی {row['title']} {int(row['match_percent'])}٪ است، زیرا: {row['reason']}"

                grouped = match_results.groupby("شناسه رزومه")

                final_rows = []
                for resume_id, group in grouped:
                    name = group["نام"].iloc[0]
                    family = group["نام خانوادگی"].iloc[0]
                    sentences = [make_sentence(row) for _, row in group.iterrows()]
                    full_text = "  ".join(sentences)
                    # پیدا کردن عنوان شغلی با بیشترین درصد تطابق
                    best_row = group.loc[group["match_percent"].idxmax()]
                    best_title = best_row["title"]

                    final_rows.append({
                        "شناسه رزومه": resume_id,
                        "نام": name,
                        "نام خانوادگی": family,
                        "موقعیت شغلی پیشنهادی": best_title,
                        "تحلیل نهایی": full_text
                    })


                summary_df = pd.DataFrame(final_rows)

                # ذخیره فایل نهایی
                summary_path = "job_matching_summary.xlsx"
                summary_df.to_excel(summary_path, index=False)
                style_excel(summary_path)

                # نمایش در صفحه
                st.success("✅ تطبیق با شناسنامه‌های شغلی با موفقیت انجام شد.")
                st.dataframe(summary_df)

                # دکمه دانلود
                with open(summary_path, "rb") as f:
                    st.download_button("📥 دانلود فایل نهایی تحلیل‌شده", f, file_name=summary_path)

                progress_bar.progress(1.0)
            
            except Exception as e:
                st.error(f"❌ خطا در انجام تطبیق: {e}")



            # اضافه کردن ستون‌های خروجی در صورت عدم وجود
                for col in ["موقعیت شغلی پیشنهادی", "دلیل انتخاب موقعیت شغلی", "گزارش بررسی شناسنامه‌ها"]:
                    if col not in df.columns:
                        df[col] = None

                rows_to_process = df[df["موقعیت شغلی پیشنهادی"].isna()]
                progress_bar = st.progress(0)
                results = []

                for idx, (_, row) in enumerate(rows_to_process.iterrows()):
                    resume_text = " ".join([str(row[col]) for col in df.columns])
                    title, reason, log = match_resume_to_job(resume_text, JOB_PROFILES)

                    row["موقعیت شغلی پیشنهادی"] = title
                    row["دلیل انتخاب موقعیت شغلی"] = reason
                    row["گزارش بررسی شناسنامه‌ها"] = log
                    results.append(row)

                    progress_bar.progress((idx + 1) / len(rows_to_process))
                    time.sleep(4)

            # ترکیب نتایج جدید با باقی داده‌ها
                rest_df = df[~df.index.isin(rows_to_process.index)]
                final_df = pd.concat([rest_df, pd.DataFrame(results)], ignore_index=True)

            # ذخیره نهایی
                final_df.to_excel(RESULT_FILE_PATH, index=False)

                st.success("✅ تطبیق با شناسنامه‌های شغلی با موفقیت انجام شد.")
                st.download_button("📥 دانلود نتایج تطبیق", data=open(RESULT_FILE_PATH, "rb").read(), file_name="matched_resumes.xlsx")


            # ✅ نمایش زنده جدول پس از هر رزومه
            if 'live_results' in st.session_state:
                results_df = pd.DataFrame(st.session_state['live_results'])
                live_columns = [
                    'شناسه', 'نام', 'نام خانوادگی', 'تایید و رد اولیه', 'علت رد',
                    'score', 'دلیل', 'موقعیت شغلی پیشنهادی', 'دلیل انتخاب موقعیت شغلی',
                    'گزارش بررسی شناسنامه‌ها'
                ]
                live_columns_available = [col for col in live_columns if col in results_df.columns]
                display_live_df = results_df[live_columns_available].copy()
                display_live_df.index = display_live_df.index + 1
                display_live_df.index.name = "ردیف"
                results_placeholder.dataframe(display_live_df)

            # 🔄 بروزرسانی نوار پیشرفت
            progress_bar.progress(1.0)

            # ⏱️ تاخیر برای جلوگیری از overload
            time.sleep(2)

            # امتیازدهی نهایی

            # تعیین موقعیت شغلی پیشنهادی و دلیل

            # ذخیره در session_state

# --- نمایش نتایج و دانلود ---
# --- نمایش نهایی و دانلود فایل کامل ---
# --- نمایش نهایی و دانلود فایل کامل ---
if RESULT_FILE_PATH.exists():
    final_df = pd.read_excel(RESULT_FILE_PATH)

    # نمایش کامل همه ستون‌ها بدون محدودسازی
    display_df = final_df.copy()
    display_df.index = display_df.index + 1
    display_df.index.name = "ردیف"

    st.markdown("### ✅ جدول نهایی رزومه‌های بررسی‌شده")
    
    # اگر ستون 'score' وجود داشت، رنگ‌آمیزی کن
    if 'score' in display_df.columns:
        styled_df = display_df.style.applymap(color_score_column, subset=['score'])
        st.dataframe(styled_df)
    else:
        st.dataframe(display_df)

    style_excel(RESULT_FILE_PATH)
    # دکمه دانلود فایل نهایی
    with open(RESULT_FILE_PATH, "rb") as f:
        st.download_button("📥 دانلود فایل نهایی", f, file_name="resume_results.xlsx")








