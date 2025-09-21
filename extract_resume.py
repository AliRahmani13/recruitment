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

# صفحه کانفیگ
st.set_page_config(
    page_title="پردازشگر رزومه ",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# استایل CSS سفارشی
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stButton > button {
        width: 100%;
        height: 3rem;
        font-size: 1.2rem;
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

def _is_rate_limit_error(exc: Exception) -> bool:
    msg = str(exc)
    return any(p.search(msg) for p in _rate_limit_patterns)

def extract_retry_delay(error_msg: str) -> int:
    """استخراج زمان انتظار از پیام خطا"""
    retry_match = re.search(r"retry.*?(\d+(?:\.\d+)?)\s*s", error_msg, re.IGNORECASE)
    if retry_match:
        return int(float(retry_match.group(1))) + 5
    return 60

@st.cache_resource
def get_genai_client_with_fallback(api_keys_tuple):
    """ایجاد کلاینت Gemini با fallback"""
    api_keys = list(api_keys_tuple)  # تبدیل tuple به list
    last_exc = None
    exhausted_keys = 0
    
    for i, key in enumerate(api_keys, start=1):
        try:
            client = genai.Client(api_key=key)
            # برگرداندن dictionary به جای tuple
            return {
                "client": client,
                "active_key_index": i,
                "success": True,
                "error": None
            }
        except Exception as e:
            last_exc = e
            if _is_rate_limit_error(e):
                exhausted_keys += 1
                continue
            else:
                time.sleep(0.5)
                try:
                    client = genai.Client(api_key=key)
                    return {
                        "client": client,
                        "active_key_index": i,
                        "success": True,
                        "error": None
                    }
                except Exception as e2:
                    last_exc = e2
                    continue
    
    # در صورت شکست
    if exhausted_keys == len(api_keys):
        return {
            "client": None,
            "active_key_index": 0,
            "success": False,
            "error": "همه کلیدهای API به محدودیت روزانه رسیده‌اند."
        }
    
    return {
        "client": None,
        "active_key_index": 0,
        "success": False,
        "error": f"هیچ‌کدام از API Keyها برای ساخت کلاینت جواب نداد: {str(last_exc)}"
    }

def extract_text_from_pdf(pdf_bytes):
    """استخراج متن از PDF"""
    try:
        doc = fitz.open(stream=pdf_bytes)
        return "".join([page.get_text() for page in doc])
    except Exception as e:
        st.error(f"خطا در خواندن PDF: {e}")
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

def extract_data_from_genai(genai_client, pdf_bytes, extracted_text, filename, max_retries=3, api_keys=None):
    """استخراج داده از PDF با استفاده از Gemini API"""
    
    prompt = f"{extracted_text}\nاین متن همان PDF است. اطلاعات این متن اولویت دارد. لطفاً اطلاعات خواسته‌شده را مطابق schema زیر استخراج کن.\n\nسوابق شغلی را به صورت لیستی از آبجکت‌ها بده که هر مورد شامل نام شرکت و مدت زمان اشتغال باشد.\nاگر در رزومه به حقوق یا دستمزد اشاره شده بود، بازه حقوق ماهیانه را به صورت عدد ریالی (تومان × 10000) استخراج کن. اگر فقط یک عدد وجود داشت، هر دو مقدار (حداقل و حداکثر) برابر همان عدد باشد."

    current_client = genai_client
    
    for attempt in range(max_retries):
        try:
            response = current_client.models.generate_content(
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
            return json.loads(response.text)
            
        except Exception as e:
            if _is_rate_limit_error(e):
                error_msg = str(e)
                retry_delay = extract_retry_delay(error_msg)
                
                if attempt < max_retries - 1:
                    st.warning(f"⏳ محدودیت API برای {filename}. تلاش {attempt + 1}/{max_retries}")
                    st.info(f"⏳ انتظار {retry_delay} ثانیه...")
                    
                    # Progress bar برای انتظار
                    progress_bar = st.progress(0)
                    for i in range(retry_delay):
                        progress_bar.progress((i + 1) / retry_delay)
                        time.sleep(1)
                    progress_bar.empty()
                    
                    # تلاش برای گرفتن کلاینت جدید اگر api_keys موجود باشد
                    if api_keys:
                        try:
                            # حذف cache برای تلاش مجدد با کلیدهای دیگر
                            get_genai_client_with_fallback.clear()
                            client_result = get_genai_client_with_fallback(tuple(api_keys))
                            if client_result["success"]:
                                current_client = client_result["client"]
                                st.info(f"🔄 تغییر به کلید #{client_result['active_key_index']}")
                            else:
                                st.error(f"❌ تمام کلیدها به محدودیت رسیده‌اند.")
                                return {}
                        except Exception as client_error:
                            st.error(f"❌ خطا در تعویض کلید: {client_error}")
                            return {}
                    
                    continue
                else:
                    st.error(f"❌ پس از {max_retries} تلاش، پردازش {filename} ناموفق بود.")
                    return {}
            else:
                st.error(f"❌ خطای غیرمنتظره برای {filename}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                return {}
    
    return {}

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
    st.markdown('<h1 class="main-header">🔍 پردازشگر رزومه</h1>', unsafe_allow_html=True)
    
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

    # تنظیمات پردازش
    st.sidebar.subheader("⚡ تنظیمات پردازش")
    max_retries = st.sidebar.slider("حداکثر تلاش مجدد:", 1, 5, 3)
    delay_between_requests = st.sidebar.slider("تأخیر بین درخواست‌ها (ثانیه):", 1, 10, 2)

    # بخش اصلی
    tab1, tab2, tab3 = st.tabs(["📤 آپلود و پردازش", "📊 نتایج", "ℹ️ راهنما"])
    
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
            
            # دکمه پردازش
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🚀 شروع پردازش", type="primary"):
                    process_files(uploaded_files, api_keys, max_retries, delay_between_requests)
    
    with tab2:
        st.header("📊 نتایج پردازش")
        
        if "processing_results" in st.session_state and st.session_state.processing_results:
            display_results()
        else:
            st.info("📝 هنوز فایلی پردازش نشده است. لطفاً ابتدا فایل‌هایتان را آپلود و پردازش کنید.")
    
    with tab3:
        display_help()

def process_files(uploaded_files, api_keys, max_retries, delay_between_requests):
    """پردازش فایل‌های آپلود شده"""
    
    # شروع پردازش
    st.info("🔄 در حال شروع پردازش...")
    
    # تلاش برای دریافت کلاینت - تبدیل list به tuple برای cache
    try:
        client_result = get_genai_client_with_fallback(tuple(api_keys))
        
        if not client_result["success"]:
            if "محدودیت روزانه" in client_result["error"]:
                st.error("❌ همه کلیدهای API به محدودیت روزانه رسیده‌اند. لطفاً فردا دوباره تلاش کنید.")
            else:
                st.error(f"❌ خطا در اتصال به API: {client_result['error']}")
            return
        
        genai_client = client_result["client"]
        active_key_index = client_result["active_key_index"]
        st.success(f"✅ اتصال به Gemini API برقرار شد (کلید #{active_key_index})")
        
    except Exception as e:
        st.error(f"❌ خطای غیرمنتظره در اتصال به API: {e}")
        return
    
    # ایجاد progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # متغیرهای آماری
    all_data = []
    failed_files = []
    processing_stats = {
        "total": len(uploaded_files),
        "processed": 0,
        "failed": 0,
        "approved": 0,
        "rejected": 0
    }
    
    # ایجاد کانتینرهای نمایش real-time
    metrics_container = st.container()
    details_container = st.container()
    
    with metrics_container:
        col1, col2, col3, col4 = st.columns(4)
        metric_total = col1.empty()
        metric_processed = col2.empty()
        metric_approved = col3.empty()
        metric_rejected = col4.empty()
    
    with details_container:
        details_expander = st.expander("📝 جزئیات پردازش", expanded=True)
        details_text = details_expander.empty()
    
    processing_details = []
    
    # پردازش هر فایل
    for i, uploaded_file in enumerate(uploaded_files):
        # به‌روزرسانی progress bar
        progress = (i + 1) / len(uploaded_files)
        progress_bar.progress(progress)
        status_text.text(f"🔄 در حال پردازش: {uploaded_file.name} ({i+1}/{len(uploaded_files)})")
        
        # استخراج متن از PDF
        pdf_bytes = uploaded_file.read()
        text = extract_text_from_pdf(pdf_bytes)
        
        if not text.strip():
            failed_files.append(uploaded_file.name)
            processing_stats["failed"] += 1
            processing_details.append(f"❌ فایل خالی: {uploaded_file.name}")
            continue
        
        # استخراج داده‌ها از Gemini
        model_output = extract_data_from_genai(
            genai_client, pdf_bytes, text, uploaded_file.name, max_retries, api_keys
        )
        
        if not model_output:
            failed_files.append(uploaded_file.name)
            processing_stats["failed"] += 1
            processing_details.append(f"❌ پردازش ناموفق: {uploaded_file.name}")
            continue
        
        # پردازش داده‌ها
        row = {field: model_output.get(field, "") for field in ORDERED_FIELDS}
        processed_row, status = process_resume_data(row, text)
        
        all_data.append(processed_row)
        processing_stats["processed"] += 1
        
        if status == "approved":
            processing_stats["approved"] += 1
            processing_details.append(f"✅ تایید شد: {processed_row.get('نام', '')} {processed_row.get('نام خانوادگی', '')}")
        else:
            processing_stats["rejected"] += 1
            processing_details.append(f"❌ رد شد: {processed_row.get('نام', '')} {processed_row.get('نام خانوادگی', '')} - {processed_row.get('علت رد', '')}")
        
        # به‌روزرسانی متریک‌ها
        metric_total.metric("🔄 کل فایل‌ها", processing_stats["total"])
        metric_processed.metric("✅ پردازش شده", processing_stats["processed"])
        metric_approved.metric("🟢 تایید شده", processing_stats["approved"])
        metric_rejected.metric("🔴 رد شده", processing_stats["rejected"])
        
        # به‌روزرسانی جزئیات
        details_text.text("\n".join(processing_details[-10:]))  # آخرین 10 مورد
        
        # تأخیر بین درخواست‌ها
        if i < len(uploaded_files) - 1:
            time.sleep(delay_between_requests)
    
    # تکمیل پردازش
    progress_bar.progress(1.0)
    status_text.text("✅ پردازش کامل شد!")
    
    # ذخیره نتایج در session state
    st.session_state.processing_results = {
        "data": all_data,
        "stats": processing_stats,
        "failed_files": failed_files,
        "processing_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # نمایش خلاصه نهایی
    st.success("🎉 پردازش با موفقیت تکمیل شد!")
    
    col1, col2 = st.columns(2)
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

def display_help():
    """نمایش راهنما"""
    
    st.header("📚 راهنمای استفاده")
    
    # بخش‌های مختلف راهنما
    help_sections = {
        "🚀 شروع سریع": """
        1. **آپلود فایل‌ها:** از تب "آپلود و پردازش" فایل‌های PDF رزومه را انتخاب کنید
        2. **تنظیمات:** در نوار کناری تنظیمات API و پروکسی را انجام دهید
        3. **پردازش:** روی دکمه "شروع پردازش" کلیک کنید
        4. **نتایج:** از تب "نتایج" خروجی‌ها را مشاهده و دانلود کنید
        """,
        
        "🔑 مدیریت API Keys": """
        - **کلیدهای پیش‌فرض:** سیستم دارای کلیدهای پیش‌تنظیم شده است
        - **کلیدهای سفارشی:** می‌توانید کلیدهای خود را وارد کنید
        - **مدیریت خودکار:** سیستم به صورت خودکار کلیدهای مختلف را امتحان می‌کند
        - **محدودیت روزانه:** هر کلید محدودیت 200 درخواست در روز دارد
        """,
        
        "⚙️ تنظیمات پیشرفته": """
        - **حداکثر تلاش مجدد:** تعداد تلاش‌های مجدد در صورت خطا
        - **تأخیر بین درخواست‌ها:** فاصله زمانی بین پردازش هر فایل
        - **پروکسی:** در صورت نیاز تنظیمات پروکسی را فعال کنید
        """,
        
        "📊 معیارهای تایید/رد": """
        **موارد رد:**
        - جنسیت خانم
        - درخواست حقوق بیش از 60 میلیون تومان
        - مدرک تحصیلی کمتر از کارشناسی
        - وضعیت سربازی مشمول
        
        **سایر موارد تایید می‌شوند**
        """,
        
        "🔧 عیب‌یابی": """
        **مشکلات رایج:**
        - **خطای 429:** محدودیت API - منتظر بمانید یا کلید جدید اضافه کنید
        - **فایل خالی:** فایل PDF قابل خواندن نیست
        - **خطای شبکه:** اتصال اینترنت یا پروکسی را بررسی کنید
        
        **راه‌حل‌ها:**
        - استفاده از کلیدهای API متعدد
        - کاهش سرعت پردازش
        - بررسی کیفیت فایل‌های PDF
        """
    }
    
    for section_title, section_content in help_sections.items():
        with st.expander(section_title, expanded=False):
            st.markdown(section_content)
    
    # اطلاعات تکنیکی
    st.subheader("🔍 اطلاعات تکنیکی")
    
    tech_info = {
        "مدل AI": "Google Gemini 2.0 Flash",
        "فرمت خروجی": "Excel (.xlsx)",
        "پشتیبانی از زبان": "فارسی",
        "حداکثر اندازه فایل": "بدون محدودیت خاص",
        "فرمت‌های پشتیبانی شده": "PDF"
    }
    
    col1, col2 = st.columns(2)
    with col1:
        for key, value in list(tech_info.items())[:3]:
            st.info(f"**{key}:** {value}")
    
    with col2:
        for key, value in list(tech_info.items())[3:]:
            st.info(f"**{key}:** {value}")

# اجرای برنامه اصلی
if __name__ == "__main__":
    # Initialize session state
    if "processing_results" not in st.session_state:
        st.session_state.processing_results = None
    
    main()