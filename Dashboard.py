# ==============================================================================
# IMPORT LIBRARIES
# ==============================================================================
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import os
from datetime import datetime

# ==============================================================================
# PAGE CONFIGURATION & STYLING
# ==============================================================================
st.set_page_config(layout="wide", page_title="Patient Experience Program")

LOGO_URL = "https://raw.githubusercontent.com/HOIARRTool/hoiarr/refs/heads/main/logo1.png"

st.sidebar.markdown(
    f'<div style="display: flex; align-items: center; margin-bottom: 1rem;"><img src="{LOGO_URL}" style="height: 40px; margin-right: 10px;"><h2 style="margin: 0; font-size: 1.5rem;"><span class="gradient-text">Patient Experience Program</span></h2></div>',
    unsafe_allow_html=True)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600;700&display=swap');
    html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"], [data-testid="stPageLink"] {
        font-family: 'Kanit', sans-serif;
    }
    .gradient-text {
        background-image: linear-gradient(45deg, #007bff, #6610f2, #6f42c1, #d63384, #dc3545);
        -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
        font-weight: 700; display: inline-block;
    }
    .metric-box {
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid #e0e0e0;
        text-align: center;
        height: 100%;
        color: #4f4f4f;
    }
    .metric-box .label { font-size: 1rem; font-weight: 500; color: #555; }
    .metric-box .value { font-size: 2.2rem; font-weight: 700; }

    /* Pastel Colors */
    .metric-box-1 { background-color: #e0f7fa; } /* Light Cyan */
    .metric-box-2 { background-color: #e8f5e9; } /* Light Green */
    .metric-box-3 { background-color: #fce4ec; } /* Light Pink */
    .metric-box-4 { background-color: #fffde7; } /* Light Yellow */
    .metric-box-5 { background-color: #f3e5f5; } /* Light Purple */
    .metric-box-6 { background-color: #e3f2fd; } /* Light Blue */

    .sidebar-info {
        padding: 10px;
        background-color: #f0f2f6;
        border-radius: 5px;
        margin-bottom: 15px;
        text-align: center;
    }
    .sidebar-info .label {
        font-size: 0.9rem;
        font-weight: bold;
    }
    .sidebar-info .value {
        font-size: 0.9rem;
    }

</style>
""", unsafe_allow_html=True)

# ==============================================================================
# DATA LOADING AND PREPARATION
# ==============================================================================
DATA_FILE = "patient_satisfaction_data.csv"


def get_file_mtime(path):
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


@st.cache_data
def load_and_prepare_data(filepath, file_mtime):
    if not os.path.exists(filepath):
        return pd.DataFrame()
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์ข้อมูล: {e}")
        return pd.DataFrame()

    column_mapping = {
        'หอผู้ป่วยที่ท่านเข้ารับบริการ/ ต้องการประเมิน \n(เพื่อสะท้อนกลับหน่วยงานโดยตรง)': 'หน่วยงาน',
        'ส่วนที่ 1 ข้อมูลทั่วไปของผู้ตอบแบบประเมิน\n1. เพศ': 'เพศ',
        '2. อายุ': 'อายุ', '3. ภูมิลำเนา': 'ภูมิลำเนา', '4. อาชีพ': 'อาชีพ', '5. สิทธิในการรักษา': 'สิทธิการรักษา',
        '6. วันที่มารับบริการ': 'วันที่รับบริการ',
        'จำนวนวันนอนรักษาที่โรงพยาบาล': 'วันนอน',
        'ส่วนที่ 2 ความพึงพอใจต่อบริการของโรงพยาบาลในภาพรวม': 'ความพึงพอใจโดยรวม',
        '2. ท่านคิดว่าสุขภาพโดยรวมของท่านเป็นอย่างไร': 'สุขภาพโดยรวม',
        '1. ขั้นตอนการติดต่อและเข้ารับการรักษาในโรงพยาบาล (Admissions) มีความสะดวกเพียงใด': 'Q1_ความสะดวกการรับบริการ',
        '2. ขณะนอนโรงพยาบาลครั้งนี้ แพทย์ พยาบาลและเจ้าหน้าที่ รับฟังและเปิดโอกาสให้ท่านซักถามข้อสงสัยได้มากน้อยเพียงใด': 'Q2_การรับฟัง',
        '3. ขณะนอนโรงพยาบาลครั้งนี้ แพทย์ พยาบาลและเจ้าหน้าที่ให้ข้อมูลเกี่ยวกับขั้นตอนการรับบริการได้ชัดเจนเพียงใด': 'Q3_ความชัดเจนข้อมูลบริการ',
        '4. ขณะนอนโรงพยาบาล ท่านรู้สึกว่าบุคลากรทุกคนดูแลท่านอย่างเท่าเทียมและให้เกียรติหรือไม่': 'Q4_ความเท่าเทียม',
        '5. โรงพยาบาลมีความสะอาด และมีสิ่งอำนวยความสะดวกเพียงพอต่อความต้องการของท่าน': 'Q5_ความสะอาดและสิ่งอำนวยความสะดวก',
        '6. เมื่อท่านต้องการความช่วยเหลือ (เช่น กดปุ่มเรียกพยาบาล) ท่านได้รับตอบสนองอย่างเหมาะสม': 'Q6_การตอบสนอง',
        '7. ขณะนอนโรงพยาบาล ท่านได้รับข้อมูลเกี่ยวกับค่าใช้จ่ายที่อาจเกิดขึ้นอย่างต่อเนื่องและชัดเจนเพียงใด': 'Q7_ข้อมูลค่าใช้จ่าย',
        '8. ขณะนอนโรงพยาบาล ท่านได้รับข้อมูลการรักษา อาการแทรกซ้อนระหว่างการรักษาพยาบาล': 'Q8_ข้อมูลการรักษา',
        '9. ท่านและครอบครัว ได้มีส่วนร่วมในการวางแผนการรักษาและการปฏิบัติตัวร่วมกับ ทีมผู้ให้การรักษาอย่างเหมาะสมหรือไม่': 'Q9_การมีส่วนร่วมวางแผน',
        '10. ท่านได้รับข้อมูลยา ผลข้างเคียงของยา และวิธีการใช้ยาอย่างชัดเจนเพียงใด': 'Q10_ข้อมูลด้านยา',
        '1. หากท่านมีอาการเจ็บป่วย ท่านจะพิจารณากลับมารับบริการ ที่โรงพยาบาลแห่งนี้หรือไม่': 'กลับมารับบริการหรือไม่',
        '2. หากมีโอกาสท่านจะแนะนำผู้อื่นให้มารับบริการที่โรงพยาบาลแห่งนี้หรือไม่': 'แนะนำผู้อื่นหรือไม่',
        '3. ท่านมีความไม่พึงพอใจในการมาใช้บริการที่โรงพยาบาลนี้หรือไม่': 'มีความไม่พึงพอใจหรือไม่',
        '(หากมี) ความไม่พึงพอใจกรุณาระบุรายละเอียด เพื่อเป็นประโยชน์ในการปรับปรุง': 'รายละเอียดความไม่พึงพอใจ',
        'ข้อเสนอแนะเพิ่มเติมเพื่อการพัฒนาคุณภาพโรงพยาบาล': 'ความคาดหวังต่อบริการ'
    }
    df = df.rename(columns=lambda c: column_mapping.get(c.strip(), c.strip()))
    df['date_col'] = pd.to_datetime(df['ประทับเวลา'], errors='coerce')
    df = df.dropna(subset=['date_col'])
    df['เดือน'] = df['date_col'].dt.month
    df['ไตรมาส'] = df['date_col'].dt.quarter
    df['ปี'] = df['date_col'].dt.year
    return df


# ==============================================================================
# PLOTTING FUNCTIONS
# ==============================================================================
def plot_satisfaction_pie_chart(df, column_name, title):
    if column_name not in df.columns or df[column_name].dropna().empty: return
    category_order = ['น้อยมาก', 'น้อย', 'ปานกลาง', 'มาก', 'มากที่สุด']
    counts = df[column_name].value_counts().reindex(category_order).dropna().reset_index()
    counts.columns = [column_name, 'จำนวน']
    fig = px.pie(counts, names=column_name, values='จำนวน', title=title, color=column_name,
                 color_discrete_map={"น้อยมาก": "#dc3545", "น้อย": "#ffc107", "ปานกลาง": "#6c757d", "มาก": "#17a2b8",
                                     "มากที่สุด": "#28a745"},
                 category_orders={column_name: category_order})
    fig.update_traces(textposition='inside', textinfo='percent+label', showlegend=True)
    st.plotly_chart(fig, use_container_width=True)


def plot_generic_pie_chart(df, column_name, title):
    if column_name not in df.columns or df[column_name].dropna().empty:
        st.info(f"ไม่มีข้อมูลสำหรับ '{title}'")
        return
    counts = df[column_name].value_counts().reset_index()
    counts.columns = [column_name, 'จำนวน']
    fig = px.pie(counts, names=column_name, values='จำนวน', title=title)
    fig.update_traces(textposition='inside', textinfo='percent+label', showlegend=True)
    st.plotly_chart(fig, use_container_width=True)


# ==============================================================================
# MAIN APP LAYOUT
# ==============================================================================

file_modification_time = get_file_mtime(DATA_FILE)
df_original = load_and_prepare_data(DATA_FILE, file_modification_time)

if df_original.empty:
    st.warning("ยังไม่มีข้อมูล, กรุณาไปที่หน้า 'Admin Upload' เพื่ออัปโหลดไฟล์ข้อมูลก่อน")
    st.stop()

# --- Sidebar ---
st.sidebar.markdown("---")
min_date = df_original['date_col'].min().strftime('%d %b %Y')
max_date = df_original['date_col'].max().strftime('%d %b %Y')
st.sidebar.markdown(f"""
<div class="sidebar-info">
    <div class="label">ช่วงวันที่ของข้อมูล</div>
    <div class="value">{min_date} - {max_date}</div>
</div>
""", unsafe_allow_html=True)
st.sidebar.header("ตัวกรองข้อมูล (Filter)")
available_departments = ['ภาพรวมทั้งหมด'] + sorted(df_original['หน่วยงาน'].dropna().unique().tolist())
selected_department = st.sidebar.selectbox("เลือกหน่วยงาน:", available_departments)
time_filter_option = st.sidebar.selectbox("เลือกช่วงเวลา:",
                                          ["ทั้งหมด", "เลือกตามปี", "เลือกตามไตรมาส", "เลือกตามเดือน"])
df_filtered = df_original.copy()
if time_filter_option != "ทั้งหมด":
    year_list = sorted(df_original['ปี'].unique(), reverse=True)
    selected_year = st.sidebar.selectbox("เลือกปี:", year_list)
    df_filtered = df_original[df_original['ปี'] == selected_year]
    if time_filter_option in ["เลือกตามไตรมาส", "เลือกตามเดือน"]:
        if time_filter_option == "เลือกตามไตรมาส":
            quarter_list = sorted(df_filtered['ไตรมาส'].unique())
            selected_quarter = st.sidebar.selectbox("เลือกไตรมาส:", quarter_list)
            df_filtered = df_filtered[df_filtered['ไตรมาส'] == selected_quarter]
        elif time_filter_option == "เลือกตามเดือน":
            month_map = {1: 'ม.ค.', 2: 'ก.พ.', 3: 'มี.ค.', 4: 'เม.ย.', 5: 'พ.ค.', 6: 'มิ.ย.', 7: 'ก.ค.', 8: 'ส.ค.',
                         9: 'ก.ย.', 10: 'ต.ค.', 11: 'พ.ย.', 12: 'ธ.ค.'}
            month_list = sorted(df_filtered['เดือน'].unique())
            selected_month_num = st.sidebar.selectbox("เลือกเดือน:", month_list,
                                                      format_func=lambda x: month_map.get(x, x))
            df_filtered = df_filtered[df_filtered['เดือน'] == selected_month_num]
if selected_department != 'ภาพรวมทั้งหมด':
    df_filtered = df_filtered[df_filtered['หน่วยงาน'] == selected_department]
if df_filtered.empty:
    st.warning("ไม่พบข้อมูลตามตัวกรองที่ท่านเลือก")
    st.stop()

# --- Page Content ---
st.title(f"DASHBOARD: {selected_department}")

# --- คำนวณ Metrics ---
satisfaction_score_map = {'มากที่สุด': 5, 'มาก': 4, 'ปานกลาง': 3, 'น้อย': 2, 'น้อยมาก': 1}
df_filtered['คะแนนความพึงพอใจ'] = df_filtered['ความพึงพอใจโดยรวม'].map(satisfaction_score_map)
average_satisfaction_score = df_filtered['คะแนนความพึงพอใจ'].mean()
display_avg_satisfaction = f"{average_satisfaction_score:.2f}" if pd.notna(average_satisfaction_score) else "N/A"
total_responses = len(df_filtered)

def calculate_percentage(df, col_name, positive_value='ใช่', decimals=1):
    if col_name in df.columns and not df[col_name].dropna().empty:
        count = (df[col_name] == positive_value).sum()
        total_count = df[col_name].notna().sum()
        if total_count > 0:
            return f"{(count / total_count) * 100:.{decimals}f}%"
    return "N/A"

return_service_pct = calculate_percentage(df_filtered, 'กลับมารับบริการหรือไม่', decimals=1)
recommend_pct = calculate_percentage(df_filtered, 'แนะนำผู้อื่นหรือไม่', decimals=1)
dissatisfied_pct = calculate_percentage(df_filtered, 'มีความไม่พึงพอใจหรือไม่', positive_value='มี', decimals=2)

most_common_health_status = df_filtered['สุขภาพโดยรวม'].mode()[0] if 'สุขภาพโดยรวม' in df_filtered.columns and not \
df_filtered['สุขภาพโดยรวม'].dropna().empty else "N/A"

st.markdown("##### ภาพรวม")
row1 = st.columns(3)
row2 = st.columns(3)
with row1[0]: st.markdown(
    f'<div class="metric-box metric-box-1"><div class="label">จำนวนผู้ตอบ</div><div class="value">{total_responses:,}</div></div>',
    unsafe_allow_html=True)
with row1[1]: st.markdown(
    f'<div class="metric-box metric-box-2"><div class="label">คะแนนพึงพอใจเฉลี่ย</div><div class="value">{display_avg_satisfaction}</div></div>',
    unsafe_allow_html=True)
with row1[2]: st.markdown(
    f'<div class="metric-box metric-box-6"><div class="label">สุขภาพผู้ป่วยโดยรวม</div><div class="value" style="font-size: 1.8rem;">{most_common_health_status}</div></div>',
    unsafe_allow_html=True)
with row2[0]: st.markdown(
    f'<div class="metric-box metric-box-3"><div class="label">% กลับมาใช้บริการ</div><div class="value">{return_service_pct}</div></div>',
    unsafe_allow_html=True)
with row2[1]: st.markdown(
    f'<div class="metric-box metric-box-4"><div class="label">% การบอกต่อ</div><div class="value">{recommend_pct}</div></div>',
    unsafe_allow_html=True)
with row2[2]: st.markdown(
    f'<div class="metric-box metric-box-5"><div class="label">% ไม่พึงพอใจ</div><div class="value">{dissatisfied_pct}</div></div>',
    unsafe_allow_html=True)
st.markdown("---")

# ==============================================================================
# ***** ส่วนที่เพิ่มเข้ามาใหม่ *****
# ==============================================================================
if selected_department == 'ภาพรวมทั้งหมด':
    st.subheader("สรุปจำนวนการประเมินตามหน่วยงาน")
    evaluation_counts = df_filtered['หน่วยงาน'].value_counts().reset_index()
    evaluation_counts.columns = ['หน่วยงาน', 'จำนวนการประเมิน']
    st.dataframe(evaluation_counts, use_container_width=True, hide_index=True)
    st.markdown("---")
# ==============================================================================
# ***** จบส่วนที่เพิ่มเข้ามาใหม่ *****
# ==============================================================================

st.header("ส่วนที่ 2: ความพึงพอใจต่อบริการ (รายหัวข้อ)")
satisfaction_cols = {
    'Q1_ความสะดวกการรับบริการ': '1. ความสะดวกในการติดต่อและเข้ารับบริการ',
    'Q2_การรับฟัง': '2. การรับฟังและเปิดโอกาสให้ซักถาม',
    'Q3_ความชัดเจนข้อมูลบริการ': '3. ความชัดเจนของข้อมูลขั้นตอนบริการ',
    'Q4_ความเท่าเทียม': '4. การดูแลอย่างเท่าเทียมและให้เกียรติ',
    'Q5_ความสะอาดและสิ่งอำนวยความสะดวก': '5. ความสะอาดและสิ่งอำนวยความสะดวก',
    'Q6_การตอบสนอง': '6. การตอบสนองเมื่อต้องการความช่วยเหลือ',
    'Q7_ข้อมูลค่าใช้จ่าย': '7. ความชัดเจนของข้อมูลค่าใช้จ่าย',
    'Q8_ข้อมูลการรักษา': '8. การได้รับข้อมูลการรักษาและอาการแทรกซ้อน',
    'Q9_การมีส่วนร่วมวางแผน': '9. การมีส่วนร่วมในการวางแผนการรักษา', 'Q10_ข้อมูลด้านยา': '10. ความชัดเจนของข้อมูลด้านยา'
}
col_pairs = [list(satisfaction_cols.items())[i:i + 2] for i in range(0, len(satisfaction_cols), 2)]
for pair in col_pairs:
    cols = st.columns(2)
    for i, (col_name, title) in enumerate(pair):
        with cols[i]:
            plot_generic_pie_chart(df_filtered, col_name, title)

st.markdown("---")
st.header("ส่วนที่ 3: ความตั้งใจในอนาคตและข้อเสนอแนะ")
col1_future, col2_future = st.columns(2)
with col1_future:
    plot_generic_pie_chart(df_filtered, 'กลับมารับบริการหรือไม่', '1. หากเจ็บป่วยจะกลับมารับบริการหรือไม่')
with col2_future:
    plot_generic_pie_chart(df_filtered, 'แนะนำผู้อื่นหรือไม่', '2. จะแนะนำผู้อื่นให้มารับบริการหรือไม่')

st.subheader("รายละเอียดความไม่พึงพอใจ (หากมี)")
if 'รายละเอียดความไม่พึงพอใจ' in df_filtered.columns:
    temp_df = df_filtered[['หน่วยงาน', 'รายละเอียดความไม่พึงพอใจ']].copy()
    temp_df.dropna(subset=['รายละเอียดความไม่พึงพอใจ'], inplace=True)
    temp_df['details_stripped'] = temp_df['รายละเอียดความไม่พึงพอใจ'].astype(str).str.strip()
    dissatisfaction_df = temp_df[
        (temp_df['details_stripped'] != '') &
        (temp_df['details_stripped'] != 'ไม่มี')
        ]

    if not dissatisfaction_df.empty:
        st.dataframe(dissatisfaction_df[['หน่วยงาน', 'รายละเอียดความไม่พึงพอใจ']], use_container_width=True,
                     hide_index=True)
    else:
        st.info("ไม่พบรายละเอียดความไม่พึงพอใจในช่วงข้อมูลที่เลือก")

st.subheader("ความคาดหวังต่อบริการของโรงพยาบาลในภาพรวม")
if 'ความคาดหวังต่อบริการของโรงพยาบาลในภาพรวม' in df_filtered.columns:
    suggestions_df = df_filtered[df_filtered['ความคาดหวังต่อบริการของโรงพยาบาลในภาพรวม'].notna()][['หน่วยงาน', 'ความคาดหวังต่อบริการของโรงพยาบาลในภาพรวม']]
    if not suggestions_df.empty:
        st.dataframe(suggestions_df, use_container_width=True, hide_index=True)
    else:
        st.info("ไม่พบข้อมูลความคาดหวังในช่วงข้อมูลที่เลือก")