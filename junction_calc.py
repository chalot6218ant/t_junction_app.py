import streamlit as st
import pandas as pd
import numpy as np

# ตั้งค่าหน้ากระดาษ
st.set_page_config(page_title="3-Way Turning Movement Analysis", layout="wide")

# หัวข้อแอป
st.title("🚦 Turning Movement Count Analysis (3-Way)")
st.markdown("โปรแกรมคำนวณปริมาณจราจรรายชั่วโมง, สัดส่วนการเลี้ยว และค่า PHF สำหรับทาง 3 แยก")

# --- 1. ส่วนเลือกรูปแบบ 3 แยก (Sidebar) ---
with st.sidebar:
    st.header("📍 Intersection Setting")
    missing_leg = st.radio(
        "เลือก 'ขา' ที่ไม่มี (ขาที่หายไป):",
        ["North (ทิศเหนือ)", "South (ทิศใต้)", "East (ทิศตะวันออก)", "West (ทิศตะวันตก)"],
        index=0
    )
    st.divider()
    st.info("ระบบจะปรับหัวข้อตารางกรอกข้อมูลให้สอดคล้องกับทาง 3 แยกที่คุณเลือก")

# --- 2. Logic กำหนดทิศทาง (Movement) ตามขาที่หายไป ---
if "North" in missing_leg:
    # 3 แยกรูปตัว T (ไม่มีขาเหนือ)
    active_legs = ['South', 'East', 'West']
    movements = {
        'South': ['Left (to West)', 'Right (to East)'],
        'East': ['Straight (to West)', 'Left (to South)'],
        'West': ['Straight (to East)', 'Right (to South)']
    }
elif "South" in missing_leg:
    # 3 แยกรูปตัว T กลับหัว (ไม่มีขาใต้)
    active_legs = ['North', 'East', 'West']
    movements = {
        'North': ['Left (to East)', 'Right (to West)'],
        'East': ['Straight (to West)', 'Right (to North)'],
        'West': ['Straight (to East)', 'Left (to North)']
    }
elif "East" in missing_leg:
    # ไม่มีขาส่งจากด้านขวา
    active_legs = ['North', 'South', 'West']
    movements = {
        'North': ['Straight (to South)', 'Right (to West)'],
        'South': ['Straight (to North)', 'Left (to West)'],
        'West': ['Left (to North)', 'Right (to South)']
    }
else: # West หาย
    active_legs = ['North', 'South', 'East']
    movements = {
        'North': ['Straight (to South)', 'Left (to East)'],
        'South': ['Straight (to North)', 'Right (to East)'],
        'East': ['Left (to South)', 'Right (to North)']
    }

# สร้างรายชื่อ Column สำหรับตารางกรอกข้อมูล
cols = []
for leg in active_legs:
    for move in movements[leg]:
        cols.append(f"{leg}: {move}")

# --- 3. ตารางกรอกข้อมูลราย 15 นาที (เหมือนแอปเดิม) ---
st.subheader("📅 15-Minute Interval Data Entry")
st.write("กรอกปริมาณจราจรแยกตามทิศทางในแต่ละช่วงเวลา (คัน):")

time_index = ['00-15 min', '15-30 min', '30-45 min', '45-60 min']

# ตรวจสอบการเปลี่ยนทิศทางเพื่อ Reset ตาราง
if 'last_config' not in st.session_state or st.session_state.last_config != missing_leg:
    st.session_state.df_input = pd.DataFrame(0, index=time_index, columns=cols)
    st.session_state.last_config = missing_leg

# ใช้ Data Editor เพื่อให้กรอกข้อมูลได้เหมือน Spreadsheet
edited_df = st.data_editor(st.session_state.df_input, use_container_width=True, key="data_editor")

# --- 4. การคำนวณค่าทางวิศวกรรมจราจร ---
# 1. ปริมาณรถรวมรายชั่วโมงของแต่ละ Movement
hourly_totals = edited_df.sum()
# 2. ปริมาณรถรวมทั้งแยก (Total Volume)
grand_total = hourly_totals.sum()
# 3. รวมปริมาณรถทุกทิศทางในแต่ละช่วง 15 นาที (เพื่อหาค่า Peak)
interval_totals = edited_df.sum(axis=1)
v_max_15 = interval_totals.max()

# 4. คำนวณ PHF (Peak Hour Factor)
# สูตร: Total Volume / (4 * ปริมาณรถในช่วง 15 นาทีที่หนาแน่นที่สุด)
if v_max_15 > 0:
    phf_result = grand_total / (4 * v_max_15)
else:
    phf_result = 0.0

# --- 5. การแสดงผล (Dashboard) ---
st.divider()
st.subheader("📊 Summary Analysis")

m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Total Intersection Volume (V)", f"{int(grand_total):,} veh/hr")
with m2:
    st.metric("Max 15-min Volume (V15)", f"{int(v_max_15):,} veh")
with m3:
    st.metric("Peak Hour Factor (PHF)", f"{phf_result:.3f}")

# ตารางสรุปสัดส่วน (Percentage Distribution)
st.write("### Turning Movement Summary")
summary_list = []
for col_name in cols:
    vol = hourly_totals[col_name]
    perc = (vol / grand_total * 100) if grand_total > 0 else 0
    summary_list.append({
        "Approach & Movement": col_name,
        "Hourly Volume (veh)": int(vol),
        "Percentage (%)": f"{perc:.2f}%"
    })

st.table(pd.DataFrame(summary_list))

# --- 6. ส่วนดาวน์โหลดไฟล์ ---
csv_data = edited_df.to_csv().encode('utf-8-sig')
st.download_button(
    label="💾 Download Data as CSV",
    data=csv_data,
    file_name='3way_traffic_analysis.csv',
    mime='text/csv',
)
