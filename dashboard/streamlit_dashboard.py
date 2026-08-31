import os
import sqlite3
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="CanHealth Analytics - Healthcare Intelligence Portal",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', 'Inter', sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at 50% 0%, #0f172a 0%, #020617 100%);
        color: #f8fafc;
    }

    .glass-card {
        background: rgba(30, 41, 59, 0.45);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 18px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4);
    }

    .metric-container {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 18px;
        text-align: center;
    }

    .metric-val {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .metric-lbl {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 4px;
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

# Initialize database if missing
if not os.path.exists(DB_PATH):
    import setup_sqlite
    setup_sqlite.main()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/hospital.png", width=75)
    st.markdown("### 🏥 CanHealth Intelligence")
    st.caption("National Healthcare Analytics & Wait Time Intelligence Engine")
    
    st.markdown("---")
    page = st.radio(
        "Navigation Menu",
        [
            "📊 Executive Overview",
            "🗺️ Province Deep Dive",
            "🩺 Procedure Analysis",
            "⚖️ Equity & Facility Type",
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
<div style="text-align: center; padding: 10px 0 25px 0;">
    <h1 style="background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem; font-weight: 800;">
        CanHealth National Analytics Platform
    </h1>
    <p style="color: #94a3b8; font-size: 1.15rem; max-width: 750px; margin: 0 auto;">
        Interactive Business Intelligence & Data Warehouse Analytics for Canadian Healthcare Performance
    </p>
</div>
""", unsafe_allow_html=True)

# --- PAGE 1: EXECUTIVE OVERVIEW ---
if page == "📊 Executive Overview":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("📈 National Key Performance Indicators")
    
    kpi_query = """
    SELECT 
        SUM(completed_volume) as total_volume,
        ROUND(AVG(p90_wait_days), 1) as avg_p90_wait,
        ROUND(AVG(within_benchmark_pct), 1) as avg_benchmark_pct,
        COUNT(DISTINCT hospital_id) as total_hospitals
    FROM fact_wait_times
    """
    kpis = run_query(kpi_query).iloc[0]
    
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-container"><div class="metric-val">{kpis["total_volume"]:,}</div><div class="metric-lbl">Total Procedures</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-container"><div class="metric-val">{kpis["avg_p90_wait"]}d</div><div class="metric-lbl">Avg P90 Wait Time</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-container"><div class="metric-val">{kpis["avg_benchmark_pct"]}%</div><div class="metric-lbl">Benchmark Met Target</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-container"><div class="metric-val">{kpis["total_hospitals"]}</div><div class="metric-lbl">Hospitals Reporting</div></div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("📅 Benchmark Compliance Trend (2014-2023)")
        trend_query = """
        SELECT p.fiscal_year, ROUND(AVG(w.within_benchmark_pct), 1) as benchmark_pct
        FROM fact_wait_times w
        JOIN dim_periods p ON w.period_id = p.period_id
        GROUP BY p.fiscal_year
        ORDER BY p.fiscal_year
        """
        df_trend = run_query(trend_query)
        fig_trend = px.line(df_trend, x='fiscal_year', y='benchmark_pct', markers=True, color_discrete_sequence=['#38bdf8'])
        fig_trend.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#f8fafc'), height=340)
        st.plotly_chart(fig_trend, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("🇨🇦 Provincial Benchmark Compliance Ranking")
        prov_query = """
        SELECT h.province, ROUND(AVG(w.within_benchmark_pct), 1) as benchmark_pct
        FROM fact_wait_times w
        JOIN dim_hospitals h ON w.hospital_id = h.hospital_id
        GROUP BY h.province
        ORDER BY benchmark_pct DESC
        """
        df_prov = run_query(prov_query)
        fig_prov = px.bar(df_prov, x='province', y='benchmark_pct', color='benchmark_pct', color_continuous_scale='viridis')
        fig_prov.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#f8fafc'), height=340)
        st.plotly_chart(fig_prov, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE 2: PROVINCE DEEP DIVE ---
elif page == "🗺️ Province Deep Dive":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("🗺️ Provincial Comparative Performance")
    
    p_query = """
    SELECT h.province, p.category_name, ROUND(AVG(w.p90_wait_days), 1) as avg_p90, ROUND(AVG(w.within_benchmark_pct), 1) as benchmark_pct, SUM(w.completed_volume) as total_vol
    FROM fact_wait_times w
    JOIN dim_hospitals h ON w.hospital_id = h.hospital_id
    JOIN dim_procedures p ON w.procedure_id = p.procedure_id
    GROUP BY h.province, p.category_name
    """
    df_p = run_query(p_query)
    
    category_filter = st.selectbox("Select Procedure Category", ["All"] + list(df_p['category_name'].unique()))
    if category_filter != "All":
        df_p = df_p[df_p['category_name'] == category_filter]
        
    fig_p = px.bar(df_p, x='province', y='avg_p90', color='category_name', barmode='group', title="Avg 90th Percentile Wait Days by Province")
    fig_p.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#f8fafc'), height=450)
    st.plotly_chart(fig_p, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE 3: PROCEDURE ANALYSIS ---
elif page == "🩺 Procedure Analysis":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("🩺 Procedure Wait Time vs Benchmark Target")
    
    proc_query = """
    SELECT pr.procedure_name, pr.benchmark_target_days, ROUND(AVG(w.p90_wait_days), 1) as actual_p90, ROUND(AVG(w.within_benchmark_pct), 1) as benchmark_pct
    FROM fact_wait_times w
    JOIN dim_procedures pr ON w.procedure_id = pr.procedure_id
    GROUP BY pr.procedure_name, pr.benchmark_target_days
    ORDER BY actual_p90 DESC
    """
    df_proc = run_query(proc_query)
    
    fig_proc = go.Figure()
    fig_proc.add_trace(go.Bar(x=df_proc['procedure_name'], y=df_proc['actual_p90'], name='Actual P90 Wait (Days)', marker_color='#818cf8'))
    fig_proc.add_trace(go.Bar(x=df_proc['procedure_name'], y=df_proc['benchmark_target_days'], name='Benchmark Target (Days)', marker_color='#34d399'))
    
    fig_proc.update_layout(barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#f8fafc'), height=450)
    st.plotly_chart(fig_proc, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE 4: EQUITY ANALYSIS ---
elif page == "⚖️ Equity & Facility Type":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("⚖️ Urban vs Rural Facility Healthcare Access Equity")
    
    eq_query = """
    SELECT h.urban_rural, pr.procedure_name, ROUND(AVG(w.p90_wait_days), 1) as avg_p90
    FROM fact_wait_times w
    JOIN dim_hospitals h ON w.hospital_id = h.hospital_id
    JOIN dim_procedures pr ON w.procedure_id = pr.procedure_id
    GROUP BY h.urban_rural, pr.procedure_name
    """
    df_eq = run_query(eq_query)
    
    fig_eq = px.bar(df_eq, x='procedure_name', y='avg_p90', color='urban_rural', barmode='group', title="Urban vs Rural P90 Wait Times")
    fig_eq.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#f8fafc'), height=450)
    st.plotly_chart(fig_eq, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE 5: HOSPITAL SCORECARD ---
elif page == "🏥 Hospital Scorecard":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("🏥 Hospital Performance Scorecard & Financial Insights")
    
    hosp_query = """
    SELECT h.hospital_name, h.province, h.urban_rural, h.bed_count, 
           ROUND(AVG(w.p90_wait_days), 1) as avg_wait_days,
           ROUND(AVG(w.within_benchmark_pct), 1) as benchmark_compliance_pct,
           ROUND(AVG(f.operating_margin_pct), 1) as margin_pct
    FROM dim_hospitals h
    LEFT JOIN fact_wait_times w ON h.hospital_id = w.hospital_id
    LEFT JOIN fact_financials f ON h.hospital_id = f.hospital_id
    GROUP BY h.hospital_name, h.province, h.urban_rural, h.bed_count
    LIMIT 100
    """
    df_hosp = run_query(hosp_query)
    st.dataframe(df_hosp, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
