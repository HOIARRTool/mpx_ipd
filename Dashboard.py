# ==============================================================================
# IMPORT LIBRARIES
# ==============================================================================
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import os
from datetime import datetime
import re
from typing import Optional, Tuple, Any

# ==============================================================================
# PAGE CONFIGURATION
# ==============================================================================
# ต้องใส่บรรทัดนี้เป็นคำสั่งแรกของ Streamlit เสมอ
st.set_page_config(layout="wide", page_title="Patient Experience Program [IPD]")

# แก้ไขลิงก์: ตัด 'refs/heads/' ออก ให้เหลือแค่ 'main'
LOGO_URL = "https://raw.githubusercontent.com/HOIARRTool/hoiarr/main/logo1.png"

st.sidebar.markdown(
    f'''
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem;">
        <img src="{LOGO_URL}" style="height:40px;display:block;">
        <h2 style="margin:0;font-size:1.5rem;">
            <span class="gradient-text">Patient Experience Program [IPD]</span>
        </h2>
    </div>
    ''',
    unsafe_allow_html=True
)

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

    /* Metric cards (พาสเทล + มุมมน) */
    .metric-box {
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 14px;
        border: 1px solid #e5e7eb;
        text-align: center;
        height: 100%;
        color: #4f4f4f;
        box-shadow: 0 2px 6px rgba(0,0,0,.05);
        background: transparent;
    }
    .metric-box-1 { background:#e0f7fa !important; }
    .metric-box-2 { background:#e8f5e9 !important; }
    .metric-box-3 { background:#fce4ec !important; }
    .metric-box-4 { background:#fffde7 !important; }
    .metric-box-5 { background:#f3e5f5 !important; }
    .metric-box-6 { background:#e3f2fd !important; }
    .metric-box .label { font-size: 1.05rem; font-weight: 600; color: #475569; margin-bottom: 6px; }
    .metric-box .value { font-size: 2.4rem; font-weight: 800; line-height: 1.1; }

    .sidebar-info {
        padding: 10px;
        background-color: #f0f2f6;
        border-radius: 5px;
        margin-bottom: 15px;
        text-align: center;
    }
    .sidebar-info .label { font-size: 0.9rem; font-weight: bold; }
    .sidebar-info .value { font-size: 0.9rem; }
    .sidebar-info .source { font-size: 0.8rem; color: #555; margin-top: 5px; }


    /* หัวข้อเกจ + n */
    .gauge-head {
        font-size: 18px; font-weight: 700; color: #111;
        line-height: 1.25; margin: 2px 4px 6px;
        white-space: normal; word-break: break-word;
    }
    .gauge-sub  {
        font-size: 16px; font-weight: 600;
        color: #374151; margin: 0 4px 6px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# DATA LOADING AND PREPARATION (*** MODIFIED SECTION ***)
# ==============================================================================
@st.cache_data(ttl=300)
def load_and_prepare_data(source: Any) -> pd.DataFrame:
    """
    Loads data from a file path or a Streamlit UploadedFile object.
    Supports both .csv and .xlsx formats.
    """
    if source is None:
        return pd.DataFrame()
    try:
        # Determine the file type and read the data into a DataFrame
        if isinstance(source, str): # File path
            if source.lower().endswith('.xlsx'):
                df = pd.read_excel(source)
            else: # Assume CSV for other string paths
                df = pd.read_csv(source)
        else: # UploadedFile object from Streamlit
            if source.name.lower().endswith('.xlsx'):
                df = pd.read_excel(source)
            else: # Assume CSV
                df = pd.read_csv(source)

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์ข้อมูล: {e}")
        return pd.DataFrame()

    # --- Data Cleaning and Preparation (same as original code) ---
    column_mapping = {
        'หอผู้ป่วยที่ท่านเข้ารับบริการ/ ต้องการประเมิน \n(เพื่อสะท้อนกลับหน่วยงานโดยตรง)': 'หน่วยงาน',
        'ส่วนที่ 1 ข้อมูลทั่วไปของผู้ตอบแบบประเมิน\n1. เพศ': 'เพศ',
        '2. อายุ': 'อายุ', '3. ภูมิลำเนา': 'ภูมิลำเนา', '4. อาชีพ': 'อาชีพ', '5. สิทธิในการรักษา': 'สิทธิการรักษา',
        '6. วันที่มารับบริการ': 'วันที่รับบริการ',
        'จำนวนวันนอนรักษาที่โรงพยาบาล': 'วันนอน',
        'ความพึงพอใจต่อบริการของโรงพยาบาลในภาพรวม': 'ความพึงพอใจโดยรวม',
        '2. ท่านคิดว่าสุขภาพโดยรวมของท่าน (ณ ตอนนี้) เป็นอย่างไร': 'สุขภาพโดยรวม',
        'แบบประเมิน [1. ขั้นตอนการติดต่อและเข้ารับการรักษาในโรงพยาบาล (Admissions) มีความสะดวกเพียงใด]': 'Q1_ความสะดวกการรับบริการ',
        'แบบประเมิน [2. ขณะนอนโรงพยาบาลครั้งนี้ แพทย์ พยาบาลและเจ้าหน้าที่ รับฟังและเปิดโอกาสให้ท่านซักถามข้อสงสัยได้มากน้อยเพียงใด]': 'Q2_การรับฟัง',
        'แบบประเมิน [3. ขณะนอนโรงพยาบาลครั้งนี้ แพทย์ พยาบาลและเจ้าหน้าที่ให้ข้อมูลเกี่ยวกับขั้นตอนการรับบริการได้ชัดเจนเพียงใด]': 'Q3_ความชัดเจนข้อมูลบริการ',
        'แบบประเมิน [4. ขณะนอนโรงพยาบาล ท่านรู้สึกว่าบุคลากรทุกคนดูแลท่านอย่างเท่าเทียมและให้เกียรติหรือไม่]': 'Q4_ความเท่าเทียม',
        'แบบประเมิน [5. โรงพยาบาลมีความสะอาด และมีสิ่งอำนวยความสะดวกเพียงพอต่อความต้องการของท่าน]': 'Q5_ความสะอาดและสิ่งอำนวยความสะดวก',
        'แบบประเมิน [6. เมื่อท่านต้องการความช่วยเหลือ (เช่น กดปุ่มเรียกพยาบาล) ท่านได้รับตอบสนองอย่างเหมาะสม]': 'Q6_การตอบสนอง',
        'แบบประเมิน [7. ขณะนอนโรงพยาบาล ท่านได้รับข้อมูลเกี่ยวกับค่าใช้จ่ายที่อาจเกิดขึ้นอย่างต่อเนื่องและชัดเจนเพียงใด]': 'Q7_ข้อมูลค่าใช้จ่าย',
        'แบบประเมิน [8. ขณะนอนโรงพยาบาล ท่านได้รับข้อมูลการรักษา อาการแทรกซ้อนระหว่างการรักษาพยาบาล]': 'Q8_ข้อมูลการรักษา',
        'แบบประเมิน [9. ท่านและครอบครัว ได้มีส่วนร่วมในการวางแผนการรักษาและการปฏิบัติตัวร่วมกับ ทีมผู้ให้การรักษาอย่างเหมาะสมหรือไม่]': 'Q9_การมีส่วนร่วมวางแผน',
        'แบบประเมิน [10. ท่านได้รับข้อมูลยา ผลข้างเคียงของยา และวิธีการใช้ยาอย่างชัดเจนเพียงใด]': 'Q10_ข้อมูลด้านยา',
        '1. หากท่านมีอาการเจ็บป่วย ท่านจะพิจารณากลับมารับบริการ ที่โรงพยาบาลแห่งนี้หรือไม่': 'กลับมารับบริการหรือไม่',
        '2. หากมีโอกาสท่านจะแนะนำผู้อื่นให้มารับบริการที่โรงพยาบาลแห่งนี้หรือไม่': 'แนะนำผู้อื่นหรือไม่',
        '3. ท่านมีความไม่พึงพอใจในการมาใช้บริการที่โรงพยาบาลนี้หรือไม่': 'มีความไม่พึงพอใจหรือไม่',
        '(หากมี) ความไม่พึงพอใจกรุณาระบุรายละเอียด เพื่อเป็นประโยชน์ในการปรับปรุง': 'รายละเอียดความไม่พึงพอใจ',
        'ข้อเสนอแนะเพิ่มเติมเพื่อการพัฒนาคุณภาพโรงพยาบาล': 'ความคาดหวังต่อบริการ'
    }
    df = df.rename(columns=lambda c: column_mapping.get(c.strip(), c.strip()))

    # Ensure the timestamp column exists before processing
    if 'ประทับเวลา' in df.columns:
    # เพิ่ม dayfirst=True เพื่อบอกว่าเลขตัวหน้าคือ "วัน" (ไม่ใช่เดือน)
        df['date_col'] = pd.to_datetime(df['ประทับเวลา'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['date_col'])
        df = df.dropna(subset=['date_col'])
        df['เดือน'] = df['date_col'].dt.month
        df['ไตรมาส'] = df['date_col'].dt.quarter
        df['ปี'] = df['date_col'].dt.year
    else:
        # If no timestamp, create a dummy column to avoid errors, but show a warning
        st.warning("ไม่พบคอลัมน์ 'ประทับเวลา' ในไฟล์ข้อมูล ตัวกรองเวลาอาจไม่ทำงาน")
        df['date_col'] = pd.NaT
        df['เดือน'] = None
        df['ไตรมาส'] = None
        df['ปี'] = None


    return df

# ==============================================================================
# HELPERS: NORMALIZE, HEART, GAUGES, DISTRIBUTION
# ==============================================================================

LIKERT_MAP = {'มากที่สุด': 5, 'มาก': 4, 'ปานกลาง': 3, 'น้อย': 2, 'น้อยมาก': 1,
              ' มากที่สุด': 5, ' มาก': 4, ' ปานกลาง': 3, ' น้อย': 2, ' น้อยมาก': 1}

def normalize_to_1_5(x):
    if pd.isna(x):
        return pd.NA
    s = str(x).strip()
    if s in LIKERT_MAP:
        return LIKERT_MAP[s]
    m = re.search(r'([1-5])', s)
    if m:
        return int(m.group(1))
    for k, v in LIKERT_MAP.items():
        base = k.strip()
        if base and base in s:
            return v
    return pd.NA

def render_average_heart_rating(avg_score: float, max_score: int = 5, responses: Optional[int] = None):
    if pd.isna(avg_score):
        st.info("ยังไม่มีคะแนนเฉลี่ยให้แสดง")
        return
    full = int(avg_score)
    frac = max(0.0, min(1.0, avg_score - full))
    hearts_html = ""
    for i in range(1, max_score + 1):
        if i <= full:
            hearts_html += '<span class="heart full">♥</span>'
        elif i == full + 1 and frac > 0:
            pct = int(round(frac * 100))
            hearts_html += f'''
            <span class="heart partial" style="
                background: linear-gradient(90deg, #e02424 {pct}%, #E6E6E6 {pct}%);
                -webkit-background-clip: text; background-clip: text;
                -webkit-text-fill-color: transparent; color: transparent;">♥</span>'''
        else:
            hearts_html += '<span class="heart empty">♥</span>'
    labels_html = "".join([f'<span class="heart-label">{i}</span>' for i in range(1, max_score + 1)])
    component_html = f"""
    <style>
      .heart-wrap {{ width: 100%; border: 1px solid #eee; border-radius: 12px; padding: 16px 18px; background: #fff; }}
      .heart-title {{ font-weight: 600; font-size: 1.05rem; color: #333; margin-bottom: 10px; }}
      .heart-row {{ display: flex; align-items: center; justify-content: space-between; gap: 8px; margin: 6px 4px 2px 4px; }}
      .heart {{ font-size: 40px; line-height: 1; display: inline-block; text-shadow: 0 1px 0 rgba(0,0,0,0.06); user-select: none; }}
      .heart.full {{ color: #e02424; }}
      .heart.empty {{ color: #E6E6E6; }}
      .heart-labels {{ display: grid; grid-template-columns: repeat({5}, 1fr); margin-top: 6px; }}
      .heart-label {{ text-align: center; color: #6b7280; font-size: 0.9rem; }}
      .heart-sub {{ color: #6b7280; font-size: 0.9rem; margin-top: 6px; }}
    </style>
    <div class="heart-wrap">
      <div class="heart-title">Average rating ({avg_score:.2f})</div>
      <div class="heart-row">{hearts_html}</div>
      <div class="heart-labels">{labels_html}</div>
      {"<div class='heart-sub'>คำตอบ " + f"{responses:,}" + " ข้อ</div>" if responses is not None else ""}
    </div>
    """
    st.markdown(component_html, unsafe_allow_html=True)

def plot_gauge_1_5(series_num: pd.Series, title: str, height: int = 190,
                     number_font_size: int = 34, key: Optional[str] = None):
    s = series_num.dropna()
    if s.empty:
        st.info(f"ไม่มีข้อมูลสำหรับ '{title}'")
        return
    avg = float(s.mean()); n = int(s.size)

    st.markdown(f"<div class='gauge-head'>{title}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='gauge-sub'>n = {n}</div>", unsafe_allow_html=True)

    steps_4 = [
        {'range': [1, 2], 'color': '#DC2626'},  # แดง
        {'range': [2, 3], 'color': '#EA580C'},  # ส้ม
        {'range': [3, 4], 'color': '#F59E0B'},  # เหลือง
        {'range': [4, 5], 'color': '#16A34A'},  # เขียว
    ]
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=avg,
        number={'valueformat': '.2f', 'font': {'size': number_font_size}},
        title={'text': ''},
        gauge={
            'axis': {'range': [1, 5], 'tickmode': 'array', 'tickvals': [1,2,3,4,5]},
            'bar': {'color': '#111827', 'thickness': 0.25},
            'steps': steps_4,
            'threshold': {'line': {'color': '#111827', 'width': 2}, 'thickness': 0.6, 'value': avg}
        }
    ))
    fig.update_layout(margin=dict(t=8, r=6, b=6, l=6), height=height)
    st.plotly_chart(fig, use_container_width=True, key=key or f"gauge_{hash(title)}")

def render_percent_gauge(title: str, pct: float, n: int, height: int = 190,
                           key: Optional[str] = None, number_font_size: int = 34, mode: str = 'high_good'):
    st.markdown(f"<div class='gauge-head'>{title}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='gauge-sub'>n = {n}</div>", unsafe_allow_html=True)
    if mode == 'high_good':
        steps_4 = [
            {'range': [0, 50],  'color': '#DC2626'},
            {'range': [50, 65], 'color': '#EA580C'},
            {'range': [65, 80], 'color': '#F59E0B'},
            {'range': [80, 100],'color': '#16A34A'},
        ]
    else:
        steps_4 = [
            {'range': [0, 5],   'color': '#16A34A'},
            {'range': [5, 10],  'color': '#F59E0B'},
            {'range': [10, 20], 'color': '#EA580C'},
            {'range': [20, 100],'color': '#DC2626'},
        ]
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=float(pct),
        number={'suffix': '%', 'valueformat': '.1f', 'font': {'size': number_font_size}},
        title={'text': ''},
        gauge={
            'axis': {'range': [0, 100], 'tickmode': 'array', 'tickvals': [0,20,40,60,80,100]},
            'bar': {'color': '#111827', 'thickness': 0.25},
            'steps': steps_4,
            'threshold': {'line': {'color': '#111827', 'width': 2}, 'thickness': 0.6, 'value': float(pct)}
        }
    ))
    fig.update_layout(margin=dict(t=8, r=6, b=6, l=6), height=height)
    st.plotly_chart(fig, use_container_width=True, key=key or f"gauge_pct_{hash(title)}")

def percent_positive(series: pd.Series, positives=("ใช่",)) -> Tuple[float, int]:
    s = series.dropna().astype(str).str.strip()
    n = s.size
    if n == 0:
        return 0.0, 0
    return (s.isin(positives).sum() / n) * 100.0, n

def plot_rating_distribution(series_likert: pd.Series, title: str, key: str):
    s = series_likert.apply(normalize_to_1_5).dropna().astype(int)
    if s.empty:
        st.info(f"ไม่มีข้อมูลสำหรับ '{title}'")
        return
    order = [1, 2, 3, 4, 5]
    counts = s.value_counts().reindex(order, fill_value=0)
    total = int(counts.sum())
    perc = (counts / total * 100).round(1)
    color_map = {1: '#DC2626', 2: '#EA580C', 3: '#F59E0B', 4: '#22C55E', 5: '#16A34A'}
    fig = go.Figure(go.Bar(
        x=order,
        y=[counts[k] for k in order],
        text=[f"{counts[k]:,} ({perc[k]:.1f}%)" for k in order],
        textposition='auto',
        marker_color=[color_map[k] for k in order],
        customdata=[perc[k] for k in order],
        hovertemplate="คะแนน %{x}<br>จำนวน %{y:,}<br>คิดเป็น %{customdata:.1f}%<extra></extra>"
    ))
    fig.update_layout(
        title=title,
        xaxis=dict(tickmode='array', tickvals=order),
        yaxis_title="จำนวน (responses)",
        margin=dict(t=40, r=10, b=40, l=50),
        height=280
    )
    st.plotly_chart(fig, use_container_width=True, key=key)

# ==============================================================================
# MAIN APP LAYOUT (*** MODIFIED SECTION ***)
# ==============================================================================
# --- Sidebar: File Uploader (ยังเก็บไว้เผื่ออยากดูไฟล์เก่า) ---
st.sidebar.markdown("---")
st.sidebar.header("จัดการข้อมูล")
uploaded_file = st.sidebar.file_uploader(
    "อัปโหลดไฟล์ใหม่ (กรณีไม่ใช้ Real-time)",
    type=['csv', 'xlsx']
)

# --- Data Loading Logic (Real-time Google Sheet) ---

# 1. ตั้งค่า Link Google Sheet ของคุณ
SHEET_ID = '11DWvvit4Y50oO-7vebb6etXmvItBe-q1rJaOuezKs4A'
SHEET_GID = '1977910889' # เอามาจากเลขหลัง gid= ในลิงก์ของคุณ
# สร้าง URL สำหรับ Export เป็น CSV
GSHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}"

df_original = pd.DataFrame()
data_source_info = ""

# Logic: ถ้ามีการอัปโหลดไฟล์ ให้ใช้ไฟล์อัปโหลดก่อน / ถ้าไม่มี ให้ดึง Real-time จาก Google Sheet
if uploaded_file is not None:
    data_source = uploaded_file
    data_source_info = f"ไฟล์ที่อัปโหลด: `{uploaded_file.name}`"
    df_original = load_and_prepare_data(data_source)
else:
    try:
        # ใช้ URL ส่งเข้าไปในฟังก์ชันเดิมได้เลย (pd.read_csv รองรับ URL)
        df_original = load_and_prepare_data(GSHEET_URL)
        data_source_info = "Google Sheets (Real-time 🟢)"
    except Exception as e:
        st.error(f"⚠️ ไม่สามารถดึงข้อมูลจาก Google Sheets ได้: {e}")
        st.info("คำแนะนำ: กรุณาตรวจสอบว่าตั้งค่า Share Google Sheet เป็น 'Anyone with the link' หรือยัง")
        st.stop()

# Stop execution if no data is available
if df_original.empty:
    st.warning("ไม่พบข้อมูลใน Google Sheet")
    st.stop()
# --- Sidebar Filters ---
min_date_val = df_original['date_col'].min()
max_date_val = df_original['date_col'].max()

st.sidebar.markdown("---")
# Display data source and date range info in the sidebar
if pd.notna(min_date_val) and pd.notna(max_date_val):
    min_date_str = min_date_val.strftime('%d %b %Y')
    max_date_str = max_date_val.strftime('%d %b %Y')
    st.sidebar.markdown(f"""
    <div class="sidebar-info">
        <div class="label">ช่วงวันที่ของข้อมูล</div>
        <div class="value">{min_date_str} - {max_date_str}</div>
        <div class="source">{data_source_info}</div>
    </div>
    """, unsafe_allow_html=True)

st.sidebar.header("ตัวกรองข้อมูล (Filter)")
available_departments = ['ภาพรวมทั้งหมด'] + sorted(df_original['หน่วยงาน'].dropna().unique().tolist())
selected_department = st.sidebar.selectbox("เลือกหน่วยงาน:", available_departments)
time_filter_option = st.sidebar.selectbox("เลือกช่วงเวลา:",
                                          ["ทั้งหมด", "เลือกตามปี", "เลือกตามไตรมาส", "เลือกตามเดือน"])

# Apply filters to the original dataframe
df_filtered = df_original.copy()
if time_filter_option != "ทั้งหมด" and pd.notna(df_original['date_col']).any():
    year_list = sorted(df_original['ปี'].dropna().unique().astype(int), reverse=True)
    selected_year = st.sidebar.selectbox("เลือกปี:", year_list)
    df_filtered = df_filtered[df_filtered['ปี'] == selected_year]

    if time_filter_option in ["เลือกตามไตรมาส", "เลือกตามเดือน"]:
        if time_filter_option == "เลือกตามไตรมาส":
            quarter_list = sorted(df_filtered['ไตรมาส'].dropna().unique().astype(int))
            selected_quarter = st.sidebar.selectbox("เลือกไตรมาส:", quarter_list)
            df_filtered = df_filtered[df_filtered['ไตรมาส'] == selected_quarter]
        elif time_filter_option == "เลือกตามเดือน":
            month_map = {1: 'ม.ค.', 2: 'ก.พ.', 3: 'มี.ค.', 4: 'เม.ย.', 5: 'พ.ค.', 6: 'มิ.ย.', 7: 'ก.ค.', 8: 'ส.ค.',
                         9: 'ก.ย.', 10: 'ต.ค.', 11: 'พ.ย.', 12: 'ธ.ค.'}
            month_list = sorted(df_filtered['เดือน'].dropna().unique().astype(int))
            selected_month_num = st.sidebar.selectbox("เลือกเดือน:", month_list,
                                                      format_func=lambda x: month_map.get(x, x))
            df_filtered = df_filtered[df_filtered['เดือน'] == selected_month_num]

if selected_department != 'ภาพรวมทั้งหมด':
    df_filtered = df_filtered[df_filtered['หน่วยงาน'] == selected_department]

if df_filtered.empty:
    st.warning("ไม่พบข้อมูลตามตัวกรองที่ท่านเลือก")
    st.stop()


# ==============================================================================
# PAGE CONTENT (*** UNCHANGED FROM THIS POINT ONWARD ***)
# ==============================================================================

# 1. กำหนด Link รูปภาพ
logo_urls = [
    "https://github.com/HOIARRTool/appqtbi/blob/main/messageImage_1763018963411.jpg?raw=true",    
    "https://mfu.ac.th/fileadmin/_processed_/6/7/csm_logo_mfu_3d_colour_15e5a7a50f.png"
]

# 2. สร้างคอลัมน์สำหรับจัดวาง (แบ่งเป็น: โลโก้1 | โลโก้2 | พื้นที่ว่างเหลือๆ)

col1, col2, col3 = st.columns([1, 1, 8])

with col1:
    st.image(logo_urls[0], use_column_width=True)

with col2:
    st.image(logo_urls[1], use_column_width=True)

# 3. แสดง Title ตามเดิม (ให้อยู่บรรทัดต่อมา)
st.title(f"DASHBOARD: {selected_department}")

# --- Metrics ---
satisfaction_score_map = {'มากที่สุด': 5, 'มาก': 4, 'ปานกลาง': 3, 'น้อย': 2, 'น้อยมาก': 1}
df_filtered['คะแนนความพึงพอใจ'] = df_filtered['ความพึงพอใจโดยรวม'].map(satisfaction_score_map)
average_satisfaction_score = df_filtered['คะแนนความพึงพอใจ'].mean()
display_avg_satisfaction = f"{average_satisfaction_score:.2f}" if pd.notna(average_satisfaction_score) else "N/A"
total_responses = len(df_filtered)

def calculate_percentage(df: pd.DataFrame, col_name: str, positive_value='ใช่', decimals=1) -> str:
    if col_name in df.columns and not df[col_name].dropna().empty:
        count = (df[col_name] == positive_value).sum()
        total_count = df[col_name].notna().sum()
        if total_count > 0:
            return f"{(count / total_count) * 100:.{decimals}f}%"
    return "N/A"

return_service_pct = calculate_percentage(df_filtered, 'กลับมารับบริการหรือไม่', decimals=1)
recommend_pct = calculate_percentage(df_filtered, 'แนะนำผู้อื่นหรือไม่', decimals=1)
dissatisfied_pct = calculate_percentage(df_filtered, 'มีความไม่พึงพอใจหรือไม่', positive_value='มี', decimals=2)

most_common_health_status = (
    df_filtered['สุขภาพโดยรวม'].mode()[0]
    if 'สุขภาพโดยรวม' in df_filtered.columns and not df_filtered['สุขภาพโดยรวม'].dropna().empty
    else "N/A"
)

st.markdown("##### ภาพรวม")
row1 = st.columns(3)
row2 = st.columns(3)
with row1[0]:
    st.markdown(
        f'<div class="metric-box metric-box-1"><div class="label">จำนวนผู้ตอบ</div><div class="value">{total_responses:,}</div></div>',
        unsafe_allow_html=True)
with row1[1]:
    st.markdown(
        f'<div class="metric-box metric-box-2"><div class="label">คะแนนพึงพอใจเฉลี่ย</div><div class="value">{display_avg_satisfaction}</div></div>',
        unsafe_allow_html=True)
with row1[2]:
    st.markdown(
        f'<div class="metric-box metric-box-6"><div class="label">สุขภาพผู้ป่วยโดยรวม</div><div class="value" style="font-size: 1.8rem;">{most_common_health_status}</div></div>',
        unsafe_allow_html=True)
with row2[0]:
    st.markdown(
        f'<div class="metric-box metric-box-3"><div class="label">% กลับมาใช้บริการ</div><div class="value">{return_service_pct}</div></div>',
        unsafe_allow_html=True)
with row2[1]:
    st.markdown(
        f'<div class="metric-box metric-box-4"><div class="label">% การบอกต่อ</div><div class="value">{recommend_pct}</div></div>',
        unsafe_allow_html=True)
with row2[2]:
    st.markdown(
        f'<div class="metric-box metric-box-5"><div class="label">% ไม่พึงพอใจ</div><div class="value">{dissatisfied_pct}</div></div>',
        unsafe_allow_html=True)
st.markdown("---")

# ===== เพิ่มตารางสรุปจำนวนการประเมิน (คงตามเดิม) =====
if selected_department == 'ภาพรวมทั้งหมด':
    st.subheader("สรุปจำนวนการประเมินตามหน่วยงาน")
    evaluation_counts = df_filtered['หน่วยงาน'].value_counts().reset_index()
    evaluation_counts.columns = ['หน่วยงาน', 'จำนวนการประเมิน']
    st.dataframe(evaluation_counts, use_container_width=True, hide_index=True)
    st.markdown("---")

# ===== ความพึงพอใจโดยรวม: หัวใจ + Distribution =====
st.subheader("ความพึงพอใจโดยรวม")
c_left, c_right = st.columns([1, 1])
with c_left:
    render_average_heart_rating(average_satisfaction_score, max_score=5, responses=total_responses)
with c_right:
    plot_rating_distribution(df_filtered['ความพึงพอใจโดยรวม'], "Distribution ของคะแนน (1–5)", key="dist_overall_ipd")
st.markdown("---")

# ===== ส่วนที่ 2: ความพึงพอใจต่อบริการ (รายหัวข้อ) → เกจ 4 โซน =====
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
    'Q9_การมีส่วนร่วมวางแผน': '9. การมีส่วนร่วมในการวางแผนการรักษา',
    'Q10_ข้อมูลด้านยา': '10. ความชัดเจนของข้อมูลด้านยา'
}
# คำนวณ score 1–5 สำหรับแต่ละหัวข้อ
for col in satisfaction_cols.keys():
    if col in df_filtered.columns:
        df_filtered[f'{col}__score'] = df_filtered[col].apply(normalize_to_1_5).astype('Float64')

# วาดเกจ 2 คอลัมน์เหมือนเดิม
col_pairs = [list(satisfaction_cols.items())[i:i + 2] for i in range(0, len(satisfaction_cols), 2)]
for pair in col_pairs:
    cols = st.columns(2)
    for i, (col_name, title) in enumerate(pair):
        with cols[i]:
            score_col = f'{col_name}__score'
            if score_col in df_filtered.columns:
                plot_gauge_1_5(df_filtered[score_col], title, height=200, key=f"g_{col_name}")
            else:
                st.info(f"ไม่มีข้อมูลสำหรับ '{title}'")

st.markdown("---")

# ===== ส่วนที่ 3: ความตั้งใจในอนาคตและข้อเสนอแนะ → เกจ 4 โซน =====
st.header("ส่วนที่ 3: ความตั้งใจในอนาคตและข้อเสนอแนะ")
c1, c2, c3 = st.columns(3)
with c1:
    pct_return, n_return = percent_positive(df_filtered['กลับมารับบริการหรือไม่'], positives=("ใช่",))
    render_percent_gauge("1. หากเจ็บป่วยจะกลับมารับบริการหรือไม่ (ตอบ 'ใช่')",
                         pct_return, n_return, height=200, key="g_future_return", mode='high_good')
with c2:
    pct_reco, n_reco = percent_positive(df_filtered['แนะนำผู้อื่นหรือไม่'], positives=("ใช่",))
    render_percent_gauge("2. จะแนะนำผู้อื่นให้มารับบริการหรือไม่ (ตอบ 'ใช่')",
                         pct_reco, n_reco, height=200, key="g_future_reco", mode='high_good')
with c3:
    # ยิ่งต่ำยิ่งดี → ใช้ mode='low_good' (เขียวซ้าย แดงขวา)
    pct_dissat, n_dissat = percent_positive(df_filtered['มีความไม่พึงพอใจหรือไม่'], positives=("มี",))
    render_percent_gauge("3. ไม่พึงพอใจ (ตอบ 'มี')",
                         pct_dissat, n_dissat, height=200, key="g_future_dissat", mode='low_good')

# ===== ตารางรายละเอียด/ความคาดหวัง (คงตามโค้ดที่ให้มา) =====
st.subheader("รายละเอียดความไม่พึงพอใจ (หากมี)")
if 'รายละเอียดความไม่พึงพอใจ' in df_filtered.columns:
    temp_df = df_filtered[['หน่วยงาน', 'รายละเอียดความไม่พึงพอใจ']].copy()
    temp_df.dropna(subset=['รายละเอียดความไม่พึงพอใจ'], inplace=True)
    temp_df['details_stripped'] = temp_df['รายละเอียดความไม่พึงพอใจ'].astype(str).str.strip()
    dissatisfaction_df = temp_df[(temp_df['details_stripped'] != '') & (temp_df['details_stripped'] != 'ไม่มี')]
    if not dissatisfaction_df.empty:
        st.dataframe(dissatisfaction_df[['หน่วยงาน', 'รายละเอียดความไม่พึงพอใจ']],
                     use_container_width=True, hide_index=True)
    else:
        st.info("ไม่พบรายละเอียดความไม่พึงพอใจในช่วงข้อมูลที่เลือก")

st.subheader("ความคาดหวังต่อบริการของโรงพยาบาลในภาพรวม")
# โค้ดเดิมตรวจชื่อคอลัมน์ยาว หากไม่เจอ ให้ fallback ไปที่คอลัมน์ที่แมปไว้ชื่อ 'ความคาดหวังต่อบริการ'
target_col = 'ความคาดหวังต่อบริการของโรงพยาบาลในภาพรวม'
if target_col not in df_filtered.columns and 'ความคาดหวังต่อบริการ' in df_filtered.columns:
    target_col = 'ความคาดหวังต่อบริการ'

if target_col in df_filtered.columns:
    suggestions_df = df_filtered[df_filtered[target_col].notna()][['หน่วยงาน', target_col]]
    if not suggestions_df.empty:
        st.dataframe(suggestions_df, use_container_width=True, hide_index=True)
    else:
        st.info("ไม่พบข้อมูลความคาดหวังในช่วงข้อมูลที่เลือก")










