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

API_KEYS = [
    "AIzaSyAHuh1NvFx0arcKMm6RbP1EF94TsRvjHh4",
    "AIzaSyDTUCWsjAj1t9D3Tnix6hHWJ3rxjzfleMs",
    "AIzaSyB0cYSO6BEXFY4EGz9A7lzdPMWw84peOXU",
    "AIzaSyAjpckNYaZkifXUdvTL0QpyAVL8k6fsSzw",
    "AIzaSyBrNZg8x4UZfFo3yVmCXJa2YeHG1iFiVhk",
    "AIzaSyATYtdvAxyBetlg00zrX8CKiVZRxfeuHtM",
    "AIzaSyB5iV3q2APEh27EJ7Jm6qqBeIfGnauqdiw",
    "AIzaSyC8tN4kY2QU5ACRacPazzRQeJPtAC08Vm8",
    "AIzaSyCh78GHgYJ9DZUo-TekO6MDxpMWTHD_zjk",
    "AIzaSyBww4mPXQz2dStjJcQJ-T6DAvXXUpgkBBo"
]

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
proxy_url = "http://localhost:2080"
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
streamlit_style = """
<style>
@font-face {
    font-family: 'BNazanin';
    src: url('https://cdn.fontcdn.ir/Fonts/B%20Nazanin/B%20Nazanin.woff2') format('woff2'),
         url('https://cdn.fontcdn.ir/Fonts/B%20Nazanin/B%20Nazanin.woff') format('woff');
    font-weight: normal;
    font-style: normal;
}

main, .block-container {
    direction: rtl;
    text-align: right;
    font-family: 'BNazanin', Tahoma, 'IRANSansWeb', sans-serif !important;
    font-size: 14px;
    line-height: 1.8;
}

html, body {
    font-family: 'BNazanin', Tahoma, 'IRANSansWeb', sans-serif  !important;
    background-color: #f5f7fa;
    color: #333333;
}

h1 {
    font-size: 42px;
    font-weight: bold;
    color: #1a73e8;
    text-align: right;
}

h2 {
    font-size: 32px;
    font-weight: bold;
    color: #1a73e8;
    text-align: right;
}

h3 {
    font-size: 30px;
    font-weight: bold;
    color: #1a73e8;
    text-align: right;
}

.stButton>button, .stDownloadButton>button {
    background-color: #1a73e8;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 8px;
    font-size: 16px;
    font-weight: bold;
    font-family: 'BNazanin', Tahoma, 'IRANSansWeb', sans-serif !important;
}

footer {visibility: hidden;}
</style>
"""



st.markdown(streamlit_style, unsafe_allow_html=True)

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
            model='gemini-2.0-flash',
            contents=json.dumps(payload, ensure_ascii=False),
            config={
                'response_mime_type': 'application/json',
                'system_instruction': """
شما یک ارزیاب حرفه‌ای منابع انسانی هستید. لطفاً امتیاز را با دقت بالا و بر اساس تفاوت‌های جزئی تعیین کنید.
معیارهای دقیق ارزیابی:
- مهارت‌های نرم‌افزاری: تسلط کامل (۳۰ امتیاز)، آشنایی معمولی (۱۵)، نبود مهارت (۰)
- سوابق شغلی مرتبط: کامل (۲۰)، جزئی (۱۰)، نامرتبط (۰)
- مقطع و رشته تحصیلی: کارشناسی مرتبط (۱۵)، کارشناسی نامرتبط (۵)، زیر کارشناسی یا اطلاعات ناقص (۰)
- دانشگاه: ممتاز (۱۰)، دولتی معمولی (۵)، غیردولتی (۰)
- سن مناسب: ۲۲ تا ۳۵ سال (۱۰)، کمتر یا بیشتر (۰)
- حقوق درخواستی مناسب: ۲۰ تا ۴۵ میلیون (۱۰)، خارج از این بازه (۰)
امتیاز نهایی را از ۰ تا ۱۰۰ بده و **در حد امکان، تفاوت‌های جزئی را نیز لحاظ کن.**
اگر اطلاعات کافی نبود، بنویس: 'اطلاعات کافی نیست'.
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
        

# تبدیل کلید 'why' به 'دلیل'
        for item in result:
            if 'why' in item:
                item['دلیل'] = item.pop('why')

        return pd.DataFrame(result)

    except Exception:
        return pd.DataFrame([{
            "score": 1.0,
            "check_id": str(row[ID_COLUMN]),
            "دلیل": "خطا در پردازش یا اطلاعات ناکافی"
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
            response = safe_generate_content(
                model="gemini-2.0-flash",
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

            # شرط خاص برای job_spatial_01
            if job["id"] == "job_spatial_01":
                keywords = ['RS', 'GIS', 'نقشه‌برداری', 'نقشه کشی', 'Remote Sensing', 'Geographic Information System']
                if not any(keyword.lower() in resume_text.lower() for keyword in keywords):
                    if score >= 30:
                        reason += " (امتیاز کاهش یافت به دلیل فقدان تجربه یا دانش مرتبط با RS یا GIS)"
                        score = 25  # یا هر عدد پایین‌تر از ۳۰

                       
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
    matched_titles = []
    matched_reasons = []
    logs = []

    for _, row in batch_df.iterrows():
        resume_text = " ".join([str(row[col]) for col in batch_df.columns])
        title, reason, log = match_resume_to_job_parallel(resume_text, JOB_PROFILES)
        matched_titles.append(title)
        logs.append(log)
        matched_reasons.append(reason)

    batch_df["موقعیت شغلی پیشنهادی"] = matched_titles
    batch_df["دلیل انتخاب موقعیت شغلی"] = matched_reasons
    batch_df["گزارش بررسی شناسنامه‌ها"] = logs
    return batch_df


# --- تابع اصلاح نمره بر اساس معیارهای اضافه ---
top_universities = ['دانشگاه صنعتی شریف', 'دانشگاه تهران', 'دانشگاه صنعتی امیرکبیر', 'دانشگاه علم و صنعت ایران']
public_keywords = ['صنعتی', 'تهران', 'امیرکبیر', 'علم و صنعت', 'فردوسی', 'تبریز', 'اصفهان', 'دولتی']

def is_public_university(univ_name):
    return any(keyword in str(univ_name) for keyword in public_keywords)

def is_top_university(univ_name):
    return any(top in str(univ_name) for top in top_universities)

def color_score_column(val):
    if val >= 90:
        color = '#00C853'  # سبز پررنگ
    elif val >= 80:
        color = '#AEEA00'  # لیمویی سبز
    elif val >= 70:
        color = '#FFD600'  # زرد
    elif val >= 60:
        color = '#FF9100'  # نارنجی
    elif val >= 50:
        color = '#FF3D00'  # نارنجی-قرمز
    else:
        color = '#D50000'  # قرمز تیره
    return f'background-color: {color}; color: white; font-weight: bold'


def adjust_score(row):
    score = row['score']
    if 'سن' in row and (row['سن'] < 22 or row['سن'] > 35):
        score -= 2
    if 'حقوق درخواستی' in row and (row['حقوق درخواستی'] < 20 or row['حقوق درخواستی'] > 45):
        score -= 10
    if 'مقطع تحصیلی' in row and 'کارشناسی' not in str(row['مقطع تحصیلی']):
        score -= 5
    univ = row.get('نام دانشگاه', '')
    if is_public_university(univ):
        score += 3
    if is_top_university(univ):
        score += 10
    return max(min(score, 100), 1.0)

def process_resume_row(row):
    resume_text = " ".join([str(row[col]) for col in row.index])
    title, reason_job, log = match_resume_to_job(resume_text, JOB_PROFILES)

    # گرفتن امتیاز اولیه از Gemini
    try:
        gemini_df = process_batch(pd.DataFrame([row]), prompt_text="ارزیابی عمومی رزومه")

        if not gemini_df.empty:
            initial_score = gemini_df.iloc[0]['score'] if 'score' in gemini_df.columns else 1.0
            reason = gemini_df.iloc[0]['دلیل'] if 'دلیل' in gemini_df.columns else "توضیحی ارائه نشده است"
        else:
            initial_score = 1.0
            reason = "پاسخی از مدل دریافت نشد"

    except Exception:
        initial_score = 1.0
        reason = "خطا در دریافت امتیاز"

    score = adjust_score({**row.to_dict(), 'score': initial_score})

    # ساختن داده نهایی
    row_data = row.to_dict()
    row_data.update({
        "score": score,
        "دلیل": reason,
        "موقعیت شغلی پیشنهادی": title,
        "دلیل انتخاب موقعیت شغلی": reason_job,
        "گزارش بررسی شناسنامه‌ها": log
    })

    # ذخیره در فایل
    if RESULT_FILE_PATH.exists():
        existing = pd.read_excel(RESULT_FILE_PATH)
        updated = pd.concat([existing, pd.DataFrame([row_data])], ignore_index=True)
    else:
        updated = pd.DataFrame([row_data])

    updated.to_excel(RESULT_FILE_PATH, index=False)

    # ذخیره در session_state
    st.session_state['live_results'].append(row_data)
    return row_data



    # سپس اصلاح امتیاز بر اساس شرایط خاص
    score = adjust_score({**row.to_dict(), 'score': initial_score})

    # اطلاعات اصلی رزومه + نتایج تحلیل را ترکیب کن
    new_data = row.to_dict()
    new_data.update({
        "score": score,
        "why": gemini_df.iloc[0]['دلیل'],
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
st.markdown("<h1 style='color:#1a73e8; font-size: 40px;'>📋 سامانه هوشمند ارزیابی رزومه</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 16px; color: #555;'>ارزیابی خودکار رزومه‌ها بر اساس معیارهای منابع انسانی، شناسنامه‌های شغلی و مهارت‌های تخصصی.</p>", unsafe_allow_html=True)

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


prompt_text = st.text_input("🎯 عنوان شغلی:")
skills_text = st.text_input("🔧 مهارت‌های موردنیاز (مثلاً Python, Excel):")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df['شماره تماس'] = df['شماره تماس'].astype(str)
    stage = st.radio("🧩 مرحله موردنظر را انتخاب کنید:", ["امتیازدهی", "تطبیق با شناسنامه‌های شغلی"])
    done_ids = []

    if RESULT_FILE_PATH.exists():
        done_ids = pd.read_excel(RESULT_FILE_PATH)['شناسه'].tolist()

    if stage == "امتیازدهی":
        st.markdown("### 🚀 مرحله امتیازدهی رزومه‌ها")
        if st.button("شروع امتیازدهی"):
            results_placeholder = st.empty()
            progress_bar = st.progress(0)
            for idx, (_, row) in enumerate(df.iterrows()):
                if row[ID_COLUMN] in done_ids:
                    continue

                gemini_df = process_batch(pd.DataFrame([row]), prompt_text="ارزیابی عمومی رزومه")
                initial_score = gemini_df.iloc[0]['score']
                score = adjust_score({**row.to_dict(), 'score': initial_score})
                row_data = row.to_dict()
                row_data.update({
                    "score": score,
                    "why": gemini_df.iloc[0]['دلیل'] if not gemini_df.empty and 'دلیل' in gemini_df.columns else "دلیلی یافت نشد"
                })

                if 'تایید و رد اولیه' in row and row['تایید و رد اولیه'] in ['تایید', 'رد']:
                    row_data['تایید و رد اولیه'] = row['تایید و رد اولیه']      

                if RESULT_FILE_PATH.exists():
                    existing = pd.read_excel(RESULT_FILE_PATH)
                    updated = pd.concat([existing, pd.DataFrame([row_data])], ignore_index=True)
                else:
                    updated = pd.DataFrame([row_data])
                updated.to_excel(RESULT_FILE_PATH, index=False)

                st.session_state['live_results'].append(row_data)

                results_df = pd.DataFrame(st.session_state['live_results'])
                results_placeholder.dataframe(results_df)

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


            st.success("✅ امتیازدهی به پایان رسید.")

    elif stage == "تطبیق با شناسنامه‌های شغلی":
        st.markdown("### 🔍 مرحله تطبیق با شناسنامه‌های شغلی")
        results_placeholder = st.empty()
        progress_bar = st.progress(0)

        if 'تایید و رد اولیه' in df.columns:
            initial_count = len(df)
        df = df[df['تایید و رد اولیه'] == 'تایید']
        removed_count = initial_count - len(df)
        st.info(f"📤 {removed_count} رزومه به دلیل رد اولیه حذف شدند. {len(df)} رزومه برای تطبیق باقی ماند.")


        if st.button("🚀شروع تطبیق با شناسنامه‌های شغلی"):
            try:
            # No need to read df again, just use df already defined above
                match_results = apply_matching_to_batch(df.copy())
                match_result_file = "job_matching_results.xlsx"
                match_results.to_excel(match_result_file, index=False)
                st.success("✅ تطبیق با شناسنامه‌های شغلی انجام شد.")
                st.dataframe(match_results)
                with open(match_result_file, "rb") as f:
                    st.download_button("📥 دانلود نتایج تطبیق شناسنامه", f, file_name=match_result_file)
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

    # دکمه دانلود فایل نهایی
    with open(RESULT_FILE_PATH, "rb") as f:
        st.download_button("📥 دانلود فایل نهایی", f, file_name="resume_results.xlsx")
