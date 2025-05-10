import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Set page config
st.set_page_config(page_title="Fuel Sales Analysis Dashboard", layout="wide")

# Read the data
@st.cache_data
def load_data():
    # Read statement data
    statement_df = pd.read_csv('data/account_statement.csv')
    statement_df['Date'] = pd.to_datetime(statement_df['Date'], format='%d-%m-%Y')
    
    # Read ledger data with custom parsing
    ledger_df = pd.read_csv('data/account_ledger.csv')
    ledger_df['Date'] = pd.to_datetime(ledger_df['Date'], format='%d/%m/%Y')
    
    # Clean and standardize numeric columns
    for col in ['Debit', 'Credit', 'Balance']:
        # Remove quotes and convert to string
        ledger_df[col] = ledger_df[col].astype(str).str.replace('"', '')
        
        # Extract numeric part and Dr/Cr indicator
        if col == 'Balance':
            # Split into amount and Dr/Cr
            ledger_df['Balance_Amount'] = ledger_df[col].str.extract(r'([\d,]+\.?\d*)').astype(str)
            ledger_df['Balance_Type'] = ledger_df[col].str.extract(r'(Dr|Cr)')
            
            # Convert amount to float
            ledger_df['Balance_Amount'] = ledger_df['Balance_Amount'].str.replace(',', '').astype(float)
            
            # Apply Dr/Cr sign
            ledger_df['Balance_Amount'] = np.where(
                ledger_df['Balance_Type'] == 'Dr',
                ledger_df['Balance_Amount'],
                -ledger_df['Balance_Amount']
            )
        else:
            # Convert Debit and Credit to float
            ledger_df[col] = ledger_df[col].str.replace(',', '').astype(float)
    
    return statement_df, ledger_df

statement_df, ledger_df = load_data()

# Calculate basic metrics
statement_df['Direct_Profit'] = statement_df['Qty.'] * 3
statement_df['Period'] = statement_df['Date'].dt.strftime('%Y-%m')  # Convert Period to string
statement_df['Half_Month'] = np.where(statement_df['Date'].dt.day <= 15, 'First', 'Second')

# Function to calculate interest
def calculate_interest(amount, days):
    monthly_rate = 0.01  # 1% per month
    daily_rate = monthly_rate / 30
    return amount * daily_rate * days

# Get all payment dates
payment_dates = ledger_df[ledger_df['Credit'] > 0].sort_values('Date')
first_payment_date = payment_dates['Date'].min()
last_payment_date = payment_dates['Date'].max()

# Function to calculate interest for each transaction
def calculate_transaction_interest(row):
    # For transactions before first payment, use first payment date
    if row['Date'] < first_payment_date:
        days_to_payment = (first_payment_date - row['Date']).days
        return calculate_interest(row['Amount'], days_to_payment)
    
    # For transactions after last payment, use last payment date
    if row['Date'] > last_payment_date:
        days_to_payment = (row['Date'] - last_payment_date).days
        return calculate_interest(row['Amount'], days_to_payment)
    
    # For transactions between payments, find next credit entry
    next_payment = ledger_df[
        (ledger_df['Date'] > row['Date']) & 
        (ledger_df['Credit'] > 0)
    ].iloc[0] if len(ledger_df[(ledger_df['Date'] > row['Date']) & (ledger_df['Credit'] > 0)]) > 0 else None
    
    if next_payment is None:
        return 0
    
    days_to_payment = (next_payment['Date'] - row['Date']).days
    if days_to_payment <= 0:
        return 0
    
    return calculate_interest(row['Amount'], days_to_payment)

# Calculate interest for each transaction
statement_df['Interest_Cost'] = statement_df.apply(calculate_transaction_interest, axis=1)
statement_df['Net_Profit'] = statement_df['Direct_Profit'] - statement_df['Interest_Cost']

# Create sidebar filters
st.sidebar.title("Filters")

# Date range filter
min_date = statement_df['Date'].min()
max_date = statement_df['Date'].max()
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Vehicle filter
vehicles = ['All'] + sorted(statement_df['Vehicle No.'].unique().tolist())
selected_vehicle = st.sidebar.selectbox("Select Vehicle", vehicles)

# Product filter
products = ['All'] + sorted(statement_df['Product Name'].unique().tolist())
selected_product = st.sidebar.selectbox("Select Product", products)

# Apply filters
filtered_df = statement_df.copy()
if selected_vehicle != 'All':
    filtered_df = filtered_df[filtered_df['Vehicle No.'] == selected_vehicle]
if selected_product != 'All':
    filtered_df = filtered_df[filtered_df['Product Name'] == selected_product]
filtered_df = filtered_df[
    (filtered_df['Date'].dt.date >= date_range[0]) &
    (filtered_df['Date'].dt.date <= date_range[1])
]

# Main dashboard
st.title("Fuel Sales Analysis Dashboard")

# Create tabs for different analyses
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "Overview", "Payment Analysis", "Interest Analysis", 
    "Payment Patterns", "Vehicle Analysis", "Time Analysis",
    "Profit Analysis", "Balance Analysis"
])

with tab1:
    st.header("Overview")
    
    # Payment Information
    col1, col2 = st.columns(2)
    with col1:
        st.write("First Payment:")
        st.write(f"Date: {first_payment_date.strftime('%d-%m-%Y')}")
        st.write(f"Amount: ₹{ledger_df[ledger_df['Date'] == first_payment_date]['Credit'].iloc[0]:,.2f}")
    with col2:
        st.write("Last Payment:")
        st.write(f"Date: {last_payment_date.strftime('%d-%m-%Y')}")
        st.write(f"Amount: ₹{ledger_df[ledger_df['Date'] == last_payment_date]['Credit'].iloc[0]:,.2f}")
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Sales", f"₹{filtered_df['Amount'].sum():,.2f}")
    with col2:
        st.metric("Total Profit", f"₹{filtered_df['Direct_Profit'].sum():,.2f}")
    with col3:
        st.metric("Total Interest Cost", f"₹{filtered_df['Interest_Cost'].sum():,.2f}")
    with col4:
        st.metric("Net Profit", f"₹{filtered_df['Net_Profit'].sum():,.2f}")

with tab2:
    st.header("Payment Analysis")
    
    # Get all payments
    payments = ledger_df[ledger_df['Credit'] > 0].sort_values('Date')
    
    # Create a selectbox for payment selection
    payment_options = [f"{row['Date'].strftime('%d-%m-%Y')} - ₹{row['Credit']:,.2f}" 
                      for _, row in payments.iterrows()]
    selected_payment = st.selectbox("Select Payment to Analyze", payment_options)
    
    # Get the selected payment date
    selected_date = pd.to_datetime(selected_payment.split(' - ')[0], format='%d-%m-%Y')
    
    # Get transactions for this payment
    if selected_date == first_payment_date:
        payment_transactions = statement_df[statement_df['Date'] < selected_date].copy()
    else:
        prev_payment = payments[payments['Date'] < selected_date]['Date'].max()
        payment_transactions = statement_df[
            (statement_df['Date'] > prev_payment) & 
            (statement_df['Date'] <= selected_date)
        ].copy()
    
    payment_transactions['Payment_Date'] = selected_date
    payment_transactions['Days_To_Payment'] = (selected_date - payment_transactions['Date']).dt.days
    
    # Show transactions
    st.subheader(f"Transactions Covered by Payment on {selected_date.strftime('%d-%m-%Y')}")
    st.dataframe(payment_transactions[[
        'Date', 'Vehicle No.', 'Product Name', 'Qty.', 'Amount',
        'Direct_Profit', 'Interest_Cost', 'Net_Profit', 'Days_To_Payment'
    ]].sort_values('Date'))
    
    # Show summary
    st.subheader("Payment Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Transactions", len(payment_transactions))
        st.metric("Total Amount", f"₹{payment_transactions['Amount'].sum():,.2f}")
    with col2:
        st.metric("Total Interest", f"₹{payment_transactions['Interest_Cost'].sum():,.2f}")
        st.metric("Average Interest per Transaction", f"₹{payment_transactions['Interest_Cost'].mean():,.2f}")
    with col3:
        st.metric("Total Profit", f"₹{payment_transactions['Direct_Profit'].sum():,.2f}")
        st.metric("Net Profit", f"₹{payment_transactions['Net_Profit'].sum():,.2f}")
    
    # Show interest distribution
    fig = px.histogram(
        payment_transactions,
        x='Interest_Cost',
        title='Distribution of Interest Costs',
        labels={'Interest_Cost': 'Interest Cost (₹)'}
    )
    st.plotly_chart(fig, key="payment_interest_dist")
    
    # Show payment timeline
    st.subheader("Payment Timeline")
    fig = px.scatter(
        payments,
        x='Date',
        y='Credit',
        title='Payment Amounts Over Time',
        labels={'Credit': 'Payment Amount (₹)'}
    )
    st.plotly_chart(fig, key="payment_timeline")

with tab3:
    st.header("Interest Analysis")
    
    # Interest by period
    interest_by_period = filtered_df.groupby('Period').agg({
        'Amount': 'sum',
        'Interest_Cost': 'sum'
    }).reset_index()
    interest_by_period['Interest_Rate'] = interest_by_period['Interest_Cost'] / interest_by_period['Amount'] * 100
    
    # Show interest trends
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(x=interest_by_period['Period'], y=interest_by_period['Interest_Cost'],
               name="Interest Cost"),
        secondary_y=False
    )
    fig.add_trace(
        go.Scatter(x=interest_by_period['Period'], y=interest_by_period['Interest_Rate'],
                  name="Interest Rate %"),
        secondary_y=True
    )
    fig.update_layout(title="Interest Cost and Rate by Period")
    st.plotly_chart(fig, key="interest_trends")
    
    # Interest by product
    interest_by_product = filtered_df.groupby('Product Name').agg({
        'Amount': 'sum',
        'Interest_Cost': 'sum'
    }).reset_index()
    interest_by_product['Interest_Rate'] = interest_by_product['Interest_Cost'] / interest_by_product['Amount'] * 100
    
    fig = px.bar(
        interest_by_product,
        x='Product Name',
        y=['Interest_Cost', 'Interest_Rate'],
        title='Interest by Product',
        barmode='group'
    )
    st.plotly_chart(fig, key="interest_by_product")

with tab4:
    st.header("Payment Pattern Analysis")
    
    # Payment frequency
    payments = ledger_df[ledger_df['Credit'] > 0].copy()
    payments['Days_Between_Payments'] = payments['Date'].diff().dt.days
    
    # Show payment frequency
    st.subheader("Payment Frequency")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Average Days Between Payments", f"{payments['Days_Between_Payments'].mean():.1f}")
    with col2:
        st.metric("Minimum Days Between Payments", f"{payments['Days_Between_Payments'].min():.1f}")
    with col3:
        st.metric("Maximum Days Between Payments", f"{payments['Days_Between_Payments'].max():.1f}")
    
    # Payment amount analysis
    fig = px.scatter(
        payments,
        x='Date',
        y='Credit',
        title='Payment Amounts Over Time',
        labels={'Credit': 'Payment Amount (₹)'}
    )
    st.plotly_chart(fig, key="payment_amount_analysis")

with tab5:
    st.header("Vehicle Analysis")
    
    # Vehicle-wise analysis
    vehicle_analysis = filtered_df.groupby('Vehicle No.').agg({
        'Amount': 'sum',
        'Interest_Cost': 'sum',
        'Net_Profit': 'sum',
        'Qty.': 'sum'
    }).reset_index()
    
    # Show top vehicles by interest
    st.subheader("Top Vehicles by Interest Cost")
    fig = px.bar(
        vehicle_analysis.sort_values('Interest_Cost', ascending=False).head(10),
        x='Vehicle No.',
        y=['Interest_Cost', 'Net_Profit'],
        title='Top 10 Vehicles by Interest Cost',
        barmode='group'
    )
    st.plotly_chart(fig, key="top_vehicles")
    
    # Show vehicle details
    st.subheader("Vehicle Details")
    st.dataframe(vehicle_analysis.sort_values('Interest_Cost', ascending=False))

with tab6:
    st.header("Time Analysis")
    
    # Daily transaction pattern
    filtered_df['Day_of_Week'] = filtered_df['Date'].dt.day_name()
    daily_pattern = filtered_df.groupby('Day_of_Week').agg({
        'Amount': 'sum',
        'Interest_Cost': 'sum'
    }).reset_index()
    
    fig = px.bar(
        daily_pattern,
        x='Day_of_Week',
        y=['Amount', 'Interest_Cost'],
        title='Transaction Pattern by Day of Week',
        barmode='group'
    )
    st.plotly_chart(fig, key="daily_pattern")
    
    # Monthly trends
    monthly_trends = filtered_df.groupby('Period').agg({
        'Amount': 'sum',
        'Interest_Cost': 'sum',
        'Net_Profit': 'sum'
    }).reset_index()
    
    fig = px.line(
        monthly_trends,
        x='Period',
        y=['Amount', 'Interest_Cost', 'Net_Profit'],
        title='Monthly Trends'
    )
    st.plotly_chart(fig, key="monthly_trends")

with tab7:
    st.header("Profit Analysis")
    
    # Profit margins
    filtered_df['Profit_Margin'] = filtered_df['Direct_Profit'] / filtered_df['Amount'] * 100
    filtered_df['Net_Profit_Margin'] = filtered_df['Net_Profit'] / filtered_df['Amount'] * 100
    
    # Show profit margins
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(x=filtered_df['Period'], y=filtered_df['Direct_Profit'],
               name="Direct Profit"),
        secondary_y=False
    )
    fig.add_trace(
        go.Scatter(x=filtered_df['Period'], y=filtered_df['Profit_Margin'],
                  name="Profit Margin %"),
        secondary_y=True
    )
    fig.update_layout(title="Profit and Margin by Period")
    st.plotly_chart(fig, key="profit_margins")
    
    # Profit by product
    profit_by_product = filtered_df.groupby('Product Name').agg({
        'Amount': 'sum',
        'Direct_Profit': 'sum',
        'Net_Profit': 'sum'
    }).reset_index()
    
    fig = px.bar(
        profit_by_product,
        x='Product Name',
        y=['Direct_Profit', 'Net_Profit'],
        title='Profit by Product',
        barmode='group'
    )
    st.plotly_chart(fig, key="profit_by_product")

with tab8:
    st.header("Balance Analysis")
    
    # Balance trends
    ledger_df['Balance_Amount'] = ledger_df['Balance_Amount'].fillna(0)
    balance_trend = ledger_df[['Date', 'Balance_Amount']].copy()
    
    fig = px.line(
        balance_trend,
        x='Date',
        y='Balance_Amount',
        title='Balance Trends Over Time'
    )
    st.plotly_chart(fig, key="balance_trends")
    
    # Balance vs Interest
    # Convert Period to datetime for proper merging
    interest_by_period = filtered_df.groupby('Period').agg({
        'Interest_Cost': 'sum'
    }).reset_index()
    interest_by_period['Date'] = pd.to_datetime(interest_by_period['Period'] + '-01')
    
    balance_interest = pd.merge(
        ledger_df[['Date', 'Balance_Amount']],
        interest_by_period[['Date', 'Interest_Cost']],
        on='Date',
        how='left'
    )
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(x=balance_interest['Date'], y=balance_interest['Balance_Amount'],
                  name="Balance"),
        secondary_y=False
    )
    fig.add_trace(
        go.Bar(x=balance_interest['Date'], y=balance_interest['Interest_Cost'],
               name="Interest Cost"),
        secondary_y=True
    )
    fig.update_layout(title="Balance vs Interest Cost")
    st.plotly_chart(fig, key="balance_vs_interest")

# Download buttons
st.sidebar.subheader("Download Analysis")
csv = filtered_df.to_csv(index=False)
st.sidebar.download_button(
    label="Download Detailed Analysis CSV",
    data=csv,
    file_name="detailed_fuel_analysis.csv",
    mime="text/csv"
) 