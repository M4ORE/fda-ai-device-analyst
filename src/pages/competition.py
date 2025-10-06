"""
Competitive landscape analysis for FDA AI/ML devices
"""
import sys
import os
import sqlite3

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

st.set_page_config(page_title="Competition Analysis", page_icon="🔍", layout="wide")

@st.cache_data
def load_data():
    """Load device data from SQLite"""
    db_path = os.getenv('SQLITE_DB_PATH', './data/devices.db')
    if not os.path.exists(db_path):
        return None

    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("""
        SELECT submission_number, decision_date, device_name, company,
               panel, product_code, imaging_modality, body_region, clinical_application
        FROM devices
    """, conn)
    conn.close()

    df['decision_date'] = pd.to_datetime(df['decision_date'], errors='coerce')
    return df

@st.cache_data
def get_panel_list(df):
    """Get sorted list of panels"""
    return sorted(df['panel'].dropna().unique().tolist())

@st.cache_data
def get_product_codes_by_panel(df, panel):
    """Get product codes filtered by panel"""
    if panel == 'All':
        codes = df['product_code'].dropna().unique()
    else:
        codes = df[df['panel'] == panel]['product_code'].dropna().unique()
    return sorted(codes.tolist())

@st.cache_data
def analyze_competition(df, panel, product_code, imaging_modality, body_region, clinical_application):
    """Analyze competitive landscape for given filters"""
    filtered = df.copy()

    if panel != 'All':
        filtered = filtered[filtered['panel'] == panel]

    if product_code != 'All':
        filtered = filtered[filtered['product_code'] == product_code]

    if imaging_modality != 'All':
        filtered = filtered[filtered['imaging_modality'] == imaging_modality]

    if body_region != 'All':
        filtered = filtered[filtered['body_region'] == body_region]

    if clinical_application != 'All':
        filtered = filtered[filtered['clinical_application'] == clinical_application]

    # Company aggregation
    company_stats = filtered.groupby('company').agg({
        'submission_number': 'count',
        'device_name': lambda x: list(x),
        'decision_date': ['min', 'max']
    }).reset_index()

    company_stats.columns = ['company', 'device_count', 'devices', 'first_approval', 'last_approval']
    company_stats = company_stats.sort_values('device_count', ascending=False)

    return filtered, company_stats

def main():
    st.title("🔍 Competitive Landscape Analysis")
    st.markdown("Analyze competing companies and products in FDA AI/ML medical device market")

    # Load data
    df = load_data()
    if df is None or len(df) == 0:
        st.error("No data available. Run `python src/extract.py` first.")
        return

    st.markdown("---")

    # Check if AI classification is available
    has_classification = df['imaging_modality'].notna().any()

    # Filters
    if has_classification:
        st.subheader("Filters")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Traditional Classification**")
            panels = ['All'] + get_panel_list(df)
            selected_panel = st.selectbox("Panel", panels, help="Medical specialty area")

            product_codes = ['All'] + get_product_codes_by_panel(df, selected_panel)
            selected_code = st.selectbox("Product Code", product_codes, help="Specific device classification")

        with col2:
            st.markdown("**AI Classification - Clinical**")
            modalities = ['All'] + sorted([m for m in df['imaging_modality'].dropna().unique() if m != 'Unknown'])
            selected_modality = st.selectbox("Imaging Modality", modalities, help="CT, MRI, X-ray, etc.")

            regions = ['All'] + sorted([r for r in df['body_region'].dropna().unique() if r != 'Unknown'])
            selected_region = st.selectbox("Body Region", regions, help="Brain, Heart, Chest, etc.")

        with col3:
            st.markdown("**AI Classification - Purpose**")
            applications = ['All'] + sorted([a for a in df['clinical_application'].dropna().unique() if a != 'Unknown'])
            selected_application = st.selectbox("Clinical Application", applications, help="Screening, Diagnosis, etc.")

    else:
        st.info("💡 AI classification not yet available. Run `python src/classify.py` to enable advanced filtering by modality, body region, and clinical application.")
        col1, col2 = st.columns(2)

        with col1:
            panels = ['All'] + get_panel_list(df)
            selected_panel = st.selectbox("Filter by Panel", panels, help="Medical specialty area")

        with col2:
            product_codes = ['All'] + get_product_codes_by_panel(df, selected_panel)
            selected_code = st.selectbox("Filter by Product Code", product_codes, help="Specific device classification")

        selected_modality = 'All'
        selected_region = 'All'
        selected_application = 'All'

    # Analysis
    filtered_df, company_stats = analyze_competition(df, selected_panel, selected_code, selected_modality, selected_region, selected_application)

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Devices", len(filtered_df))
    with col2:
        st.metric("Competing Companies", len(company_stats))
    with col3:
        st.metric("Product Codes", filtered_df['product_code'].nunique())
    with col4:
        if len(company_stats) > 0:
            market_leader = company_stats.iloc[0]['company']
            leader_share = company_stats.iloc[0]['device_count']
            st.metric("Market Leader", f"{market_leader[:20]}...", f"{leader_share} devices")
        else:
            st.metric("Market Leader", "N/A")

    st.markdown("---")

    # Company distribution
    st.subheader("Company Market Share")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Top companies bar chart
        top_n = st.slider("Show top N companies", 5, 50, 15, 5)
        top_companies = company_stats.head(top_n)

        fig_bar = px.bar(
            top_companies,
            x='device_count',
            y='company',
            orientation='h',
            labels={'device_count': 'Number of Devices', 'company': 'Company'},
            title=f'Top {top_n} Companies by Device Count'
        )
        fig_bar.update_layout(height=max(400, top_n * 25), yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        # Market concentration pie chart
        if len(company_stats) > 10:
            top_10 = company_stats.head(10).copy()
            others_count = company_stats.iloc[10:]['device_count'].sum()
            top_10 = pd.concat([top_10, pd.DataFrame([{
                'company': 'Others',
                'device_count': others_count
            }])], ignore_index=True)
        else:
            top_10 = company_stats.copy()

        fig_pie = px.pie(
            top_10,
            values='device_count',
            names='company',
            title='Market Concentration (Top 10)'
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # Company details table
    st.subheader("Company Details")

    # Search
    search_company = st.text_input("Search company name")

    display_stats = company_stats.copy()
    if search_company:
        display_stats = display_stats[display_stats['company'].str.contains(search_company, case=False, na=False)]

    # Format for display
    display_table = display_stats.copy()
    display_table['first_approval'] = pd.to_datetime(display_table['first_approval']).dt.strftime('%Y-%m-%d')
    display_table['last_approval'] = pd.to_datetime(display_table['last_approval']).dt.strftime('%Y-%m-%d')
    display_table = display_table[['company', 'device_count', 'first_approval', 'last_approval']]
    display_table.columns = ['Company', 'Device Count', 'First Approval', 'Latest Approval']

    st.dataframe(display_table, use_container_width=True, height=400)

    # Device list expander
    st.markdown("---")
    st.subheader("Device Details")

    selected_company = st.selectbox("Select company to view devices", ['All'] + company_stats['company'].tolist())

    if selected_company != 'All':
        company_devices = filtered_df[filtered_df['company'] == selected_company].copy()
        company_devices = company_devices.sort_values('decision_date', ascending=False)

        st.markdown(f"**{selected_company}** has **{len(company_devices)}** approved devices:")

        if has_classification:
            display_cols = ['decision_date', 'submission_number', 'device_name', 'product_code', 'imaging_modality', 'body_region', 'clinical_application']
        else:
            display_cols = ['decision_date', 'submission_number', 'device_name', 'product_code']

        st.dataframe(
            company_devices[display_cols],
            use_container_width=True,
            height=300
        )
    else:
        device_display = filtered_df.sort_values('decision_date', ascending=False).copy()

        if has_classification:
            display_cols = ['decision_date', 'submission_number', 'device_name', 'company', 'product_code', 'imaging_modality', 'body_region', 'clinical_application']
        else:
            display_cols = ['decision_date', 'submission_number', 'device_name', 'company', 'product_code']

        st.dataframe(
            device_display[display_cols],
            use_container_width=True,
            height=300
        )

    # Export
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        csv_companies = display_table.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Company Statistics (CSV)",
            data=csv_companies,
            file_name=f"competition_analysis_{selected_panel}_{selected_code}.csv",
            mime="text/csv"
        )

    with col2:
        csv_devices = filtered_df[['decision_date', 'submission_number', 'device_name', 'company', 'panel', 'product_code']].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Device List (CSV)",
            data=csv_devices,
            file_name=f"devices_{selected_panel}_{selected_code}.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
