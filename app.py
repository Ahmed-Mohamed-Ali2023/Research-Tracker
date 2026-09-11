import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import os
from datetime import datetime

# إعدادات الصفحة والمراحل
st.set_page_config(page_title="نظام النشر", layout="wide")
st.title("📊 سيستم متابعة نشر الأبحاث (متصل بـ Google Sheets)")

STAGES = ["الترشيح والتسعير", "موافقة العميل", "تأكيد التنسيق", "التقديم للمجلة", "التحكيم والتعديلات", "الدفع والقبول", "النشر"]

# ----------------- دالة الاتصال بجوجل شيت -----------------
@st.cache_resource
def get_sheet():
    creds_json = os.environ.get("GCP_CREDENTIALS")
    if not creds_json:
        st.error("⚠️ لم يتم العثور على المفتاح السري GCP_CREDENTIALS في الإعدادات.")
        st.stop()
    
    creds_dict = json.loads(creds_json)
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    
    return client.open("Research_Tracker").sheet1

# تحميل البيانات من الشيت
sheet = get_sheet()
data = sheet.get_all_records()
df = pd.DataFrame(data)

# ----------------- تقسيم الواجهة -----------------
tab1, tab2, tab3 = st.tabs(["📋 لوحة المتابعة", "➕ إضافة بحث", "⚙️ تحديث حالة وتكاليف"])

# ----------------- التبويب الأول: المتابعة -----------------
with tab1:
    if not df.empty:
        def get_progress(stage_name):
            if stage_name in STAGES:
                idx = STAGES.index(stage_name)
                return min((idx + 1) / len(STAGES), 1.0)
            return 0.0

        df['نسبة الإنجاز'] = df.get('المرحلة', pd.Series([''] * len(df))).apply(get_progress)
        
        st.success(f"إجمالي الأبحاث الحالية: {len(df)}")
        
        st.data_editor(
            df,
            column_config={
                "نسبة الإنجاز": st.column_config.ProgressColumn("التقدم", format="%.2f", min_value=0, max_value=1)
            },
            hide_index=True, use_container_width=True
        )
    else:
        st.info("لا توجد أبحاث مسجلة حتى الآن. اذهب إلى التبويب التالي لإضافة بحث.")

# ----------------- التبويب الثاني: إضافة بحث -----------------
with tab2:
    with st.form("add_form"):
        col1, col2 = st.columns(2)
        code = col1.text_input("كود البحث (مثال: RES-001)")
        date_received = st.date_input("تاريخ الاستلام", datetime.today())
        
        title = st.text_input("عنوان البحث")
        researcher = st.text_input("اسم الباحث")
        journal = st.text_input("اسم المجلة (يمكن تركه فارغاً)")
        
        col3, col4 = st.columns(2)
        initial_cost = col3.number_input("التكلفة المبدئية", min_value=0.0, value=0.0)
        final_cost = col4.number_input("التكلفة النهائية", min_value=0.0, value=0.0)
        
        if st.form_submit_button("حفظ البحث الجديد", type="primary"):
            if code and title and researcher:
                new_row = [
                    code, str(date_received), title, researcher, 
                    journal, initial_cost, final_cost, STAGES[0]
                ]
                sheet.append_row(new_row)
                st.success("تمت الإضافة بنجاح! تم حفظ البيانات في Google Sheets.")
                st.rerun()
            else:
                st.error("الرجاء إدخال كود البحث، العنوان، واسم الباحث كحد أدنى.")

# ----------------- التبويب الثالث: تحديث الحالة والتكاليف -----------------
with tab3:
    if not df.empty:
        research_dict = dict(zip(df['كود البحث'].astype(str) + " | " + df['الباحث'].astype(str), df['كود البحث'].astype(str)))
        selected_display = st.selectbox("🔍 اختر البحث لتحديثه:", list(research_dict.keys()))
        selected_code = research_dict[selected_display]
        
        current_data = df[df['كود البحث'].astype(str) == selected_code].iloc[0]
        
        st.markdown("---")
        current_stage = current_data.get('المرحلة', STAGES[0])
        stage_idx = STAGES.index(current_stage) if current_stage in STAGES else 0
        
        new_stage = st.selectbox("➡️ اختر المرحلة الجديدة للبحث:", STAGES, index=stage_idx)
        new_journal = st.text_input("اسم المجلة:", value=str(current_data.get('اسم المجلة', '')))
        
        col5, col6 = st.columns(2)
        
        try:
            curr_initial = float(current_data.get('التكلفة المبدئية', 0))
        except:
            curr_initial = 0.0
        try:
            curr_final = float(current_data.get('التكلفة النهائية', 0))
        except:
            curr_final = 0.0
            
        new_initial_cost = col5.number_input("التكلفة المبدئية:", value=curr_initial)
        new_final_cost = col6.number_input("التكلفة النهائية:", value=curr_final)
        
        if st.button("💾 حفظ التحديثات"):
            try:
                cell = sheet.find(selected_code)
                if cell:
                    sheet.update_cell(cell.row, 5, new_journal)
                    sheet.update_cell(cell.row, 6, new_initial_cost)
                    sheet.update_cell(cell.row, 7, new_final_cost)
                    sheet.update_cell(cell.row, 8, new_stage)
                    
                    st.success("تم تحديث بيانات البحث بنجاح في Google Sheets!")
                    st.rerun()
                else:
                    st.error("لم يتم العثور على هذا البحث في الشيت.")
            except Exception as e:
                st.error(f"حدث خطأ أثناء التحديث: {e}")