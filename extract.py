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
import streamlit as st
import zipfile
from PyPDF2 import PdfReader

os.environ["SSL_CERT_FILE"] = certifi.where()


# --- تنظیمات اولیه ---
proxy_url = "http://172.16.217.234:33525"
os.environ['HTTP_PROXY'] = proxy_url
os.environ['HTTPS_PROXY'] = proxy_url

genai_client = genai.Client(api_key="AIzaSyBEZ9d7p008FjBDcw_bLWL-328AX7rAng0")

input_folder = pathlib.Path(r"D:\AliRahmani\input")
output_excel_path = pathlib.Path(r"D:\AliRahmani\output\newData.xlsx")
output_folder = pathlib.Path(r"D:\AliRahmani\outbox")
output_folder.mkdir(parents=True, exist_ok=True)

# --- ترتیب فیلدها در خروجی ---
ordered_fields = [
    "نام", "نام خانوادگی", "شماره تماس", "جنسیت", "ایمیل", "کانال دریافت رزومه",
    "معرف", "کارشناسی", "کارشناسی ارشد", "دکتری", "رشته تحصیلی", "گرایش تحصیلی", "مقطع تحصیلی",
    "دانشگاه محل تحصیلی", "نوع دانشگاه آخرین مدرک تحصیلی", "وضعیت تحصیلی",
    "دوره های آموزشی", "نرم افزارها", "سوابق شغلی",
    "وضعیت خدمت سربازی", "وضعیت تاهل", "محل سکونت", "سن", "year_of_birth",
    "حداقل حقوق ماهیانه", "حداکثر حقوق ماهیانه",
    "فعالیت های داوطلبانه", "درباره ی من",
    "تایید و رد اولیه", "علت رد"
]

# --- استخراج متن از PDF ---
def extract_text_from_pdf(file_path):
    try:
        doc = fitz.open(file_path)
        return "".join([page.get_text() for page in doc])
    except Exception as e:
        print(f"❌ خطا در خواندن PDF {file_path.name}: {e}")
        return ""

# --- تخمین سال تولد از روی سن ---
def estimate_birth_year_from_text(text):
    match = re.search(r"(?:سن\s*[:\-]?)?\s*(\d{2})\s*سال", text)
    if match:
        age = int(match.group(1))
        estimated = 1404 - age
        if 1300 <= estimated <= 1404:
            return estimated
    return ""


# --- پاک‌سازی year_of_birth ---
def clean_year_of_birth(value):
    try:
        year = float(value)
        year_int = int(round(year))
        return year_int if 1300 <= year_int <= 1404 else ""
    except:
        return ""

# --- تبدیل لیست سوابق شغلی به متن نمایشی ---
def format_job_experience(job_list):
    if isinstance(job_list, list):
        return "; ".join([f"{item.get('شرکت', '')} ({item.get('مدت', '')})" for item in job_list])
    return job_list

# --- تبدیل لیست دوره‌های آموزشی به متن نمایشی ---
def format_courses(course_list):
    if isinstance(course_list, list):
        return "; ".join([
            f"{c.get('نام دوره', '')}"
            + (f" - {c['مؤسسه']}" if c.get("مؤسسه") else "")
            + (f" ({c['مدت']})" if c.get("مدت") else "")
            for c in course_list
        ])
    return course_list

# --- دریافت داده‌ها از Gemini ---
def extract_data_from_genai(pdf_path: pathlib.Path, extracted_text: str) -> dict:
    try:
        prompt = f"{extracted_text}\nاین متن همان PDF است. اطلاعات این متن اولویت دارد. لطفاً اطلاعات خواسته‌شده را مطابق schema زیر استخراج کن.\n\nسوابق شغلی را به صورت لیستی از آبجکت‌ها بده که هر مورد شامل نام شرکت و مدت زمان اشتغال باشد.\nاگر در رزومه به حقوق یا دستمزد اشاره شده بود، بازه حقوق ماهیانه را به صورت عدد ریالی (تومان × 10000) استخراج کن. اگر فقط یک عدد وجود داشت، هر دو مقدار (حداقل و حداکثر) برابر همان عدد باشد."

        response = genai_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Part.from_bytes(data=pdf_path.read_bytes(), mime_type='application/pdf'),
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
        print(f"❌ خطا در Gemini برای فایل {pdf_path.name}: {e}")
        return {}

# --- اجرای پردازش رزومه‌ها ---
def process_resumes():
    all_data = []

    for pdf_file in input_folder.glob("*.pdf"):
        print(f"📄 پردازش فایل: {pdf_file.name}")
        text = extract_text_from_pdf(pdf_file)
        if not text.strip():
            print(f"⚠️ فایل خالی: {pdf_file.name}")
            continue

        model_output = extract_data_from_genai(pdf_file, text)
        if not model_output:
            continue

        row = {field: model_output.get(field, "") for field in ordered_fields}

        phone = row.get("شماره تماس", "")
        if phone.startswith("0"):
            row["شماره تماس"] = phone[1:]

        row["year_of_birth"] = clean_year_of_birth(row.get("year_of_birth", ""))
        if not row["year_of_birth"]:
            row["year_of_birth"] = estimate_birth_year_from_text(text)

        row["سوابق شغلی"] = format_job_experience(row.get("سوابق شغلی", ""))
        row["دوره های آموزشی"] = format_courses(row.get("دوره های آموزشی", ""))

        # --- تایید و رد اولیه (با لاگ کامل) ---
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
        except Exception as e:
            print(f"⚠️ خطا در بررسی حقوق برای {row.get('نام', '')} {row.get('نام خانوادگی', '')}: {e}")

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
            print(f"❌ رد شد: {row['نام']} {row['نام خانوادگی']} | دلایل: {row['علت رد']}")
        else:
            row["تایید و رد اولیه"] = "تایید"
            row["علت رد"] = ""
            print(f"✅ تایید شد: {row['نام']} {row['نام خانوادگی']}")

        

        all_data.append(row)

        try:
            destination = output_folder / pdf_file.name
            if destination.exists():
                destination = output_folder / f"{pdf_file.stem}_moved{pdf_file.suffix}"
            shutil.move(str(pdf_file), destination)
            time.sleep(3)
        except Exception as e:
            print(f"⚠️ خطا در انتقال {pdf_file.name}: {e}")

    if all_data:
        df = pd.DataFrame(all_data)
        for col in df.columns:
            df[col] = df[col].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)

        df = df[[col for col in ordered_fields if col in df.columns]]

        try:
            df.to_excel(output_excel_path, index=False)
            print(f"✅ فایل اکسل با موفقیت ذخیره شد: {output_excel_path}")
        except Exception as e:
            print(f"❌ خطا در ذخیره‌سازی فایل Excel: {e}")
    else:
        print("⚠️ هیچ رزومه‌ای پردازش نشد.")

# --- اجرا ---
process_resumes()

# تابعی برای استخراج اطلاعات از فایل PDF
def extract_info_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()  # استخراج متن از صفحات
    # اینجا می‌توانید کدهای خود را برای پردازش متن و استخراج اطلاعات اضافه کنید
    extracted_data = {
        "Text": text  # برای مثال، فقط متن کامل فایل PDF را ذخیره می‌کنیم
    }
    return extracted_data

# پردازش فایل‌های زیپ
def extract_info_from_pdf(pdf_file):
    from PyPDF2 import PdfReader
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()  # استخراج متن از صفحات
    # اینجا می‌توانید کدهای خود را برای پردازش متن و استخراج اطلاعات اضافه کنید
    extracted_data = {
        "Text": text  # برای مثال، فقط متن کامل فایل PDF را ذخیره می‌کنیم
    }
    return extracted_data

# پردازش فایل‌های PDF
def process_pdf(file):
    extracted_data = extract_info_from_pdf(file)
    
    # ساخت یک DataFrame از اطلاعات استخراج‌شده
    df = pd.DataFrame([extracted_data])
    
    # ذخیره فایل اکسل به صورت موقت در سیستم
    output_dir = "D:/AliRahmani/extracted_data"  # مسیر ذخیره فایل اکسل
    os.makedirs(output_dir, exist_ok=True)  # اگر دایرکتوری وجود ندارد، آن را می‌سازد

    output_file = os.path.join(output_dir, "extracted_data.xlsx")

    # ذخیره داده‌ها در فایل اکسل
    df.to_excel(output_file, index=False)
    
    # فراهم کردن امکان دانلود فایل اکسل
    with open(output_file, "rb") as f:
        st.download_button(
            label="دانلود فایل اکسل",
            data=f,
            file_name="extracted_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# بارگذاری فایل‌ها
def upload_files():
    uploaded_file = st.file_uploader("فایل‌ها را بارگذاری کنید (PDF یا زیپ)", type=["zip", "pdf"])
    if uploaded_file:
        return uploaded_file
    return None

# نمایش نتایج پردازش
def display_results(files):
    if isinstance(files, list):  # برای فایل‌های زیپ
        for file in files:
            if file.name.endswith(".zip"):
                st.write(f"در حال پردازش فایل زیپ: {file.name}")
                # پردازش فایل زیپ را اینجا اضافه کنید
            elif file.name.endswith(".pdf"):
                st.write(f"در حال پردازش فایل PDF: {file.name}")
                process_pdf(file)
    else:  # برای فایل PDF تنها
        st.write(f"در حال پردازش فایل PDF: {files.name}")
        process_pdf(files)

def main():
    st.title("بارگذاری و پردازش فایل‌های PDF و زیپ")
    
    uploaded_files = upload_files()
    if uploaded_files:
        display_results(uploaded_files)

if __name__ == "__main__":
    main()