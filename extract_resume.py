import streamlit as st
import pathlib
import fitz
import json
import re
import pandas as pd
import shutil
import os
from google import genai
from google.genai import types
import certifi
import time
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter
from datetime import datetime, timedelta
import tempfile
import zipfile
from io import BytesIO
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import itertools

# صفحه کانفیگ
st.set_page_config(
    page_title="پردازشگر رزومه ",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* ================================
   RTL برای صفحه + استثناءهای ضروری
   ================================ */

/* چیدمان کلی صفحه */
.main .block-container {
    direction: rtl;
    text-align: right;
}

/* ویجت‌های ورودی (متنی/انتخابی) */
.stSelectbox > div > div > div,
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSidebar .stSelectbox > div > div > div,
.stSidebar .stTextInput > div > div > input,
.stSidebar .stTextArea > div > div > textarea {
    direction: rtl;
    text-align: right;
}

/* تب‌ها و اجزای جانبی */
.stTabs [data-baseweb="tab-list"],
.streamlit-expanderHeader,
.metric-container,
.stFileUploader > div,
.stProgress,
.stAlert,
.stDownloadButton {
    direction: rtl;
    text-align: right;
}

/* ستون‌ها: راست‌چین ولی بدون تغییر direction */
.stColumns > div {
    text-align: right;
}

/* تیترها */
h1, h2, h3, h4, h5, h6 {
    direction: rtl;
    text-align: right;
    font-family: 'Vazir', 'Tahoma', sans-serif;
}

/* کارت‌ها و باکس‌های سفارشی */
.main-header {
    text-align: center;
    color: #1f77b4;
    font-size: 2.5rem;
    margin-bottom: 1rem;
    font-family: 'Vazir', 'Tahoma', sans-serif;
}
.success-box {
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    border-radius: 5px;
    padding: 10px;
    margin: 10px 0;
    direction: rtl;
    text-align: right;
}
.error-box {
    background-color: #f8d7da;
    border: 1px solid #f5c6cb;
    border-radius: 5px;
    padding: 10px;
    margin: 10px 0;
    direction: rtl;
    text-align: right;
}
.info-box {
    background-color: #d1ecf1;
    border: 1px solid #bee5eb;
    border-radius: 5px;
    padding: 10px;
    margin: 10px 0;
    direction: rtl;
    text-align: right;
}
.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 10px;
    color: white;
    text-align: center;
    direction: rtl;
    font-family: 'Vazir', 'Tahoma', sans-serif;
}

/* دکمه‌ها */
.stButton > button {
    width: 100%;
    height: 3rem;
    font-size: 1.2rem;
    font-family: 'Vazir', 'Tahoma', sans-serif;
}

/* ======== استثناءهای مهم برای باگ‌های UI ======== */

/* 1) دیتافریم باید LTR باشد تا کامل رندر شود */
.stDataFrame, .stDataFrame * {
    direction: ltr !important;
    text-align: left !important;
}

/* 2) اسلایدر باید LTR باشد تا کشویی و لیبل‌ها به‌هم نریزند */
.stSlider, .stSlider * {
    direction: ltr !important;
    text-align: left !important;
}
</style>
""", unsafe_allow_html=True)

# تنظیمات اولیه
os.environ["SSL_CERT_FILE"] = certifi.where()

# کلیدهای API
DEFAULT_GENAI_KEYS = [
    "AIzaSyAQ1Z8HmIZm-eNvohxoM4ZNFM8JsZsxDII",  
    "AIzaSyAQhK01WbSxiXUdXqe5xEvJA3feUiQCL0E",  
    "AIzaSyAhMXCXIfat3NQqsyWk-S8gdOzTRZLc_bA",  
    "AIzaSyCBH-nSuALuLBerOBn2JS-z3yBYuvPXTPw",
    "AIzaSyClzhUwWrUyI_dEjaYO4d4mijfBFGw1his",
    "AIzaSyCWZVz-ciOp91vKr2u7J87IktK2skygOro",
    "AIzaSyB11u1-TTuvIRNhSAp44PgWWpoK9kq1mAo"
]

# الگوهای خطای محدودیت
_rate_limit_patterns = [
    re.compile(r"429"),
    re.compile(r"rate.*limit", re.IGNORECASE),
    re.compile(r"quota", re.IGNORECASE),
    re.compile(r"exceed", re.IGNORECASE),
    re.compile(r"RateLimit", re.IGNORECASE),
]

# ترتیب فیلدها
ORDERED_FIELDS = [
    "نام", "نام خانوادگی", "شماره تماس", "جنسیت", "ایمیل", "کانال دریافت رزومه",
    "معرف", "کارشناسی", "کارشناسی ارشد", "دکتری", "رشته تحصیلی", "گرایش تحصیلی", "مقطع تحصیلی",
    "دانشگاه محل تحصیلی", "نوع دانشگاه آخرین مدرک تحصیلی", "وضعیت تحصیلی",
    "دوره های آموزشی", "نرم افزارها", "سوابق شغلی",
    "وضعیت خدمت سربازی", "وضعیت تاهل", "محل سکونت", "سن", "year_of_birth",
    "حداقل حقوق ماهیانه", "حداکثر حقوق ماهیانه",
    "فعالیت های داوطلبانه", "درباره ی من",
    "تایید و رد اولیه", "علت رد"
]

class QuotaExhaustedException(Exception):
    """خطای سهمیه تمام شده برای همه کلیدها"""
    pass

class APIKeyManager:
    """مدیر کلیدهای API با قابلیت مدیریت موثر"""
    def __init__(self, api_keys):
        self.api_keys = api_keys
        self.clients = {}
        self.failed_keys = set()
        self.key_usage_count = {key: 0 for key in api_keys}
        self.lock = threading.Lock()
        self._initialize_clients()
    
    def _initialize_clients(self):
        """ایجاد کلاینت‌ها برای تمام کلیدها"""
        for key in self.api_keys:
            try:
                client = genai.Client(api_key=key)
                self.clients[key] = client
            except Exception as e:
                print(f"Failed to initialize client for key {key[:10]}...: {e}")
    
    def get_available_client(self):
        """دریافت یک کلاینت موجود"""
        with self.lock:
            # پیدا کردن کلیدی که کمترین استفاده را داشته و فعال است
            available_keys = [key for key in self.api_keys if key not in self.failed_keys]
            
            if not available_keys:
                raise QuotaExhaustedException("همه کلیدهای API غیرفعال شده‌اند")
            
            # انتخاب کلید با کمترین استفاده
            selected_key = min(available_keys, key=lambda k: self.key_usage_count[k])
            self.key_usage_count[selected_key] += 1
            
            return self.clients[selected_key], selected_key
    
    def mark_key_failed(self, key, temporary=True):
        """علامت‌گذاری کلید به عنوان ناموفق"""
        with self.lock:
            if temporary:
                # برای خطاهای موقتی، فقط کاهش اولویت
                self.key_usage_count[key] += 1000  # penalty
            else:
                # برای خطاهای دائمی، کلید را غیرفعال کن
                self.failed_keys.add(key)
    
    def get_stats(self):
        """آمار استفاده از کلیدها"""
        with self.lock:
            active_keys = len(self.api_keys) - len(self.failed_keys)
            total_usage = sum(self.key_usage_count.values())
            return {
                "total_keys": len(self.api_keys),
                "active_keys": active_keys,
                "failed_keys": len(self.failed_keys),
                "total_usage": total_usage
            }

def _is_rate_limit_error(exc: Exception) -> bool:
    msg = str(exc)
    return any(p.search(msg) for p in _rate_limit_patterns)

def extract_retry_delay(error_msg: str) -> int:
    """استخراج زمان انتظار از پیام خطا"""
    retry_match = re.search(r"retry.*?(\d+(?:\.\d+)?)\s*s", error_msg, re.IGNORECASE)
    if retry_match:
        return int(float(retry_match.group(1))) + 5
    return 60

def extract_text_from_pdf(pdf_bytes):
    """استخراج متن از PDF"""
    try:
        doc = fitz.open(stream=pdf_bytes)
        return "".join([page.get_text() for page in doc])
    except Exception as e:
        return ""

def estimate_birth_year_from_text(text):
    """تخمین سال تولد از روی سن"""
    match = re.search(r"(?:سن\s*[:\-]?)?\s*(\d{2})\s*سال", text)
    if match:
        age = int(match.group(1))
        estimated = 1404 - age
        if 1300 <= estimated <= 1404:
            return estimated
    return ""

def clean_year_of_birth(value):
    """پاک‌سازی year_of_birth"""
    try:
        year = float(value)
        year_int = int(round(year))
        return year_int if 1300 <= year_int <= 1404 else ""
    except:
        return ""

def format_job_experience(job_list):
    """تبدیل لیست سوابق شغلی به متن نمایشی"""
    if isinstance(job_list, list):
        return "; ".join([f"{item.get('شرکت', '')} ({item.get('مدت', '')})" for item in job_list])
    return job_list

def format_courses(course_list):
    """تبدیل لیست دوره‌های آموزشی به متن نمایشی"""
    if isinstance(course_list, list):
        return "; ".join([
            f"{c.get('نام دوره', '')}"
            + (f" - {c['مؤسسه']}" if c.get("مؤسسه") else "")
            + (f" ({c['مدت']})" if c.get("مدت") else "")
            for c in course_list
        ])
    return course_list

def process_single_file(file_info, api_manager, max_retries=3):
    """پردازش یک فایل با استفاده از API Manager"""
    filename, pdf_bytes, extracted_text = file_info
    
    prompt = f"{extracted_text}\nاین متن همان PDF است. اطلاعات این متن اولویت دارد. لطفاً اطلاعات خواسته‌شده را مطابق schema زیر استخراج کن.\n\nسوابق شغلی را به صورت لیستی از آبجکت‌ها بده که هر مورد شامل نام شرکت و مدت زمان اشتغال باشد.\nاگر در رزومه به حقوق یا دستمزد اشاره شده بود، بازه حقوق ماهیانه را به صورت عدد ریالی (تومان × 10000) استخراج کن. اگر فقط یک عدد وجود داشت، هر دو مقدار (حداقل و حداکثر) برابر همان عدد باشد."
    
    for attempt in range(max_retries):
        try:
            # دریافت کلاینت از API Manager
            client, current_key = api_manager.get_available_client()
            
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Part.from_bytes(data=pdf_bytes, mime_type='application/pdf'),
                    types.Part(text=prompt)
                ],
                config={
                    'response_mime_type': 'application/json',
                    'system_instruction': 'extract asked information from Persian resume',
                    'response_schema': { 
                      "type": "object",
                        "properties": {
                            "نام": {"type": "string", "nullable": False,"description": "extract just first name in persian language."},
                            "نام خانوادگی": {"type": "string", "nullable": False,"description": "extract just family name in persian language"},
                            "شماره تماس": {"type": "string", "nullable": False,"description": "extract just one phone number that begin with 09"},
                            "جنسیت": {"type": "string", "nullable": False,"description": "افراد با جنسیت مذکر را 'آقا'بنویس و جنسیت مونث را 'خانم'بنویس. از نوشتن مرد، مذکر، زن، مونث خودداری کن"},
                            "ایمیل": {"type": "string", "nullable": False,"description":'extract email, prefer gmail if multiple emails exist'},
                            "کانال دریافت رزومه": {"type": "string", "nullable": False,"description": "print 'جاب ویژن' for everyone"},
                            "معرف": {"type": "string", "nullable": False,"description":'این فیلد رو همیشه خالی بذار'},
                            "کارشناسی": {
                                "type": "string", "nullable": True,
                                "description": "لطفاً اطلاعات را به صورت کامل و ساختاریافته بنویس. مثال: 'کارشناسی - مهندسی صنایع - دانشگاه تهران - 1395 تا 1399 - معدل 17.30'"
                            },
                            "کارشناسی ارشد": {
                                "type": "string", "nullable": True,
                                "description": "مثال: 'کارشناسی ارشد - اقتصاد - دانشگاه شهید بهشتی تهران - 1402 تا کنون - معدل 18.02'"
                            },
                            "دکتری": {
                                "type": "string", "nullable": True,
                                "description": "مثال: 'دکتری - مدیریت منابع انسانی - دانشگاه علامه طباطبایی - 1398 تا 1402 - معدل 17.75'"
                            },
                            "رشته تحصیلی": {"type": "string", "nullable": False,"description":'آخرین رشته تحصیلی ای که خونده'},
                            "گرایش تحصیلی": {"type": "string", "nullable": True},
                            "دانشگاه محل تحصیلی": {"type": "string", "nullable": False,"description":'آخرین دانشگاهی که تحصیل کرده'},
                            "نوع دانشگاه آخرین مدرک تحصیلی": {"type": "string", "enum": ["دولتی", "آزاد", "غیر انتفاعی", "پیام نور", "فنی حرفه ای"]},
                            "وضعیت تحصیلی": {"type": "string", "enum": ["فارغ التحصیل کارشناسی ارشد", "فارغ التحصیل دکتری", "دانشجوی کارشناسی", "دانشجوی کارشناسی ارشد", "دانشجوی دکتری"]},
                            "مقطع تحصیلی": {"type": "string", "enum": ["کارشناسی", "دکتری", "کارشناسی ارشد", "کاردانی کارشناسی"]},
                            "نرم افزارها": {"type": "string", "nullable": True},
                            "دوره های آموزشی": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "نام دوره": {"type": "string"},
                                        "مؤسسه": {"type": "string", "nullable": True},
                                        "مدت": {"type": "string", "nullable": True}
                                    },
                                    "required": ["نام دوره"]
                                }
                            },
                            "زبان های خارجی": {"type": "array", "items": {"type": "string"}},
                            "وضعیت خدمت سربازی": {"type": "string", "enum": ["پایان خدمت", "مشمول", "معافیت تحصیلی", "معافیت", "خانم"]},
                            "وضعیت تاهل": {"type": "string", "enum": ["متاهل", "مجرد"]},
                            "year_of_birth": {"type": "number", "nullable": True},
                            "سن": {"type": "number", "nullable": True},
                            "محل سکونت": {"type": "string", "nullable": True},
                            "سوابق شغلی": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "شرکت": {"type": "string"},
                                        "مدت": {"type": "string"}
                                    },
                                    "required": ["شرکت", "مدت"]
                                },
                                "nullable": True
                            },
                            "حداقل حقوق ماهیانه": {"type": "number", "nullable": True},
                            "حداکثر حقوق ماهیانه": {"type": "number", "nullable": True},
                            "فعالیت های داوطلبانه": {"type": "string", "nullable": True},
                            "درباره ی من": {"type": "string", "nullable": True}
                        },
                        "required": [
                            "نام", "نام خانوادگی", "شماره تماس", "جنسیت", "ایمیل", "کانال دریافت رزومه",
                            "رشته تحصیلی", "دانشگاه محل تحصیلی", "نوع دانشگاه آخرین مدرک تحصیلی",
                            "وضعیت تحصیلی", "year_of_birth", "سن", "نرم افزارها",
                            "دوره های آموزشی", "وضعیت خدمت سربازی", "وضعیت تاهل", "مقطع تحصیلی"
                        ]  
                    }
                }
            )
            
            result = json.loads(response.text)
            return {"success": True, "data": result, "filename": filename, "key_used": current_key}
            
        except Exception as e:
            error_msg = str(e)
            
            if _is_rate_limit_error(e):
                # علامت‌گذاری کلید به عنوان موقتاً ناموفق
                api_manager.mark_key_failed(current_key, temporary=True)
                
                if attempt < max_retries - 1:
                    retry_delay = extract_retry_delay(error_msg)
                    time.sleep(min(retry_delay, 10))  # حداکثر 10 ثانیه انتظار
                    continue
                else:
                    return {"success": False, "error": f"Rate limit exceeded after {max_retries} attempts", "filename": filename}
            else:
                # خطای دیگر - کلید را دائماً غیرفعال کن
                api_manager.mark_key_failed(current_key, temporary=False)
                
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    return {"success": False, "error": str(e), "filename": filename}
    
    return {"success": False, "error": "Max retries exceeded", "filename": filename}

def process_resume_data(row, text):
    """پردازش و تنظیم داده‌های رزومه"""
    
    # پردازش شماره تماس
    phone = row.get("شماره تماس", "")
    if phone.startswith("0"):
        row["شماره تماس"] = phone[1:]

    # پردازش سال تولد
    row["year_of_birth"] = clean_year_of_birth(row.get("year_of_birth", ""))
    if not row["year_of_birth"]:
        row["year_of_birth"] = estimate_birth_year_from_text(text)

    # فرمت‌دهی داده‌ها
    row["سوابق شغلی"] = format_job_experience(row.get("سوابق شغلی", ""))
    row["دوره های آموزشی"] = format_courses(row.get("دوره های آموزشی", ""))

    # تایید و رد اولیه
    reasons = []

    # استخراج و پاک‌سازی مقادیر
    gender = str(row.get("جنسیت", "")).strip()
    degree = str(row.get("مقطع تحصیلی", "")).strip()
    military_status = str(row.get("وضعیت خدمت سربازی", "")).strip()
    max_salary = row.get("حداکثر حقوق ماهیانه", "")

    # بررسی جنسیت
    if "خانم" in gender:
        reasons.append("جنسیت خانم باعث رد شده است.")

    # بررسی حقوق ماهیانه
    try:
        if max_salary and float(max_salary) > 60_000_000:
            reasons.append("درخواست حقوق بیش از 60 میلیون تومان باعث رد شده است.")
    except:
        pass

    # بررسی مقطع تحصیلی
    if degree not in ["کارشناسی", "کارشناسی ارشد", "دکتری"]:
        reasons.append("مدرک تحصیلی کمتر از کارشناسی باعث رد شده است.")

    # بررسی وضعیت خدمت سربازی
    if "مشمول" in military_status:
        reasons.append("مشمول بودن وضعیت سربازی باعث رد شده است.")

    # وضعیت نهایی
    if reasons:
        row["تایید و رد اولیه"] = "رد"
        row["علت رد"] = "؛ ".join(reasons)
        return row, "rejected"
    else:
        row["تایید و رد اولیه"] = "تایید"
        row["علت رد"] = ""
        return row, "approved"

def create_excel_file(all_data):
    """ایجاد فایل Excel با استایل مناسب"""
    df = pd.DataFrame(all_data)
    for col in df.columns:
        df[col] = df[col].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
    df = df[[col for col in ORDERED_FIELDS if col in df.columns]]

    # ایجاد فایل Excel در حافظه
    output = BytesIO()
    
    # دسته‌بندی ستون‌ها
    base_fields = ["نام", "نام خانوادگی", "شماره تماس", "جنسیت", "ایمیل", "کانال دریافت رزومه", "معرف"]
    base_indexes = [df.columns.get_loc(f) for f in base_fields if f in df.columns]
    if base_indexes:
        base_start = min(base_indexes) + 1
        base_end = max(base_indexes) + 1
    else:
        base_start = 1
        base_end = 7

    check_start = base_end + 1
    check_end = df.shape[1]

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="رزومه‌ها", startrow=1)
        workbook = writer.book
        worksheet = writer.sheets["رزومه‌ها"]

        # اضافه کردن ردیف دسته‌بندی
        worksheet.insert_rows(1)
        worksheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=base_end)
        worksheet.merge_cells(start_row=1, start_column=base_end + 1, end_row=1, end_column=check_end)
        worksheet.cell(row=1, column=1).value = "مشخصات پایه و معرف"
        worksheet.cell(row=1, column=base_end + 1).value = "بررسی رزومه"
            
        # رنگ و استایل برای گروه‌بندی
        base_fill = PatternFill(start_color="C2E0FF", end_color="C2E0FF", fill_type="solid")
        check_fill = PatternFill(start_color="FFE699", end_color="FFE699", fill_type="solid")
        group_font = Font(bold=True, size=13)
        group_alignment = Alignment(horizontal="center", vertical="center")
        
        for col in range(1, base_end + 1):
            worksheet.cell(row=1, column=col).fill = base_fill
            worksheet.cell(row=1, column=col).font = group_font
            worksheet.cell(row=1, column=col).alignment = group_alignment
        for col in range(base_end + 1, check_end + 1):
            worksheet.cell(row=1, column=col).fill = check_fill
            worksheet.cell(row=1, column=col).font = group_font
            worksheet.cell(row=1, column=col).alignment = group_alignment

        # استایل هدر
        header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        for cell in worksheet[2]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # رنگ‌دهی ردیف تایید/رد
        approve_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        reject_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        
        try:
            status_col_idx = ORDERED_FIELDS.index("تایید و رد اولیه")
            for row in worksheet.iter_rows(min_row=3, max_row=worksheet.max_row):
                if len(row) > status_col_idx:
                    status = row[status_col_idx].value
                    if status == "تایید":
                        for cell in row:
                            cell.fill = approve_fill
                    elif status == "رد":
                        for cell in row:
                            cell.fill = reject_fill
        except (ValueError, IndexError):
            pass

        # تنظیم عرض ستون‌ها
        for idx, col in enumerate(worksheet.columns, 1):
            max_length = 0
            for cell in col:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)  # حداکثر عرض 50
            worksheet.column_dimensions[get_column_letter(idx)].width = adjusted_width

    output.seek(0)
    return output

def main():
    # هدر اصلی
    st.markdown('<h1 class="main-header">📋 پردازشگر رزومه موازی</h1>', unsafe_allow_html=True)
    
    # Sidebar برای تنظیمات
    st.sidebar.header("⚙️ تنظیمات")
    
    # مدیریت API Keys
    st.sidebar.subheader("🔑 مدیریت کلیدهای API")
    
    # انتخاب نوع ورودی کلیدها
    key_input_method = st.sidebar.radio(
        "روش ورود کلیدها:",
        ["استفاده از کلیدهای پیش‌فرض", "ورود کلیدهای سفارشی"]
    )
    
    if key_input_method == "استفاده از کلیدهای پیش‌فرض":
        api_keys = DEFAULT_GENAI_KEYS
        st.sidebar.success(f"✅ {len(api_keys)} کلید پیش‌فرض لود شد")
    else:
        custom_keys_text = st.sidebar.text_area(
            "کلیدهای API (هر کدام در یک خط):",
            height=150,
            placeholder="AIzaSy...\nAIzaSy...\n..."
        )
        
        if custom_keys_text:
            api_keys = [key.strip() for key in custom_keys_text.split('\n') if key.strip()]
            st.sidebar.success(f"✅ {len(api_keys)} کلید سفارشی لود شد")
        else:
            api_keys = DEFAULT_GENAI_KEYS
            st.sidebar.warning("⚠️ از کلیدهای پیش‌فرض استفاده می‌شود")

    # تنظیمات پروکسی
    st.sidebar.subheader("🌐 تنظیمات پروکسی")
    use_proxy = st.sidebar.checkbox("استفاده از پروکسی")
    
    if use_proxy:
        proxy_url = st.sidebar.text_input(
            "آدرس پروکسی:",
            value="http://172.16.217.234:33525"
        )
        if proxy_url:
            os.environ['HTTP_PROXY'] = proxy_url
            os.environ['HTTPS_PROXY'] = proxy_url
            st.sidebar.success("✅ پروکسی تنظیم شد")
    else:
        # پاک کردن پروکسی
        os.environ.pop('HTTP_PROXY', None)
        os.environ.pop('HTTPS_PROXY', None)

    # تنظیمات پردازش موازی
    st.sidebar.subheader("⚡ تنظیمات پردازش موازی")
    max_workers = st.sidebar.slider("حداکثر Thread های موازی:", 1, min(len(api_keys), 10), min(len(api_keys), 5))
    max_retries = st.sidebar.slider("حداکثر تلاش مجدد:", 1, 5, 3)

    # بخش اصلی
    tab1, tab2, tab3, tab4 = st.tabs(["📤 آپلود و پردازش", "📊 نتایج", "📈 آمار API", "ℹ️ راهنما"])
    
    with tab1:
        st.header("📤 آپلود فایل‌های PDF")
        
        # آپلود فایل‌ها
        uploaded_files = st.file_uploader(
            "فایل‌های PDF رزومه را انتخاب کنید:",
            type=['pdf'],
            accept_multiple_files=True,
            help="می‌توانید چندین فایل PDF را به صورت همزمان آپلود کنید"
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} فایل آپلود شد")
            
            # نمایش لیست فایل‌ها
            with st.expander("📋 لیست فایل‌های آپلود شده", expanded=False):
                for i, file in enumerate(uploaded_files, 1):
                    st.write(f"{i}. {file.name} ({file.size:,} بایت)")
            
            # اطلاعات پردازش موازی
            st.info(f"🚀 پردازش موازی با {max_workers} Thread و {len(api_keys)} کلید API")
            
            # دکمه پردازش
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🚀 شروع پردازش موازی", type="primary"):
                    process_files_parallel(uploaded_files, api_keys, max_workers, max_retries)
    
    with tab2:
        st.header("📊 نتایج پردازش")
        
        if "processing_results" in st.session_state and st.session_state.processing_results:
            display_results()
        else:
            st.info("🔍 هنوز فایلی پردازش نشده است. لطفاً ابتدا فایل‌هایتان را آپلود و پردازش کنید.")
    
    with tab3:
        st.header("📈 آمار استفاده از API")
        
        if "api_stats" in st.session_state and st.session_state.api_stats:
            display_api_stats()
        else:
            st.info("🔍 آماری از استفاده API موجود نیست.")
    
    with tab4:
        display_help()

def process_files_parallel(uploaded_files, api_keys, max_workers, max_retries):
    """پردازش موازی فایل‌های آپلود شده"""
    
    # شروع پردازش
    st.info("🔄 در حال شروع پردازش موازی...")
    
    # ایجاد API Manager
    api_manager = APIKeyManager(api_keys)
    
    # آماده‌سازی داده‌های ورودی
    file_data = []
    for uploaded_file in uploaded_files:
        pdf_bytes = uploaded_file.read()
        extracted_text = extract_text_from_pdf(pdf_bytes)
        
        if extracted_text.strip():
            file_data.append((uploaded_file.name, pdf_bytes, extracted_text))
        else:
            st.warning(f"⚠️ فایل {uploaded_file.name} قابل خواندن نیست")
    
    if not file_data:
        st.error("❌ هیچ فایل قابل پردازشی وجود ندارد")
        return
    
    # ایجاد progress bar و containers
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # متغیرهای آماری
    processing_stats = {
        "total": len(file_data),
        "processed": 0,
        "failed": 0,
        "approved": 0,
        "rejected": 0,
        "start_time": time.time()
    }
    
    # کانتینرهای نمایش real-time
    metrics_container = st.container()
    details_container = st.container()
    
    with metrics_container:
        col1, col2, col3, col4, col5 = st.columns(5)
        metric_total = col1.empty()
        metric_processed = col2.empty()
        metric_approved = col3.empty()
        metric_rejected = col4.empty()
        metric_speed = col5.empty()
    
    with details_container:
        details_expander = st.expander("🔍 جزئیات پردازش", expanded=True)
        details_text = details_expander.empty()
    
    processing_details = []
    all_data = []
    failed_files = []
    
    # تابع به‌روزرسانی UI
    def update_ui():
        # محاسبه سرعت
        elapsed_time = time.time() - processing_stats["start_time"]
        speed = processing_stats["processed"] / max(elapsed_time, 1) * 60  # فایل در دقیقه
        
        # به‌روزرسانی متریک‌ها
        metric_total.metric("📄 کل فایل‌ها", processing_stats["total"])
        metric_processed.metric("✅ پردازش شده", processing_stats["processed"])
        metric_approved.metric("🟢 تایید شده", processing_stats["approved"])
        metric_rejected.metric("🔴 رد شده", processing_stats["rejected"])
        metric_speed.metric("⚡ سرعت", f"{speed:.1f}/min")
        
        # به‌روزرسانی جزئیات
        details_text.text("\n".join(processing_details[-15:]))  # آخرین 15 مورد
    
    # پردازش موازی با ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # ارسال تمام تسک‌ها
        future_to_file = {
            executor.submit(process_single_file, file_info, api_manager, max_retries): file_info[0] 
            for file_info in file_data
        }
        
        # پردازش نتایج به محض آماده شدن
        for future in as_completed(future_to_file):
            filename = future_to_file[future]
            
            try:
                result = future.result()
                
                if result["success"]:
                    # پردازش داده‌های رزومه
                    model_output = result["data"]
                    row = {field: model_output.get(field, "") for field in ORDERED_FIELDS}
                    
                    # استخراج متن برای پردازش بیشتر
                    file_text = ""
                    for file_info in file_data:
                        if file_info[0] == filename:
                            file_text = file_info[2]
                            break
                    
                    processed_row, status = process_resume_data(row, file_text)
                    all_data.append(processed_row)
                    
                    processing_stats["processed"] += 1
                    
                    if status == "approved":
                        processing_stats["approved"] += 1
                        processing_details.append(f"✅ تایید شد: {processed_row.get('نام', '')} {processed_row.get('نام خانوادگی', '')} (کلید: {result['key_used'][:10]}...)")
                    else:
                        processing_stats["rejected"] += 1
                        processing_details.append(f"❌ رد شد: {processed_row.get('نام', '')} {processed_row.get('نام خانوادگی', '')} - {processed_row.get('علت رد', '')}")
                else:
                    failed_files.append(filename)
                    processing_stats["failed"] += 1
                    processing_details.append(f"❌ پردازش ناموفق: {filename} - {result.get('error', 'خطای نامشخص')}")
                
            except Exception as e:
                failed_files.append(filename)
                processing_stats["failed"] += 1
                processing_details.append(f"❌ خطای غیرمنتظره: {filename} - {str(e)}")
            
            # به‌روزرسانی UI
            progress = (processing_stats["processed"] + processing_stats["failed"]) / processing_stats["total"]
            progress_bar.progress(progress)
            status_text.text(f"🔄 پردازش شده: {processing_stats['processed'] + processing_stats['failed']}/{processing_stats['total']}")
            
            update_ui()
    
    # تکمیل پردازش
    progress_bar.progress(1.0)
    status_text.text("✅ پردازش موازی کامل شد!")
    
    # محاسبه زمان کل
    total_time = time.time() - processing_stats["start_time"]
    
    # ذخیره نتایج در session state
    st.session_state.processing_results = {
        "data": all_data,
        "stats": processing_stats,
        "failed_files": failed_files,
        "processing_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_time": total_time
    }
    
    # ذخیره آمار API
    st.session_state.api_stats = api_manager.get_stats()
    
    # نمایش خلاصه نهایی
    st.success(f"🎉 پردازش موازی با موفقیت در {total_time:.1f} ثانیه تکمیل شد!")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"""
        📊 **آمار کلی:**
        - کل فایل‌ها: {processing_stats['total']}
        - پردازش موفق: {processing_stats['processed']}
        - پردازش ناموفق: {processing_stats['failed']}
        """)
    
    with col2:
        st.info(f"""
        🔍 **نتایج بررسی:**
        - تایید شده: {processing_stats['approved']}
        - رد شده: {processing_stats['rejected']}
        - نرخ تایید: {(processing_stats['approved']/(processing_stats['processed'] or 1)*100):.1f}%
        """)
    
    with col3:
        avg_time = total_time / len(file_data) if file_data else 0
        st.info(f"""
        ⚡ **عملکرد:**
        - زمان کل: {total_time:.1f} ثانیه
        - متوسط هر فایل: {avg_time:.1f} ثانیه
        - سرعت: {len(file_data)/total_time*60:.1f} فایل/دقیقه
        """)

def display_results():
    """نمایش نتایج پردازش"""
    
    results = st.session_state.processing_results
    
    # آمار کلی
    st.subheader("📈 آمار کلی")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{results['stats']['total']}</h3>
            <p>کل فایل‌ها</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{results['stats']['processed']}</h3>
            <p>پردازش موفق</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{results['stats']['approved']}</h3>
            <p>تایید شده</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{results['stats']['rejected']}</h3>
            <p>رد شده</p>
        </div>
        """, unsafe_allow_html=True)
    
    # نمودار دایره‌ای
    if results['data']:
        st.subheader("📊 توزیع نتایج")
        
        # آماده‌سازی داده‌ها برای نمودار
        chart_data = pd.DataFrame({
            'وضعیت': ['تایید شده', 'رد شده'],
            'تعداد': [results['stats']['approved'], results['stats']['rejected']]
        })
        
        # نمودار ستونی
        st.bar_chart(chart_data.set_index('وضعیت'))
    
    # اطلاعات عملکرد
    if 'total_time' in results:
        st.subheader("⚡ عملکرد پردازش")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("⏱️ زمان کل", f"{results['total_time']:.1f} ثانیه")
        
        with col2:
            avg_time = results['total_time'] / results['stats']['total'] if results['stats']['total'] > 0 else 0
            st.metric("📊 متوسط هر فایل", f"{avg_time:.1f} ثانیه")
        
        with col3:
            speed = results['stats']['total'] / results['total_time'] * 60 if results['total_time'] > 0 else 0
            st.metric("🚀 سرعت", f"{speed:.1f} فایل/دقیقه")
    
    # نمایش داده‌های پردازش شده
    if results['data']:
        st.subheader("📋 داده‌های استخراج شده")
        
        df = pd.DataFrame(results['data'])
        
        # فیلتر بر اساس وضعیت
        filter_status = st.selectbox(
            "فیلتر بر اساس وضعیت:",
            ["همه", "تایید شده", "رد شده"]
        )
        
        if filter_status == "تایید شده":
            df_filtered = df[df["تایید و رد اولیه"] == "تایید"]
        elif filter_status == "رد شده":
            df_filtered = df[df["تایید و رد اولیه"] == "رد"]
        else:
            df_filtered = df
        
        # نمایش جدول
        st.dataframe(
            df_filtered,
            use_container_width=True,
            height=400
        )
        
        # دکمه دانلود Excel
        if st.button("📥 دانلود فایل Excel", type="secondary"):
            excel_file = create_excel_file(results['data'])
            
            st.download_button(
                label="💾 دانلود Excel",
                data=excel_file,
                file_name=f"resume_processing_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    # فایل‌های ناموفق
    if results['failed_files']:
        st.subheader("⚠️ فایل‌های پردازش نشده")
        
        st.markdown('<div class="error-box">', unsafe_allow_html=True)
        st.write("فایل‌های زیر به دلیل خطا پردازش نشدند:")
        for failed_file in results['failed_files']:
            st.write(f"• {failed_file}")
        st.markdown('</div>', unsafe_allow_html=True)

def display_api_stats():
    """نمایش آمار استفاده از API"""
    
    stats = st.session_state.api_stats
    
    st.subheader("🔑 آمار کلیدهای API")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🔑 کل کلیدها", stats['total_keys'])
    
    with col2:
        st.metric("✅ کلیدهای فعال", stats['active_keys'])
    
    with col3:
        st.metric("❌ کلیدهای غیرفعال", stats['failed_keys'])
    
    with col4:
        st.metric("📊 کل درخواست‌ها", stats['total_usage'])
    
    # نمودار وضعیت کلیدها
    if stats['total_keys'] > 0:
        chart_data = pd.DataFrame({
            'وضعیت': ['فعال', 'غیرفعال'],
            'تعداد': [stats['active_keys'], stats['failed_keys']]
        })
        
        st.bar_chart(chart_data.set_index('وضعیت'))

def display_help():
    """نمایش راهنما"""
    
    st.header("📚 راهنمای استفاده")
    
    # بخش‌های مختلف راهنما
    help_sections = {
        "🚀 پردازش موازی": """
        **مزایای پردازش موازی:**
        - استفاده همزمان از چندین کلید API
        - سرعت پردازش بالاتر (تا 5-10 برابر سریع‌تر)
        - مدیریت خودکار کلیدهای ناموفق
        - بهره‌وری بهتر از منابع
        
        **نحوه کار:**
        1. هر فایل به یک Thread جداگانه اختصاص می‌یابد
        2. هر Thread از یک کلید API مجزا استفاده می‌کند
        3. در صورت خطا، کلید دیگری انتخاب می‌شود
        4. نتایج به صورت real-time نمایش داده می‌شوند
        """,
        
        "🔑 مدیریت هوشمند کلیدها": """
        **ویژگی‌های مدیر کلیدها:**
        - توزیع یکنواخت بار بین کلیدها
        - تشخیص خودکار کلیدهای ناموفق
        - مدیریت محدودیت‌های موقت و دائم
        - آمارگیری دقیق از استفاده
        
        **انواع خطاها:**
        - **خطای موقت:** محدودیت نرخ، انتظار کوتاه
        - **خطای دائم:** کلید نامعتبر، غیرفعال‌سازی کامل
        """,
        
        "⚙️ تنظیمات بهینه": """
        **حداکثر Thread:**
        - کمتر از تعداد کلیدهای API
        - برای اتصال سریع: 3-5 Thread
        - برای اتصال آهسته: 1-2 Thread
        
        **تعداد تلاش مجدد:**
        - برای شبکه پایدار: 3-5
        - برای شبکه ناپایدار: 1-2
        
        **نکات مهم:**
        - بیش از 10 Thread توصیه نمی‌شود
        - کلیدهای بیشتر = سرعت بالاتر
        """,
        
        "📊 نظارت بر عملکرد": """
        **متریک‌های مهم:**
        - سرعت پردازش (فایل/دقیقه)
        - نرخ موفقیت
        - توزیع استفاده از کلیدها
        - زمان متوسط هر فایل
        
        **بهینه‌سازی:**
        - مانیتور کردن آمار API
        - تعدیل تعداد Thread‌ها
        - جایگزینی کلیدهای ناموفق
        """
    }
    
    for section_title, section_content in help_sections.items():
        with st.expander(section_title, expanded=False):
            st.markdown(section_content)
    
    # مقایسه عملکرد
    st.subheader("📊 مقایسه عملکرد")
    
    comparison_data = pd.DataFrame({
        "روش": ["تک‌رشته‌ای", "موازی (3 Thread)", "موازی (5 Thread)"],
        "سرعت تقریبی": ["10 فایل/دقیقه", "30 فایل/دقیقه", "50 فایل/دقیقه"],
        "کاربرد": ["فایل کم", "متوسط", "فایل زیاد"]
    })
    
    st.table(comparison_data)

# اجرای برنامه اصلی
if __name__ == "__main__":
    # Initialize session state
    if "processing_results" not in st.session_state:
        st.session_state.processing_results = None
    
    if "api_stats" not in st.session_state:
        st.session_state.api_stats = None
    
    main()
