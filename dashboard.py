import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio

# Plotly dark theme
pio.templates.default = "plotly_dark"

# Streamlit config
st.set_page_config(page_title="AI Fraud Detection Agent", layout="wide")

# Load custom dark CSS
st.markdown('<style>{}</style>'.format(open('assets/style.css').read()), unsafe_allow_html=True)

# Header
st.markdown("""
<div class='header'>
    <h1>🧠 Real-Time Fraud Detection Dashboard</h1>
    <p>Monitor fraud trends, top users, and live fraud alerts</p>
</div>
""", unsafe_allow_html=True)

# Sidebar File Upload
with st.sidebar:
    st.markdown("### 📁 Upload Transaction File")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

# Load Data
if uploaded_file:
    df = pd.read_csv(uploaded_file, parse_dates=['timestamp'])
    st.success("✅ Uploaded file loaded successfully.")
else:
    df = pd.read_csv('large_financial_transactions.csv', parse_dates=['timestamp'])
    st.info("ℹ️ Using default dataset.")

# Preview Data
with st.expander("🔍 Preview Data"):
    st.dataframe(df.head(10), use_container_width=True)

# Sidebar Filters (No Minimum Amount)
st.sidebar.markdown("### ⚙️ Filter Transactions")
txn_type = st.sidebar.selectbox("Transaction Type", ["All", "PAYMENT", "TRANSFER", "CASH_OUT", "DEPOSIT"])
time_of_day = st.sidebar.slider("Hour of Day", 0, 23, (0, 23))

# Apply Filters
filtered_df = df[(df['timestamp'].dt.hour >= time_of_day[0]) & 
                 (df['timestamp'].dt.hour <= time_of_day[1])]
if txn_type != "All":
    filtered_df = filtered_df[filtered_df['transaction_type'] == txn_type]

# KPIs
total_txns = len(filtered_df)
fraud_txns = filtered_df['is_fraud'].sum()
fraud_rate = (fraud_txns / total_txns) * 100 if total_txns > 0 else 0

st.markdown("## 📊 Key Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Transactions", f"{total_txns}")
col2.metric("Fraudulent Transactions", f"{fraud_txns}")
col3.metric("Fraud Rate (%)", f"{fraud_rate:.2f}%")

# 🚨 Fraud Threshold Slider with Tooltip-style ℹ️
st.markdown("## 🚨 Set Fraud Threshold (%) ℹ️")
with st.expander("ℹ️ What is this?"):
    st.markdown("""
    - Set the **maximum fraud rate** you consider acceptable.  
    - If the **current fraud rate** exceeds this and there are **high-value frauds** (amount > 15,000),  
      a high fraud alert will trigger.  
    """, unsafe_allow_html=True)

fraud_threshold = st.slider("Select fraud risk threshold (%)", 0, 100, 15)

# Fraud Alert Logic
if total_txns == 0:
    st.warning("⚠️ No transactions after filtering. Please adjust your filters.")
else:
    high_value_frauds = filtered_df[(filtered_df['amount'] > 15000) & (filtered_df['is_fraud'] == 1)]

    if fraud_rate > fraud_threshold and len(high_value_frauds) > 0:
        st.markdown(f"<div class='alert-high'>🚨 High Fraud Alert!<br>Fraud rate: {fraud_rate:.2f}%<br>High-value frauds detected: {len(high_value_frauds)}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='alert-low'>✅ Fraud Levels Normal. Fraud rate: {fraud_rate:.2f}%</div>", unsafe_allow_html=True)

# Area Chart: Fraud by Hour
st.markdown("## ⏰ Fraud Trends by Hour")
df['hour'] = df['timestamp'].dt.hour
fraud_by_hour = df.groupby('hour')['is_fraud'].sum().reset_index()

fig_area = px.area(
    fraud_by_hour,
    x='hour',
    y='is_fraud',
    labels={'is_fraud': 'Fraud Count', 'hour': 'Hour of Day'},
    height=400
)
fig_area.update_traces(mode='lines+markers', fill='tozeroy')
st.plotly_chart(fig_area, use_container_width=True)

# Top Users and Donut Side-by-Side
st.markdown("## 👤 Top 10 Users and Fraud Breakdown")
col1, col2 = st.columns(2)

# Bar Chart
with col1:
    top_users = df.groupby('from_user')['amount'].sum().sort_values(ascending=False).head(10).reset_index()
    fig_bar = px.bar(
        top_users,
        x='amount',
        y='from_user',
        orientation='h',
        color='amount',
        color_continuous_scale='Viridis',
        labels={'from_user': 'User', 'amount': 'Total Sent'},
        height=500
    )
    fig_bar.update_layout(
        yaxis=dict(categoryorder='total ascending'),
        title="Top 10 Users by Amount Sent",
        showlegend=False,
        margin=dict(l=50, r=20, t=50, b=40)
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# Donut Chart (Updated Colors)
with col2:
    fraud_counts = filtered_df['is_fraud'].value_counts().rename(index={0: 'Legit', 1: 'Fraud'}).reset_index()
    fraud_counts.columns = ['Transaction Type', 'Count']

    fig_donut = px.pie(
        fraud_counts,
        names='Transaction Type',
        values='Count',
        hole=0.55,
        title="Fraud vs Legit Transactions",
        color='Transaction Type',
        color_discrete_map={'Fraud': '#9C27B0', 'Legit': '#900C3F'},  # Purple & Aqua
        template="plotly_dark",
        height=500
    )
    fig_donut.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_donut, use_container_width=True)


if st.button("📧 Send Fraud Alert Email"):
    if fraud_rate > fraud_threshold and len(high_value_frauds) > 0:
        st.success("✅ Simulated: Email alert sent.")
    else:
        st.info("Fraud rate below threshold or no high-value frauds.")
