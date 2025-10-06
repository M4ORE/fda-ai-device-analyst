"""
Streamlit dashboard for FDA AI/ML device data visualization
"""
import sys
import os
import sqlite3
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

# Page config
st.set_page_config(
    page_title="FDA AI/ML Medical Devices",
    page_icon="🏥",
    layout="wide"
)

@st.cache_data
def load_data():
    """Load data from SQLite database"""
    db_path = os.getenv('SQLITE_DB_PATH', './data/devices.db')

    if not os.path.exists(db_path):
        return None

    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("""
        SELECT submission_number, decision_date, device_name, company,
               panel, product_code, pdf_pages
        FROM devices
    """, conn)
    conn.close()

    # Parse date
    df['decision_date'] = pd.to_datetime(df['decision_date'], errors='coerce')
    df['year'] = df['decision_date'].dt.year
    df['month'] = df['decision_date'].dt.to_period('M').astype(str)

    return df

def main():
    st.title("FDA AI/ML-Enabled Medical Devices")
    st.markdown("Interactive dashboard for FDA-approved AI/ML medical devices data")

    # Load data
    df = load_data()

    if df is None or len(df) == 0:
        st.warning("No data available. Run data extraction first: `python src/extract.py`")
        return

    # Sidebar filters
    st.sidebar.header("Filters")

    # Panel filter
    panels = ['All'] + sorted(df['panel'].dropna().unique().tolist())
    selected_panel = st.sidebar.selectbox("Panel", panels)

    # Year filter
    years = ['All'] + sorted(df['year'].dropna().unique().tolist(), reverse=True)
    selected_year = st.sidebar.selectbox("Year", years)

    # Apply filters
    filtered_df = df.copy()
    if selected_panel != 'All':
        filtered_df = filtered_df[filtered_df['panel'] == selected_panel]
    if selected_year != 'All':
        filtered_df = filtered_df[filtered_df['year'] == selected_year]

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Devices", len(filtered_df))
    with col2:
        st.metric("Companies", filtered_df['company'].nunique())
    with col3:
        st.metric("Panels", filtered_df['panel'].nunique())
    with col4:
        st.metric("Product Codes", filtered_df['product_code'].nunique())

    st.markdown("---")

    # Timeline chart
    st.subheader("Approval Timeline")
    timeline_df = filtered_df.groupby('month').size().reset_index(name='count')
    fig_timeline = px.line(
        timeline_df,
        x='month',
        y='count',
        title='Device Approvals Over Time',
        labels={'month': 'Month', 'count': 'Number of Approvals'}
    )
    st.plotly_chart(fig_timeline, use_container_width=True)

    # Two columns for charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 Companies")
        company_counts = filtered_df['company'].value_counts().head(10)
        fig_companies = px.bar(
            x=company_counts.values,
            y=company_counts.index,
            orientation='h',
            labels={'x': 'Number of Devices', 'y': 'Company'}
        )
        fig_companies.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_companies, use_container_width=True)

    with col2:
        st.subheader("Panel Distribution")
        panel_counts = filtered_df['panel'].value_counts()
        fig_panels = px.bar(
            x=panel_counts.values,
            y=panel_counts.index,
            orientation='h',
            labels={'x': 'Number of Devices', 'y': 'Panel'}
        )
        fig_panels.update_layout(showlegend=False, height=400, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_panels, use_container_width=True)

    st.markdown("---")

    # Product code distribution
    st.subheader("Top Product Codes")
    code_counts = filtered_df['product_code'].value_counts().head(15)
    fig_codes = px.bar(
        x=code_counts.index,
        y=code_counts.values,
        labels={'x': 'Product Code', 'y': 'Count'}
    )
    st.plotly_chart(fig_codes, use_container_width=True)

    st.markdown("---")

    # Data table
    st.subheader("Device Records")

    # Search
    search_term = st.text_input("Search by device name, company, or submission number")
    if search_term:
        mask = (
            filtered_df['device_name'].str.contains(search_term, case=False, na=False) |
            filtered_df['company'].str.contains(search_term, case=False, na=False) |
            filtered_df['submission_number'].str.contains(search_term, case=False, na=False)
        )
        display_df = filtered_df[mask]
    else:
        display_df = filtered_df

    # Display table
    st.dataframe(
        display_df[['decision_date', 'submission_number', 'device_name', 'company', 'panel', 'product_code']].sort_values('decision_date', ascending=False),
        use_container_width=True,
        height=400
    )

    # Footer
    st.markdown("---")
    st.caption(f"Data: {len(df)} FDA AI/ML-enabled medical devices | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

if __name__ == "__main__":
    main()
