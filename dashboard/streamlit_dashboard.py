import os
import sqlite3
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="CanHealth Intelligence - Healthcare Analytics",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DISTINCT EMERALD & TEAL HEALTHCARE THEME (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', 'Inter', sans-serif;
    }

    /* Deep Emerald & Cyan Oceanic Radial Background */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #064e3b 0%, #0f2922 40%, #020617 100%);
        color: #f8fafc;
    }

    /* Glassmorphism Cards with Emerald Border Glow */
    .glass-card {
        background: rgba(15, 23, 42, 0.65);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(45, 212, 191, 0.2);
        border-radius: 20px;
        padding: 26px;
        margin-bottom: 24px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.45);
        transition: transform 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
    }

    .glass-card:hover {
        border-color: rgba(45, 212, 191, 0.5);
        box-shadow: 0 25px 50px rgba(45, 212, 191, 0.15);
    }

    /* Metrics Container */
    .metric-container {
        background: rgba(6, 78, 59, 0.35);
        border: 1px solid rgba(45, 212, 191, 0.25);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
    }

    .metric-val {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #2dd4bf 0%, #38bdf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .metric-lbl {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-top: 4px;
    }

    /* Pill Badges */
    .badge-tag {
        display: inline-block;
        background: rgba(45, 212, 191, 0.15);
        border: 1px solid rgba(45, 212, 191, 0.35);
        color: #99f6e4;
        padding: 6px 18px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0 6px 14px 6px;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)

# --- DATABASE CONNECTION ---
DB_PATH = "/Users/shuprov630/canhealth-analytics/canhealth.db"

@st.cache_data
def run_query(query):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

if not os.path.exists(DB_PATH):
    import setup_sqlite
    setup_sqlite.main()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown('<div style="text-align: center; padding: 12px 0;"><img src="https://img.icons8.com/isometric/120/hospital.png" width="80"></div>', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align: center; color: #99f6e4; font-weight: 700;">CanHealth Intelligence</h3>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #94a3b8; font-size: 0.9rem;">National Healthcare Analytics Platform</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    page = st.radio(
        "Navigation Menu",
        [
            "📊 Executive Overview",
            "🗺️ Province Deep Dive",
            "🩺 Procedure Analysis",
            "⚖️ Equity & Access Analysis",
            "🏥 Hospital Scorecard"
        ]
    )
    
    st.markdown("---")
    st.markdown("#### ⚙️ Data Warehouse Details")
    st.caption("• **Architecture**: PostgreSQL / SQLite Star Schema")
    st.caption("• **Dimensions**: Hospitals, Periods, Procedures")
    st.caption("• **Fact Tables**: Wait Times, Financial Performance")

# --- HEADER ---
st.markdown("""
<div style="text-align: center; padding: 10px 0 30px 0;">
    <span class="badge-tag">🇨🇦 Health Data Warehouse</span>
    <span class="badge-tag">📈 Clinical & Financial BI</span>
    <span class="badge-tag">⚡ Star Schema Engine</span>
    <h1 style="background: linear-gradient(135deg, #2dd4bf 0%, #38bdf8 50%, #a855f7 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3.2rem; font-weight: 800; letter-spacing: -0.02em;">
        CanHealth National Healthcare Analytics
    </h1>
    <p style="color: #94a3b8; font-size: 1.2rem; max-width: 800px; margin: 0 auto; line-height: 1.6;">
        Enterprise Data Warehouse & Business Intelligence Platform Analyzing Canadian Hospital Operational Efficiency, Wait Times, and Access Equity.
    </p>
</div>
""", unsafe_allow_html=True)

# --- PAGE 1: EXECUTIVE OVERVIEW ---
if page == "📊 Executive Overview":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<h3 style="color: #2dd4bf; margin-bottom: 16px;">📈 National Key Performance Indicators</h3>', unsafe_allow_html=True)
    
    kpi_query = """
    SELECT 
        SUM(patient_count) as total_volume,
        ROUND(AVG(p90_wait_days), 1) as avg_p90_wait,
        ROUND(AVG(pct_within_benchmark), 1) as avg_benchmark_pct,
        COUNT(DISTINCT hospital_id) as total_hospitals
    FROM fact_wait_times
    """
    kpis = run_query(kpi_query).iloc[0]
    
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-container"><div class="metric-val">{int(kpis["total_volume"]):,}</div><div class="metric-lbl">Total Patient Visits</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-container"><div class="metric-val">{kpis["avg_p90_wait"]}d</div><div class="metric-lbl">Avg P90 Wait Time</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-container"><div class="metric-val">{kpis["avg_benchmark_pct"]}%</div><div class="metric-lbl">Benchmark Met Target</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-container"><div class="metric-val">{int(kpis["total_hospitals"])}</div><div class="metric-lbl">Hospitals Reporting</div></div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<h3 style="color: #38bdf8; margin-bottom: 12px;">📅 Benchmark Compliance Trend (2014-2023)</h3>', unsafe_allow_html=True)
        trend_query = """
        SELECT p.fiscal_year, ROUND(AVG(w.pct_within_benchmark), 1) as benchmark_pct
        FROM fact_wait_times w
        JOIN dim_periods p ON w.period_id = p.period_id
        GROUP BY p.fiscal_year
        ORDER BY p.fiscal_year
        """
        df_trend = run_query(trend_query)
        fig_trend = px.line(df_trend, x='fiscal_year', y='benchmark_pct', markers=True, color_discrete_sequence=['#2dd4bf'])
        fig_trend.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#f8fafc', family='Outfit'), height=340)
        st.plotly_chart(fig_trend, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<h3 style="color: #2dd4bf; margin-bottom: 12px;">🇨🇦 Provincial Benchmark Compliance Ranking</h3>', unsafe_allow_html=True)
        prov_query = """
        SELECT h.province_name as province, ROUND(AVG(w.pct_within_benchmark), 1) as benchmark_pct
        FROM fact_wait_times w
        JOIN dim_hospitals h ON w.hospital_id = h.hospital_id
        GROUP BY h.province_name
        ORDER BY benchmark_pct DESC
        """
        df_prov = run_query(prov_query)
        fig_prov = px.bar(df_prov, x='province', y='benchmark_pct', color='benchmark_pct', color_continuous_scale='tealgrn')
        fig_prov.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#f8fafc', family='Outfit'), height=340)
        st.plotly_chart(fig_prov, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE 2: PROVINCE DEEP DIVE ---
elif page == "🗺️ Province Deep Dive":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<h3 style="color: #2dd4bf;">🗺️ Provincial Comparative Performance</h3>', unsafe_allow_html=True)
    
    p_query = """
    SELECT h.province_name as province, pr.category, ROUND(AVG(w.p90_wait_days), 1) as avg_p90, ROUND(AVG(w.pct_within_benchmark), 1) as benchmark_pct, SUM(w.patient_count) as total_vol
    FROM fact_wait_times w
    JOIN dim_hospitals h ON w.hospital_id = h.hospital_id
    JOIN dim_procedures pr ON w.procedure_id = pr.procedure_id
    GROUP BY h.province_name, pr.category
    """
    df_p = run_query(p_query)
    
    category_filter = st.selectbox("Select Procedure Category", ["All"] + list(df_p['category'].unique()))
    if category_filter != "All":
        df_p = df_p[df_p['category'] == category_filter]
        
    fig_p = px.bar(df_p, x='province', y='avg_p90', color='category', barmode='group', title="Avg 90th Percentile Wait Days by Province", color_discrete_sequence=px.colors.qualitative.Teal)
    fig_p.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#f8fafc', family='Outfit'), height=450)
    st.plotly_chart(fig_p, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE 3: PROCEDURE ANALYSIS ---
elif page == "🩺 Procedure Analysis":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<h3 style="color: #38bdf8;">🩺 Procedure Wait Time vs Benchmark Target</h3>', unsafe_allow_html=True)
    
    proc_query = """
    SELECT pr.name as procedure_name, pr.benchmark_90_days as target_days, ROUND(AVG(w.p90_wait_days), 1) as actual_p90, ROUND(AVG(w.pct_within_benchmark), 1) as benchmark_pct
    FROM fact_wait_times w
    JOIN dim_procedures pr ON w.procedure_id = pr.procedure_id
    GROUP BY pr.name, pr.benchmark_90_days
    ORDER BY actual_p90 DESC
    """
    df_proc = run_query(proc_query)
    
    fig_proc = go.Figure()
    fig_proc.add_trace(go.Bar(x=df_proc['procedure_name'], y=df_proc['actual_p90'], name='Actual P90 Wait (Days)', marker_color='#2dd4bf'))
    fig_proc.add_trace(go.Bar(x=df_proc['procedure_name'], y=df_proc['target_days'], name='Benchmark Target (Days)', marker_color='#38bdf8'))
    
    fig_proc.update_layout(barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#f8fafc', family='Outfit'), height=450)
    st.plotly_chart(fig_proc, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE 4: EQUITY ANALYSIS ---
elif page == "⚖️ Equity & Access Analysis":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<h3 style="color: #2dd4bf;">⚖️ Urban vs Rural Facility Healthcare Access Equity</h3>', unsafe_allow_html=True)
    
    eq_query = """
    SELECT h.urban_rural, pr.name as procedure_name, ROUND(AVG(w.p90_wait_days), 1) as avg_p90
    FROM fact_wait_times w
    JOIN dim_hospitals h ON w.hospital_id = h.hospital_id
    JOIN dim_procedures pr ON w.procedure_id = pr.procedure_id
    GROUP BY h.urban_rural, pr.name
    """
    df_eq = run_query(eq_query)
    
    fig_eq = px.bar(df_eq, x='procedure_name', y='avg_p90', color='urban_rural', barmode='group', title="Urban vs Rural P90 Wait Times", color_discrete_sequence=['#2dd4bf', '#f472b6'])
    fig_eq.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#f8fafc', family='Outfit'), height=450)
    st.plotly_chart(fig_eq, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE 5: HOSPITAL SCORECARD ---
elif page == "🏥 Hospital Scorecard":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<h3 style="color: #38bdf8;">🏥 Hospital Performance Scorecard & Financial Insights</h3>', unsafe_allow_html=True)
    
    hosp_query = """
    SELECT h.hospital_name, h.province_name as province, h.urban_rural, h.bed_count, 
           ROUND(AVG(w.p90_wait_days), 1) as avg_wait_days,
           ROUND(AVG(w.pct_within_benchmark), 1) as benchmark_compliance_pct,
           SUM(w.patient_count) as total_patients
    FROM dim_hospitals h
    LEFT JOIN fact_wait_times w ON h.hospital_id = w.hospital_id
    GROUP BY h.hospital_name, h.province_name, h.urban_rural, h.bed_count
    LIMIT 100
    """
    df_hosp = run_query(hosp_query)
    st.dataframe(df_hosp, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
