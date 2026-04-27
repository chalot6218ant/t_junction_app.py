import streamlit as st
import numpy as np

st.set_page_config(layout="wide", page_title="Traffic Analysis (3-Way/4-Way)")

# --- 1. ส่วนรับข้อมูล ---
with st.sidebar:
    st.header("📝 ตั้งค่าจุดตัด")
    intersection_type = st.radio("ประเภทจุดตัด", ["4 แยก (Cross)", "3 แยก (T-Junction)"])
    
    disabled_direction = None
    if intersection_type == "3 แยก (T-Junction)":
        disabled_direction = st.selectbox("ทิศทางที่ 'ไม่มี' ถนน", ["North (N)", "South (S)", "East (E)", "West (W)"])

    st.header("🛣️ ชื่อถนน")
    title_text = st.text_input("ชื่อกราฟ", "ปริมาณจราจรปี 2569")
    n_road = st.text_input("ถนนทิศเหนือ (N)", "ถ.กาญจนาภิเษก (N)") if disabled_direction != "North (N)" else ""
    s_road = st.text_input("ถนนทิศใต้ (S)", "ถ.กาญจนาภิเษก (S)") if disabled_direction != "South (S)" else ""
    e_road = st.text_input("ถนนทิศตะวันออก (E)", "ถ.โครงการแนวตะวันออก-ตก") if disabled_direction != "East (E)" else ""
    w_road = st.text_input("ถนนทิศตะวันตก (W)", "ถ.บางกรวย-ไทรน้อย") if disabled_direction != "West (W)" else ""

st.subheader(f"🚗 วิเคราะห์ Turning Movement ({intersection_type})")

# จัดเตรียม Columns สำหรับ Input
col1, col2, col3, col4 = st.columns(4)
dirs = {"North (N)": (col1, "N"), "South (S)": (col2, "S"), "East (E)": (col3, "E"), "West (W)": (col4, "W")}
inputs = {}

for name, (col, key) in dirs.items():
    with col:
        if disabled_direction == name:
            st.info(f"ไม่มีทางเชื่อม {key}")
            inputs[f'in_{key.lower()}'] = 0
            inputs[f'out_{key.lower()}'] = 0
        else:
            inputs[f'in_{key.lower()}'] = st.number_input(f"Inbound ({key})", value=1000, step=10)
            inputs[f'out_{key.lower()}'] = st.number_input(f"Outbound ({key})", value=1000, step=10)

# --- 2. การคำนวณ (Matrix Balancing) ---
t_in = np.array([inputs['in_n'], inputs['in_s'], inputs['in_e'], inputs['in_w']])
t_out = np.array([inputs['out_n'], inputs['out_s'], inputs['out_e'], inputs['out_w']])

total_in = int(np.sum(t_in))
total_out = int(np.sum(t_out))
diff = int(abs(total_in - total_out))
p_diff = (diff / total_in * 100) if total_in > 0 else 0

# Seed Matrix: ปรับให้เป็น 0 ในทิศที่ไม่มีถนน
seed = np.array([
    [0.0, 0.7, 0.15, 0.15], # From N to [N, S, E, W]
    [0.7, 0.0, 0.15, 0.15], # From S
    [0.15, 0.15, 0.0, 0.7], # From E
    [0.15, 0.15, 0.7, 0.0]  # From W
])

# ปิดทิศทางที่ไม่ได้ใช้งานใน Matrix
dir_idx = {"North (N)": 0, "South (S)": 1, "East (E)": 2, "West (W)": 3}
if disabled_direction:
    idx = dir_idx[disabled_direction]
    seed[idx, :] = 0 # Outbound จากทิศนั้นเป็น 0
    seed[:, idx] = 0 # Inbound ไปทิศนั้นเป็น 0

mat = seed.copy()
for _ in range(50): # Balancing
    if mat.sum() == 0: break
    mat = (mat.T * (t_in / np.maximum(mat.sum(axis=1), 1))).T
    mat = mat * (t_out / np.maximum(mat.sum(axis=0), 1))

def gv(o, d): return int(round(mat[o, d]))
res = {
    'nl': gv(0, 2), 'nt': gv(0, 1), 'nr': gv(0, 3),
    'sl': gv(1, 3), 'st': gv(1, 0), 'sr': gv(1, 2),
    'el': gv(2, 1), 'et': gv(2, 3), 'er': gv(2, 0),
    'wl': gv(3, 0), 'wt': gv(3, 2), 'wr': gv(3, 1)
}

# --- 3. ส่วนการสร้าง Diagram (SVG) ---
# ฟังก์ชันช่วยซ่อนเส้นถนน
def get_road_style(dir_name):
    return "display:none;" if disabled_direction == dir_name else ""

svg_code = f"""
<div style="display: flex; justify-content: center;">
<svg viewBox="0 0 850 750" xmlns="http://www.w3.org/2000/svg" style="background:white; border:1px solid #ccc; width:100%; max-width:850px;">
    <rect width="850" height="50" fill="#f8f9fa" />
    <text x="425" y="32" text-anchor="middle" font-size="22" font-weight="bold" font-family="Arial">{title_text}</text>

    <path d="M 350 50 V 280 M 500 50 V 280" stroke="black" stroke-width="2" style="{get_road_style('North (N)')}"/>
    <path d="M 350 470 V 700 M 500 470 V 700" stroke="black" stroke-width="2" style="{get_road_style('South (S)')}"/>
    <path d="M 500 280 H 800 M 500 470 H 800" stroke="black" stroke-width="2" style="{get_road_style('East (E)')}"/>
    <path d="M 50 280 H 350 M 50 470 H 350" stroke="black" stroke-width="2" style="{get_road_style('West (W)')}"/>
    
    {"<line x1='350' y1='280' x2='500' y2='280' stroke='black' stroke-width='2'/>" if disabled_direction == 'North (N)' else ""}
    {"<line x1='350' y1='470' x2='500' y2='470' stroke='black' stroke-width='2'/>" if disabled_direction == 'South (S)' else ""}
    {"<line x1='500' y1='280' x2='500' y2='470' stroke='black' stroke-width='2'/>" if disabled_direction == 'East (E)' else ""}
    {"<line x1='350' y1='280' x2='350' y2='470' stroke='black' stroke-width='2'/>" if disabled_direction == 'West (W)' else ""}

    <defs>
        <marker id="arrow" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
            <path d="M0,0 L6,3 L0,6 Z" fill="black" />
        </marker>
    </defs>

    <g font-size="16" font-weight="bold" font-family="Arial">
        <g style="{get_road_style('North (N)')}"><text x="465" y="80" text-anchor="middle" fill="#2E7D32">IN: {inputs['in_n']:,}</text> <text x="385" y="80" text-anchor="middle" fill="#C62828">OUT: {inputs['out_n']:,}</text></g>
        <g style="{get_road_style('South (S)')}"><text x="385" y="680" text-anchor="middle" fill="#2E7D32">IN: {inputs['in_s']:,}</text> <text x="465" y="680" text-anchor="middle" fill="#C62828">OUT: {inputs['out_s']:,}</text></g>
        <g style="{get_road_style('East (E)')}"><text x="730" y="320" text-anchor="middle" fill="#2E7D32">IN: {inputs['in_e']:,}</text> <text x="730" y="440" text-anchor="middle" fill="#C62828">OUT: {inputs['out_e']:,}</text></g>
        <g style="{get_road_style('West (W)')}"><text x="120" y="320" text-anchor="middle" fill="#2E7D32">IN: {inputs['in_w']:,}</text> <text x="120" y="440" text-anchor="middle" fill="#C62828">OUT: {inputs['out_w']:,}</text></g>
    </g>

    {f'''<g transform="translate(435, 230)" style="{get_road_style('North (N)')}">
        <path d="M 50 -30 Q 50 0 75 0" fill="none" stroke="black" stroke-width="2" marker-end="url(#arrow)" style="{get_road_style('East (E)')}"/>
        <path d="M 32 -30 V 10" fill="none" stroke="black" stroke-width="2" marker-end="url(#arrow)" style="{get_road_style('South (S)')}"/>
        <path d="M 14 -30 Q 14 0 -15 0" fill="none" stroke="black" stroke-width="2" marker-end="url(#arrow)" style="{get_road_style('West (W)')}"/>
        <rect x="41" y="-85" width="22" height="55" fill="white" stroke="black" style="{get_road_style('East (E)')}"/><text x="52" y="-57.5" text-anchor="middle" dominant-baseline="central" font-size="14" font-weight="bold" transform="rotate(-90 52,-57.5)" style="{get_road_style('East (E)')}">{res['nl']:,}</text>
        <rect x="21" y="-85" width="22" height="55" fill="white" stroke="black" style="{get_road_style('South (S)')}"/><text x="32" y="-57.5" text-anchor="middle" dominant-baseline="central" font-size="14" font-weight="bold" transform="rotate(-90 32,-57.5)" style="{get_road_style('South (S)')}">{res['nt']:,}</text>
        <rect x="1" y="-85" width="22" height="55" fill="white" stroke="black" style="{get_road_style('West (W)')}"/><text x="12" y="-57.5" text-anchor="middle" dominant-baseline="central" font-size="14" font-weight="bold" transform="rotate(-90 12,-57.5)" style="{get_road_style('West (W)')}">{res['nr']:,}</text>
    </g>''' if disabled_direction != 'North (N)' else ''}

    {f'''<g transform="translate(355, 410)" style="{get_road_style('South (S)')}">
        <path d="M 14 45 Q 14 15 -10 15" fill="none" stroke="black" stroke-width="2" marker-end="url(#arrow)" style="{get_road_style('West (W)')}"/>
        <path d="M 32 45 V 5" fill="none" stroke="black" stroke-width="2" marker-end="url(#arrow)" style="{get_road_style('North (N)')}"/>
        <path d="M 50 45 Q 50 15 75 15" fill="none" stroke="black" stroke-width="2" marker-end="url(#arrow)" style="{get_road_style('East (E)')}"/>
        <rect x="3" y="45" width="22" height="55" fill="white" stroke="black" style="{get_road_style('West (W)')}"/><text x="14" y="72.5" text-anchor="middle" dominant-baseline="central" font-size="14" font-weight="bold" transform="rotate(-90 14,72.5)" style="{get_road_style('West (W)')}">{res['sl']:,}</text>
        <rect x="21" y="45" width="22" height="55" fill="white" stroke="black" style="{get_road_style('North (N)')}"/><text x="32" y="72.5" text-anchor="middle" dominant-baseline="central" font-size="14" font-weight="bold" transform="rotate(-90 32,72.5)" style="{get_road_style('North (N)')}">{res['st']:,}</text>
        <rect x="39" y="45" width="22" height="55" fill="white" stroke="black" style="{get_road_style('East (E)')}"/><text x="50" y="72.5" text-anchor="middle" dominant-baseline="central" font-size="14" font-weight="bold" transform="rotate(-90 50,72.5)" style="{get_road_style('East (E)')}">{res['sr']:,}</text>
    </g>''' if disabled_direction != 'South (S)' else ''}

    {f'''<g transform="translate(265, 300)" style="{get_road_style('West (W)')}">
        <path d="M -30 14 Q 5 14 5 -10" fill="none" stroke="black" stroke-width="2" marker-end="url(#arrow)" style="{get_road_style('North (N)')}"/>
        <path d="M -30 32 H 10" fill="none" stroke="black" stroke-width="2" marker-end="url(#arrow)" style="{get_road_style('East (E)')}"/>
        <path d="M -30 50 Q 5 50 5 75" fill="none" stroke="black" stroke-width="2" marker-end="url(#arrow)" style="{get_road_style('South (S)')}"/>
        <rect x="-85" y="1" width="55" height="22" fill="white" stroke="black" style="{get_road_style('North (N)')}"/><text x="-57.5" y="12" text-anchor="middle" dominant-baseline="central" font-size="14" font-weight="bold" style="{get_road_style('North (N)')}">{res['wl']:,}</text>
        <rect x="-85" y="21" width="55" height="22" fill="white" stroke="black" style="{get_road_style('East (E)')}"/><text x="-57.5" y="32" text-anchor="middle" dominant-baseline="central" font-size="14" font-weight="bold" style="{get_road_style('East (E)')}">{res['wt']:,}</text>
        <rect x="-85" y="41" width="55" height="22" fill="white" stroke="black" style="{get_road_style('South (S)')}"/><text x="-57.5" y="52" text-anchor="middle" dominant-baseline="central" font-size="14" font-weight="bold" style="{get_road_style('South (S)')}">{res['wr']:,}</text>
    </g>''' if disabled_direction != 'West (W)' else ''}

    {f'''<g transform="translate(525, 385)" style="{get_road_style('East (E)')}">
        <path d="M 60 50 Q 25 50 25 75" fill="none" stroke="black" stroke-width="2" marker-end="url(#arrow)" style="{get_road_style('South (S)')}"/>
        <path d="M 60 32 H 20" fill="none" stroke="black" stroke-width="2" marker-end="url(#arrow)" style="{get_road_style('West (W)')}"/>
        <path d="M 60 14 Q 25 14 25 -10" fill="none" stroke="black" stroke-width="2" marker-end="url(#arrow)" style="{get_road_style('North (N)')}"/>
        <rect x="60" y="41" width="55" height="22" fill="white" stroke="black" style="{get_road_style('South (S)')}"/><text x="87.5" y="52" text-anchor="middle" dominant-baseline="central" font-size="14" font-weight="bold" style="{get_road_style('South (S)')}">{res['el']:,}</text>
        <rect x="60" y="21" width="55" height="22" fill="white" stroke="black" style="{get_road_style('West (W)')}"/><text x="87.5" y="32" text-anchor="middle" dominant-baseline="central" font-size="14" font-weight="bold" style="{get_road_style('West (W)')}">{res['et']:,}</text>
        <rect x="60" y="1" width="55" height="22" fill="white" stroke="black" style="{get_road_style('North (N)')}"/><text x="87.5" y="12" text-anchor="middle" dominant-baseline="central" font-size="14" font-weight="bold" style="{get_road_style('North (N)')}">{res['er']:,}</text>
    </g>''' if disabled_direction != 'East (E)' else ''}

    <g transform="translate(630, 600)">
        <rect x="0" y="0" width="200" height="120" fill="#f0f4f7" stroke="#2c3e50" stroke-width="2" rx="10"/>
        <text x="100" y="25" text-anchor="middle" font-size="16" font-weight="bold" fill="#2c3e50">สรุปผลรวม (Total)</text>
        <line x1="10" y1="35" x2="190" y2="35" stroke="#2c3e50" stroke-width="1"/>
        <text x="20" y="60" font-size="14" font-weight="bold" fill="#2E7D32">Total IN:</text> <text x="180" y="60" text-anchor="end" font-size="14" font-weight="bold">{total_in:,}</text>
        <text x="20" y="85" font-size="14" font-weight="bold" fill="#C62828">Total OUT:</text> <text x="180" y="85" text-anchor="end" font-size="14" font-weight="bold">{total_out:,}</text>
        <text x="20" y="108" font-size="14" font-weight="bold" fill="#1976D2">Diff (%):</text> <text x="180" y="108" text-anchor="end" font-size="14" font-weight="bold">{diff:,} ({p_diff:.2f}%)</text>
    </g>

    <text x="340" y="180" transform="rotate(-90 340,180)" font-size="13" fill="blue" font-weight="bold" style="{get_road_style('North (N)')}">{n_road}</text>
    <text x="515" y="550" transform="rotate(-90 515,550)" font-size="13" fill="blue" font-weight="bold" style="{get_road_style('South (S)')}">{s_road}</text>
    <text x="650" y="270" font-size="13" fill="blue" font-weight="bold" style="{get_road_style('East (E)')}">{e_road}</text>
    <text x="100" y="485" font-size="13" fill="blue" font-weight="bold" style="{get_road_style('West (W)')}">{w_road}</text>
</svg>
</div>
"""

st.components.v1.html(svg_code, height=750)
