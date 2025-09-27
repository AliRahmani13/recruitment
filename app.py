# تغییرات لازم در app.py برای حذف وابستگی به ستون "شناسه"

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

# تنظیمات کلی
pd.set_option('display.max_rows', None)
OUTPUT_ALL_PATH = Path("recruitment_score.xlsx")

# **تغییر مهم: استفاده از ایندکس به جای ستون شناسه**
# ID_COLUMN = 'شناسه'  # حذف این خط
BATCH_SIZE = 10
RESULT_FILE_PATH = Path("resume_results.xlsx")

# بقیه کد همان کدهای قبلی...
API_KEYS = [
    "AIzaSyAQ1Z8HmIZm-eNvohxoM4ZNFM8JsZsxDII",
    "AIzaSyAQhK01WbSxiXUdXqe5xEvJA3feUiQCL0E",
    # ... سایر کلیدها
]

# تابع کمکی برای تولید شناسه یکتا
def generate_unique_id(row_index, row_data):
    """تولید شناسه یکتا برای هر ردیف"""
    # اولویت اول: استفاده از شماره تماس
    if 'شماره تماس' in row_data and row_data['شماره تماس']:
        return str(row_data['شماره تماس'])
    
    # اولویت دوم: استفاده از ترکیب نام و نام خانوادگی
    if 'نام' in row_data and 'نام خانوادگی' in row_data:
        name_combo = f"{row_data['نام']}_{row_data['نام خانوادگی']}"
        return name_combo.replace(' ', '_')
    
    # اولویت سوم: استفاده از ایمیل
    if 'ایمیل' in row_data and row_data['ایمیل']:
        return str(row_data['ایمیل']).split('@')[0]
    
    # اولویت چهارم: ایندکس ردیف
    return f"ROW_{row_index}"

def get_row_id(row, row_index):
    """دریافت شناسه برای یک ردیف"""
    # اگر ستون شناسه وجود دارد، از آن استفاده کن
    if 'شناسه' in row and row['شناسه']:
        return str(row['شناسه'])
    
    # در غیر این صورت، شناسه جدید تولید کن
    return generate_unique_id(row_index, row)

# تابع اصلاح شده برای پردازش batch
def process_batch(batch_df, prompt_text):
    payload = {
        "employer requirements": prompt_text,
        "applicant information": []
    }
    
    for idx, (_, row) in enumerate(batch_df.iterrows()):
        resume_text = " ".join([str(row[col]) for col in batch_df.columns])
        row_id = get_row_id(row, idx)
        
        payload["applicant information"].append({
            "resume": resume_text, 
            "id": row_id
        })
    
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
        # در صورت خطا، برای همه ردیف‌ها پاسخ پیش‌فرض بده
        default_results = []
        for idx, (_, row) in enumerate(batch_df.iterrows()):
            row_id = get_row_id(row, idx)
            default_results.append({
                "score": 1.0,
                "check_id": row_id,
                "why": "خطا در پردازش - اطلاعات کافی نیست"
            })
        return pd.DataFrame(default_results)

def apply_matching_to_batch(batch_df):
    all_results = []
    
    for idx, (_, row) in enumerate(batch_df.iterrows()):
        resume_text = " ".join([str(row[col]) for col in batch_df.columns])
        match_df = evaluate_resume_against_all_jobs(resume_text, JOB_PROFILES)
        
        # استفاده از تابع جدید برای شناسه
        row_id = get_row_id(row, idx)
        match_df["شناسه رزومه"] = row_id
        match_df["نام"] = row.get("نام", "")
        match_df["نام خانوادگی"] = row.get("نام خانوادگی", "")
        
        all_results.append(match_df)
    
    return pd.concat(all_results, ignore_index=True)

def process_resume_row(row, row_index):
    resume_text = " ".join([str(row[col]) for col in row.index])
    title, reason, log = match_resume_to_job(resume_text, JOB_PROFILES)
    
    # گرفتن امتیاز اولیه از Gemini
    gemini_df = process_batch(pd.DataFrame([row]), prompt_text="ارزیابی عمومی رزومه")
    initial_score = gemini_df.iloc[0]['score']
    
    # اصلاح امتیاز
    score = adjust_score({**row.to_dict(), 'score': initial_score})
    
    # شناسه برای این ردیف
    row_id = get_row_id(row, row_index)
    
    new_data = row.to_dict()
    new_data.update({
        "شناسه": row_id,  # اضافه کردن شناسه به داده‌ها
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
    
    # ذخیره در session
    if 'live_results' not in st.session_state:
        st.session_state['live_results'] = []
    st.session_state['live_results'].append(new_data)
    
    return new_data

# تابع اصلاح شده برای مدیریت done_ids
def get_done_ids():
    """دریافت لیست شناسه‌های پردازش شده"""
    if RESULT_FILE_PATH.exists():
        existing_df = pd.read_excel(RESULT_FILE_PATH)
        if 'شناسه' in existing_df.columns:
            return existing_df['شناسه'].tolist()
        else:
            # اگر ستون شناسه وجود نداشت، از ایندکس استفاده کن
            return [f"ROW_{i}" for i in existing_df.index]
    return []

# بخش اصلی که نیاز به تغییر دارد
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    stage = st.radio("🧩 مرحله موردنظر را انتخاب کنید:", ["امتیازدهی", "تطبیق با شناسنامه‌های شغلی"])
    done_ids = get_done_ids()  # استفاده از تابع جدید

    if stage == "امتیازدهی": 
        st.markdown("### 🚀 مرحله امتیازدهی رزومه‌ها") 
        if st.button("شروع امتیازدهی"): 
            results_placeholder = st.empty() 
            progress_bar = st.progress(0) 
            rows = [] 
            
            for idx, (_, row) in enumerate(df.iterrows()): 
                current_row_id = get_row_id(row, idx)
                
                # بررسی اینکه آیا این ردیف قبلاً پردازش شده یا نه
                if current_row_id in done_ids: 
                    continue

                resume = " ".join([str(row[col]) for col in row.index]) 
                skills = all_skills
                required_experience_desc = "سابقه مرتبط با عنوان شغلی" 
                universities = universities_info 
                major_list = []
                job_profile_title = ""
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
                row_data['شناسه'] = current_row_id  # اضافه کردن شناسه
                
                for agent, detail in results.items():
                    if agent != "FinalScore":
                        row_data[f"{agent}_score"] = detail['score']
                        row_data[f"{agent}_reason"] = detail['reason']
                row_data['final_score'] = results['FinalScore']

                row_data['تایید و رد اولیه'] = "تایید" if row_data['final_score'] >= 70 else "رد"
                rows.append(row_data)

                progress_bar.progress((idx + 1) / len(df))

            # ذخیره و نمایش نتایج
            results_df = pd.DataFrame(rows)
            results_placeholder.dataframe(results_df)
            results_df.to_excel("resume_scoring.xlsx", index=False)
            style_excel("resume_scoring.xlsx")

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
                summary_path = "job_matching_summary.xlsx"
                summary_df.to_excel(summary_path, index=False)
                style_excel(summary_path)

                st.success("✅ تطبیق با شناسنامه‌های شغلی با موفقیت انجام شد.")
                st.dataframe(summary_df)

                with open(summary_path, "rb") as f:
                    st.download_button("📥 دانلود فایل نهایی تحلیل‌شده", f, file_name=summary_path)
            
            except Exception as e:
                st.error(f"❌ خطا در انجام تطبیق: {e}")

# نمایش نتایج نهایی
if RESULT_FILE_PATH.exists():
    final_df = pd.read_excel(RESULT_FILE_PATH)
    
    # اطمینان از وجود ستون شناسه
    if 'شناسه' not in final_df.columns:
        final_df['شناسه'] = [generate_unique_id(i, row) for i, (_, row) in enumerate(final_df.iterrows())]
        # ذخیره مجدد فایل با ستون شناسه
        final_df.to_excel(RESULT_FILE_PATH, index=False)

    display_df = final_df.copy()
    display_df.index = display_df.index + 1
    display_df.index.name = "ردیف"

    st.markdown("### ✅ جدول نهایی رزومه‌های بررسی‌شده")
    
    if 'score' in display_df.columns:
        styled_df = display_df.style.applymap(color_score_column, subset=['score'])
        st.dataframe(styled_df)
    else:
        st.dataframe(display_df)

    style_excel(RESULT_FILE_PATH)
    
    with open(RESULT_FILE_PATH, "rb") as f:
        st.download_button("📥 دانلود فایل نهایی", f, file_name="resume_results.xlsx")
