import streamlit as st
import pandas as pd
import numpy as np

# ตั้งค่าหน้ากระดาษให้กว้างและสวยงาม
st.set_page_config(page_title="3-Way Turning Movement Analysis", layout="wide")

# ส่วนหัวของแอปพลิเคชัน
st.title("🚦 Turning Movement Count Analysis (3-Way)")
st.markdown("โปรแกรมคำนวณปริมาณจราจรรายชั่วโมง สัดส่วนการเลี้ยว และค่า PHF สำหรับทาง 3 แยก")

# --- 1. ส่วนการเลือกรูปแบบทางแยก (ขาที่หายไป) ---
with st.sidebar:
    st.header("📍 Intersection Setting")
    missing_leg = st.radio(
        "เลือก 'ขา' ที่ไม่มี (ขาที่หายไป):",
        ["North (ทิศเหนือ)", "South (ทิศใต้)", "East (ทิศตะวันออก)", "West (ทิศตะวันตก)"],
        index=0
    )
    st.divider()
    st.info("ระบบจะปรับตารางกรอกข้อมูลให้สอดคล้องกับทาง 3 แยกโดยอัตโนมัติ")

# --- 2. Logic กำหนดทิศทางและ Movement ตามขาที่เลือก ---
# ใน 3 แยก จะมี 6 Movements หลัก
if "North" in missing_leg:
    active_legs = ['South', 'East', 'West']
    movements = {
        'South': ['Left', 'Right'],      # ตรงไม่ได้เพราะติดทางตัน/ไม่มีขาเหนือ
        'East': ['Straight', 'Left'],    # ขวาไม่ได้
        'West': ['Straight', 'Right']    # ซ้ายไม่ได้
    }
elif "South" in missing_leg:
    active_legs = ['North', 'East', 'West']
    movements = {
        'North': ['Left', 'Right'],
        'East': ['Straight', 'Right'],
        'West': ['Straight', 'Left']
    }
elif "East" in missing_leg:
    active_legs = ['North', 'South', 'West']
    movements = {
        'North': ['Straight', 'Right'],
        'South': ['Straight', 'Left'],
        'West': ['Left', 'Right']
    }
else: # West หาย
    active_legs = ['North', 'South', 'East']
    movements = {
        'North': ['Straight', 'Left'],
        'South': ['Straight', 'Right'],
        'East': ['Left', 'Right']
    }

# สร้างรายชื่อ Column ทั้งหมดสำหรับตาราง
cols = []
for leg in active_legs:
    for move in movements[leg]:
        cols.append(f"{leg}_{move}")

# --- 3. ส่วนการกรอกข้อมูลราย 15 นาที (หน้าตาเหมือนแอปเดิม) ---
st.subheader("📅 15-Minute Interval Data Entry")
st.write("กรอกปริมาณจราจรแยกตามทิศทาง (คัน):")

time_index = ['00-15 min', '15-30 min', '30-45 min', '45-60 min']
# สร้าง DataFrame เปล่า
if 'df_input' not in st.session_state or st.session_state.get('last_leg') != missing_leg:
    st.session_state.df_input = pd.DataFrame(0, index=time_index, columns=cols)
    st.session_state.last_leg = missing_leg

# ตารางกรอกข้อมูลแบบ Editable (เหมือน Spreadsheet ในแอปเดิม)
edited_df = st.data_editor(st.session_state.df_input, use_container_width=True)

# --- 4. การคำนวณผลลัพธ์ ---
# รวมยอดรายชั่วโมงของแต่ละ Movement
hourly_totals = edited_df.sum()
# รวมปริมาณรถรวมทั้งแยก
grand_total = hourly_totals.sum()

# คำนวณ PHF
# รวมปริมาณรถทุกทิศทางในแต่ละ 15 นาที
interval_sums = edited_df.sum(axis=1)
v_max_15 = interval_sums.max() # ช่วง 15 นาทีที่รถเยอะที่สุด
if v_max_15 > 0:
    phf_calc = grand_total / (4 * v_max_15)
else:
    phf_calc = 0.0

# --- 5. การแสดงผล Dashboard ---
st.divider()
st.subheader("📊 Summary Dashboard")

m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Total Volume (V)", f"{int(grand_total):,} veh/hr")
with m2:
    st.metric("Max 15-min Volume", f"{int(v_max_15):,} veh")
with m3:
    st.metric("Peak Hour Factor (PHF)", f"{phf_calc:.3f}")

# ตารางสรุปสัดส่วนการเลี้ยว
st.write("### Turning Movement Summary Table")
summary_data = []
for col in cols:
    vol = hourly_totals[col]
    perc = (vol / grand_total * 100) if grand_total > 0 else 0
    summary_data.append({
        "Approach & Movement": col.replace("_", " "),
        "Hourly Volume (veh)": int(vol),
        "Percentage (%)": f"{perc:.2f}%"
    })

st.table(pd.DataFrame(summary_data))

# --- 6. ส่วนการ Export ข้อมูล ---
st.divider()
c1, c2 = st.columns(2)
with c1:
    csv = edited_df.to_csv().encode('utf-8-sig')
    st.download_button(
        label="💾 Download Raw Data (CSV)",
        data=csv,
        file_name='traffic_data_3way.csv',
        mime='text/csv',
    )
with c2:
    st.info("คุณสามารถคัดลอกข้อมูลจากตารางด้านบนไปวางใน Excel หรือ Google Sheets ได้โดยตรง")
