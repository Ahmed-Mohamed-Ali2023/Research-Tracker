import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import os
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="نظام النشر", layout="wide")

# تطبيق خط Cairo الداكن، تقليل المسافات، وتنسيق التبويبات
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@600;800;900&display=swap');
    
    html, body, [class*="css"], .stDataFrame {
        font-family: 'Cairo', sans-serif !important;
        color: #1a1a1a !important; 
    }
    
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        max-width: 95% !important;
    }
    
    /* تنسيق التبويبات (Tabs) */
    button[data-baseweb="tab"] {
        font-family: 'Cairo', sans-serif !important;
        font-size: 20px !important;
        font-weight: 800 !important;
        padding: 12px 24px !important;
        background-color: #1e1e1e !important;
        color: #9e9e9e !important;
        border-radius: 8px 8px 0 0 !important;
        border: 1px solid #333 !important;
        border-bottom: none !important;
        margin-right: 5px !important;
        transition: all 0.3s ease !important;
    }
    
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #2196f3 !important;
        color: #ffffff !important;
        border: 1px solid #2196f3 !important;
        box-shadow: 0 -4px 10px rgba(33, 150, 243, 0.3) !important;
    }
    
    button[data-baseweb="tab"]:hover {
        background-color: #333 !important;
        color: #fff !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 المنصة الذكية لإدارة ومتابعة نشر الأبحاث")

# التحقق من الرابط السري (هل المستخدم هو الأدمن؟)
is_admin = st.query_params.get("mode") == "admin"

STAGES = ["الترشيح والتسعير", "موافقة العميل", "التقديم للمجلة", "قيد التحكيم", "التعديلات", "الدفع والقبول", "النشر"]

# ----------------- دالة الاتصال بجوجل شيت -----------------
@st.cache_resource
def get_sheet():
    creds_json = os.environ.get("GCP_CREDENTIALS")
    if not creds_json:
        st.error("⚠️ لم يتم العثور على المفتاح السري GCP_CREDENTIALS.")
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

# ----------------- تقسيم الواجهة بناءً على الصلاحيات -----------------
if is_admin:
    # واجهة الأدمن (كاملة)
    tab1, tab2, tab3 = st.tabs(["📋 لوحة المتابعة", "➕ إضافة بحث", "⚙️ تحديث حالة وتكاليف"])
    dashboard_view = tab1
else:
    # واجهة المدير (مشاهدة فقط)
    st.info("👁️ وضع المشاهدة: لوحة المتابعة والإحصائيات")
    dashboard_view = st.container()

# ----------------- الكود الخاص بلوحة المتابعة (يظهر للجميع) -----------------
with dashboard_view:
    if not df.empty:
        total_research = len(df)
        completed_research = len(df[df['المرحلة'] == "النشر"])
        in_progress_research = total_research - completed_research
        
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        
        with col_stat1:
            st.markdown(f"""
            <div style="background-color: #1e1e1e; padding: 15px; border-radius: 8px; border-top: 4px solid #4caf50; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px;">
                <h4 style="margin:0; color: #e0e0e0; font-family: 'Cairo', sans-serif;">المكتملة 🟢</h4>
                <h1 style="margin:0; color: #4caf50; font-family: 'Cairo', sans-serif;">{completed_research}</h1>
            </div>
            """, unsafe_allow_html=True)
            
        with col_stat2:
            st.markdown(f"""
            <div style="background-color: #1e1e1e; padding: 15px; border-radius: 8px; border-top: 4px solid #f44336; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px;">
                <h4 style="margin:0; color: #e0e0e0; font-family: 'Cairo', sans-serif;">قيد العمل 🔴</h4>
                <h1 style="margin:0; color: #f44336; font-family: 'Cairo', sans-serif;">{in_progress_research}</h1>
            </div>
            """, unsafe_allow_html=True)
            
        with col_stat3:
            st.markdown(f"""
            <div style="background-color: #1e1e1e; padding: 15px; border-radius: 8px; border-top: 4px solid #2196f3; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px;">
                <h4 style="margin:0; color: #e0e0e0; font-family: 'Cairo', sans-serif;">إجمالي الأبحاث 📊</h4>
                <h1 style="margin:0; color: #2196f3; font-family: 'Cairo', sans-serif;">{total_research}</h1>
            </div>
            """, unsafe_allow_html=True)

        def get_progress(stage_name):
            if stage_name in STAGES:
                idx = STAGES.index(stage_name)
                return min((idx + 1) / len(STAGES), 1.0)
            return 0.0
            
        def get_color_indicator(stage_name):
            if stage_name == "النشر":
                return "🟢 مكتمل"
            elif stage_name == "الدفع والقبول":
                return "🟡 قبول"
            else:
                return "🔴 قيد العمل"

        def style_indicator_column(val):
            if val == "🟢 مكتمل":
                return 'color: #4caf50; font-weight: bold; background-color: rgba(76, 175, 80, 0.15);'
            elif val == "🟡 قبول":
                return 'color: #ffb300; font-weight: bold; background-color: rgba(255, 179, 0, 0.15);'
            elif val == "🔴 قيد العمل":
                return 'color: #f44336; font-weight: bold; background-color: rgba(244, 67, 54, 0.15);'
            return ''

        df['نسبة الإنجاز'] = df.get('المرحلة', pd.Series([''] * len(df))).apply(get_progress)
        df['المؤشر'] = df.get('المرحلة', pd.Series([''] * len(df))).apply(get_color_indicator)
        
        columns_order = ['كود البحث', 'تاريخ الاستلام', 'عنوان البحث', 'الباحث', 'اسم المجلة', 'التكلفة المبدئية', 'التكلفة النهائية', 'المرحلة', 'المؤشر', 'نسبة الإنجاز']
        available_columns = [col for col in columns_order if col in df.columns]
        df = df[available_columns]
        
        styled_df = df.style.set_properties(**{'text-align': 'center', 'font-family': 'Cairo'})
        
        styled_df = styled_df.set_properties(subset=['المرحلة'], **{
            'background-color': 'rgba(33, 150, 243, 0.15)', 
            'color': '#64b5f6', 
            'font-weight': 'bold'
        })
        
        styled_df = styled_df.set_table_styles([
            {'selector': 'th', 'props': [
                ('font-weight', '900'), 
                ('font-size', '16px'), 
                ('color', '#000000'), 
                ('background-color', '#dbeafe'), 
                ('text-align', 'center')
            ]}
        ])
        
        styled_df = styled_df.apply(lambda x: [style_indicator_column(v) for v in x], subset=['المؤشر'])
        
        st.dataframe(
            styled_df,
            column_config={
                "نسبة الإنجاز": st.column_config.ProgressColumn("التقدم", format="%.2f", min_value=0, max_value=1),
                "المؤشر": st.column_config.TextColumn("حالة البحث")
            },
            hide_index=True, use_container_width=True
        )
    else:
        st.info("لا توجد أبحاث مسجلة حتى الآن.")

# ----------------- الإضافة والتعديل (تظهر للأدمن فقط) -----------------
if is_admin:
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

    with tab3:
        if not df.empty:
            display_names = df['كود البحث'].astype(str) + " | " + df['الباحث'].astype(str)
            research_dict = dict(zip(display_names, df['كود البحث'].astype(str)))
            
            selected_display = st.selectbox("🔍 اختر البحث:", list(research_dict.keys()))
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
            
            if st.button("💾 حفظ التحديثات", use_container_width=True):
                try:
                    cell = sheet.find(selected_code)
                    if cell:
                        sheet.update_cell(cell.row, 5, new_journal)
                        sheet.update_cell(cell.row, 6, new_initial_cost)
                        sheet.update_cell(cell.row, 7, new_final_cost)
                        sheet.update_cell(cell.row, 8, new_stage)
                        
                        st.success("تم تحديث بيانات البحث بنجاح!")
                        st.rerun()
                    else:
                        st.error("لم يتم العثور على هذا البحث في الشيت.")
                except Exception as e:
                    st.error(f"حدث خطأ أثناء التحديث: {e}")
