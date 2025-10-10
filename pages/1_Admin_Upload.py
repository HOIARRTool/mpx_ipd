# pages/1_Admin_Upload.py

import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide", page_title="Admin Upload")


# ==============================================================================
# PASSWORD PROTECTION
# ==============================================================================
def check_password():
    """Returns `True` if the user entered the correct password."""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    st.header("กรุณาเข้าสู่ระบบ")
    password = st.text_input("รหัสผ่านสำหรับ Admin:", type="password")

    if password == "admin1234":
        st.session_state.password_correct = True
        st.rerun()
    elif password != "":
        st.error("รหัสผ่านไม่ถูกต้อง กรุณาลองอีกครั้ง")
        st.session_state.password_correct = False

    return st.session_state.password_correct


# ==============================================================================
# MAIN UPLOAD LOGIC
# ==============================================================================
if not st.session_state.get("password_correct", False):
    if check_password():
        pass
    st.stop()

# --- ส่วนนี้จะแสดงผลก็ต่อเมื่อใส่รหัสผ่านถูกต้องแล้ว ---
st.success("✅ เข้าสู่ระบบสำเร็จ!")
st.title("Admin: อัปโหลดไฟล์ข้อมูล")
st.markdown("---")
st.header("อัปโหลดไฟล์ Patient Satisfaction (XLSX)")

# ❗️ จุดที่ 1: เปลี่ยน type เป็น 'xlsx'
uploaded_file = st.file_uploader(
    "เลือกไฟล์ Excel (.xlsx)",
    type=['xlsx']
)

if uploaded_file is not None:
    # กำหนดตำแหน่งที่จะบันทึกไฟล์ (ยังคงเป็น .csv เพื่อให้หน้า Dashboard อ่านได้)
    save_path = "patient_satisfaction_data.csv"

    try:
        # ❗️ จุดที่ 2: อ่านไฟล์ Excel ด้วย pd.read_excel()
        df_from_excel = pd.read_excel(uploaded_file, engine='openpyxl')

        # ❗️ จุดที่ 3: บันทึก DataFrame ที่ได้เป็นไฟล์ CSV
        # เพื่อให้หน้า Dashboard หลัก (Dashboard.py) สามารถทำงานได้เหมือนเดิมโดยไม่ต้องแก้ไข
        df_from_excel.to_csv(save_path, index=False)

        st.success(f"ไฟล์ '{uploaded_file.name}' ได้รับการประมวลผลและบันทึกเป็น `{save_path}` เรียบร้อยแล้ว!")
        st.info(f"พบข้อมูลทั้งหมด {len(df_from_excel):,} แถว")
        st.markdown("##### ตัวอย่างข้อมูล 5 แถวแรก:")
        st.dataframe(df_from_excel.head())

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการประมวลผลไฟล์: {e}")
        st.warning("กรุณาตรวจสอบว่าไฟล์เป็น Excel (.xlsx) ที่ถูกต้องตามรูปแบบหรือไม่")