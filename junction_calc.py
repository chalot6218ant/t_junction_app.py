import streamlit as st
import pandas as pd

st.set_page_config(page_title="T-Junction App", layout="wide")

st.title("🚦 3-Way Junction Analysis")

# ส่วนเลือกรูปแบบทางแยก
type_3way = st.sidebar.selectbox("รูปแบบจุดตัด (ขาที่หายไป)", ["ไม่มีขาเหนือ (T-Shape)", "ไม่มีขาใต้", "ไม่มีขาตะวันออก", "ไม่มีขาตะวันตก"])

# กำหนดทิศทาง
if "ไม่มีขาเหนือ" in type_3way:
    moves = {"South": ["Left", "Right"], "East": ["Left", "Through"], "West": ["Right", "Through"]}
elif "ไม่มีขาใต้" in type_3way:
    moves = {"North": ["Left", "Right"], "East": ["Right", "Through"], "West": ["Left", "Through"]}
elif "ไม่มีขาตะวันออก" in type_3way:
    moves = {"North": ["Through", "Right"], "South": ["Through", "Left"], "West": ["Left", "Right"]}
else:
    moves = {"North": ["Through", "Left"], "South": ["Through", "Right"], "East": ["Left", "Right"]}

# ส่วนรับข้อมูล
st.sidebar.subheader("📥 กรอกปริมาณจราจร")
data_list = []
for app, directions in moves.items():
    st.sidebar.write(f"**มาจากทิศ {app}**")
    for d in directions:
        val = st.sidebar.number_input(f"ไป {d}", min_value=0, key=f"{app}_{d}")
        data_list.append({"Approach": app, "Movement": d, "Volume": val})

# คำนวณและแสดงผล
df = pd.DataFrame(data_list)
total = df["Volume"].sum()
df["% Distribution"] = (df["Volume"] / total * 100) if total > 0 else 0

col1, col2 = st.columns([1, 2])
with col1:
    st.metric("Total Volume", f"{total:,}")
    # ส่วนคำนวณ PHF แบบง่าย
    with st.expander("คำนวณ PHF"):
        v1 = st.number_input("15 min 1", min_value=0)
        v2 = st.number_input("15 min 2", min_value=0)
        v3 = st.number_input("15 min 3", min_value=0)
        v4 = st.number_input("15 min 4", min_value=0)
        if (v1+v2+v3+v4) > 0:
            phf = (v1+v2+v3+v4) / (4 * max(v1, v2, v3, v4))
            st.success(f"PHF: {phf:.3f}")

with col2:
    st.subheader("Data Summary")
    st.dataframe(df.style.format({"% Distribution": "{:.2f}"}), use_container_width=True)
