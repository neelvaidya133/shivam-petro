import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Page config
st.set_page_config(
    page_title="Shivam Petroleum - Interest Calculator Dashboard",
    page_icon="💰",
    layout="wide"
)

@st.cache_data
def load_ledger_data():
    """Load ledger data from JSON file"""
    with open('ledger_data.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def format_currency(amount):
    """Format amount in Indian currency format"""
    if amount >= 10000000:  # 1 crore
        return f"₹{amount/10000000:.2f} Cr"
    elif amount >= 100000:  # 1 lakh
        return f"₹{amount/100000:.2f} L"
    else:
        return f"₹{amount:,.0f}"

def group_transactions_by_date(transactions):
    """Group transactions by date and calculate daily net amounts"""
    df = pd.DataFrame(transactions)
    df['date'] = pd.to_datetime(df['date'])
    
    # Group by date and sum debits and credits
    daily_summary = df.groupby('date').agg({
        'debit': 'sum',
        'credit': 'sum',
        'balance': 'last'  # Take the last balance for each date
    }).reset_index()
    
    # Calculate net amount for each day
    daily_summary['net_amount'] = daily_summary['debit'] - daily_summary['credit']
    daily_summary['balance_type'] = daily_summary['balance'].apply(
        lambda x: 'Dr' if x > 0 else 'Cr' if x < 0 else ''
    )
    
    return daily_summary

def calculate_interest_on_balance(balance, days, interest_rate):
    """Calculate interest on outstanding balance"""
    if balance <= 0:
        return 0
    
    # Simple interest calculation: P * R * T / 100
    # where P = Principal (balance), R = Rate per annum, T = Time in years
    time_in_years = days / 365
    interest = (balance * interest_rate * time_in_years) / 100
    return interest

def calculate_daily_interest(daily_summary, interest_rate):
    """Calculate compound interest with FIFO payment logic for EVERY SINGLE DAY"""
    daily_summary = daily_summary.copy()
    
    # Daily interest rate (compound)
    daily_rate = interest_rate / 365 / 100
    
    # Get date range
    start_date = daily_summary['date'].min()
    end_date = daily_summary['date'].max()
    
    # Create complete daily range (no gaps)
    all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Create new dataframe with all days
    complete_df = pd.DataFrame({'date': all_dates})
    complete_df = complete_df.merge(daily_summary, on='date', how='left')
    complete_df = complete_df.fillna(0)  # Fill missing values with 0
    
    # Initialize columns
    complete_df['interest'] = 0.0
    complete_df['cumulative_interest'] = 0.0
    complete_df['outstanding_balance'] = 0.0
    complete_df['payments_applied'] = 0.0
    complete_df['new_debt'] = 0.0
    
    # Track running balance with compound interest
    # Start with opening balance if available
    opening_balance = daily_summary.iloc[0]['balance'] if not daily_summary.empty else 0.0
    running_balance = opening_balance
    cumulative_interest = 0.0
    
    for i, row in complete_df.iterrows():
        # Step 1: Apply payments at beginning of day (FIFO)
        payments_today = row['credit']  # Credits are payments
        new_debt_today = row['debit']   # Debits are new debt
        
        # Apply payments to reduce outstanding balance
        if payments_today > 0 and running_balance > 0:
            if payments_today >= running_balance:
                # Full payment - clear all outstanding
                payments_applied = running_balance
                running_balance = 0.0
            else:
                # Partial payment - reduce outstanding
                payments_applied = payments_today
                running_balance -= payments_today
        else:
            payments_applied = 0.0
        
        # Step 2: Calculate compound interest on remaining balance (EVERY DAY)
        if running_balance > 0:
            daily_interest = running_balance * daily_rate
            running_balance += daily_interest  # Compound interest
            cumulative_interest += daily_interest
        else:
            daily_interest = 0.0
        
        # Step 3: Add new debt at end of day
        if new_debt_today > 0:
            running_balance += new_debt_today
        
        # Store results
        complete_df.at[i, 'outstanding_balance'] = running_balance
        complete_df.at[i, 'payments_applied'] = payments_applied
        complete_df.at[i, 'new_debt'] = new_debt_today
        complete_df.at[i, 'interest'] = daily_interest
        complete_df.at[i, 'cumulative_interest'] = cumulative_interest
    
    return complete_df

def create_balance_interest_chart(daily_summary):
    """Create chart showing balance and interest over time"""
    from plotly.subplots import make_subplots
    
    # Create subplot with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add balance line
    fig.add_trace(go.Scatter(
        x=daily_summary['date'],
        y=daily_summary['outstanding_balance'],
        mode='lines+markers',
        name='Outstanding Balance (with Interest)',
        line=dict(color='#1f77b4', width=2)
    ), secondary_y=False)
    
    # Add cumulative interest line
    fig.add_trace(go.Scatter(
        x=daily_summary['date'],
        y=daily_summary['cumulative_interest'],
        mode='lines+markers',
        name='Cumulative Interest',
        line=dict(color='#ff7f0e', width=2)
    ), secondary_y=True)
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    # Update layout
    fig.update_layout(
        title="Outstanding Balance & Interest Over Time",
        xaxis_title="Date",
        hovermode='x unified',
        height=500
    )
    
    # Set y-axes titles
    fig.update_yaxes(title_text="Balance (₹)", secondary_y=False)
    fig.update_yaxes(title_text="Cumulative Interest (₹)", secondary_y=True)
    
    # Format y-axes as currency
    fig.update_yaxes(tickformat='₹,.0f', secondary_y=False)
    fig.update_yaxes(tickformat='₹,.0f', secondary_y=True)
    
    return fig

def create_daily_activity_chart(daily_summary):
    """Create chart showing daily transaction activity"""
    fig = go.Figure()
    
    # Add net amount bars
    colors = ['red' if x > 0 else 'green' if x < 0 else 'gray' for x in daily_summary['net_amount']]
    
    fig.add_trace(go.Bar(
        x=daily_summary['date'],
        y=daily_summary['net_amount'],
        name='Net Amount',
        marker_color=colors,
        text=[f"₹{x:,.0f}" for x in daily_summary['net_amount']],
        textposition='auto'
    ))
    
    fig.update_layout(
        title="Daily Net Transaction Amounts",
        xaxis_title="Date",
        yaxis_title="Net Amount (₹)",
        height=400
    )
    
    fig.update_yaxes(tickformat='₹,.0f')
    
    return fig

def main():
    st.title("💰 Shivam Petroleum - Interest Calculator Dashboard")
    st.markdown("---")
    
    # Load data
    customers = load_ledger_data()
    
    # Sidebar
    st.sidebar.header("🔧 Calculator Settings")
    
    # Customer selection
    customer_options = [f"{c['customer_id']} - {c['customer_name']}" for c in customers]
    selected_customer_idx = st.sidebar.selectbox(
        "Select Customer:",
        range(len(customer_options)),
        format_func=lambda x: customer_options[x]
    )
    
    selected_customer = customers[selected_customer_idx]
    
    # Interest rate input
    interest_rate = st.sidebar.number_input(
        "Interest Rate (% per annum):",
        min_value=0.0,
        max_value=50.0,
        value=12.0,
        step=0.1,
        help="Enter the annual interest rate for calculating interest on outstanding balances"
    )
    
    # Date range filter
    st.sidebar.subheader("📅 Date Range Filter")
    
    # Get date range from data
    transactions_df = pd.DataFrame(selected_customer['transactions'])
    transactions_df['date'] = pd.to_datetime(transactions_df['date'])
    min_date = transactions_df['date'].min().date()
    max_date = transactions_df['date'].max().date()
    
    date_range = st.sidebar.date_input(
        "Select Date Range:",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Display filter
    st.sidebar.subheader("🔍 Display Options")
    show_all_days = st.sidebar.checkbox(
        "Show All Days (including non-transaction days)",
        value=False,
        help="Check to see interest calculated for every single day, not just transaction days"
    )
    
    # Main content
    st.header(f"📊 Interest Analysis - {selected_customer['customer_name']}")
    
    # Customer summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Transactions", selected_customer['total_transactions'])
    
    with col2:
        final_balance = selected_customer['summary']['final_balance']
        st.metric("Current Balance", f"{format_currency(final_balance)}")
    
    with col3:
        st.metric("Interest Rate", f"{interest_rate}% p.a.")
    
    with col4:
        # Calculate total interest
        daily_summary = group_transactions_by_date(selected_customer['transactions'])
        daily_summary = calculate_daily_interest(daily_summary, interest_rate)
        total_interest = daily_summary['cumulative_interest'].iloc[-1]
        st.metric("Total Interest", f"{format_currency(total_interest)}")
    
    # Filter data by date range
    if len(date_range) == 2:
        start_date, end_date = date_range
        daily_summary = daily_summary[
            (daily_summary['date'].dt.date >= start_date) & 
            (daily_summary['date'].dt.date <= end_date)
        ]
    
    # Filter by display option
    if not show_all_days:
        # Show only days with transactions (debit or credit > 0)
        daily_summary = daily_summary[
            (daily_summary['debit'] > 0) | (daily_summary['credit'] > 0)
        ]
    
    # Grouped transactions by date
    st.subheader("📅 Daily Transaction Summary")
    
    # Display daily summary table
    display_df = daily_summary.copy()
    display_df['date_str'] = display_df['date'].dt.strftime('%Y-%m-%d')
    display_df['debit_formatted'] = display_df['debit'].apply(lambda x: f"₹{x:,.0f}" if x > 0 else "")
    display_df['credit_formatted'] = display_df['credit'].apply(lambda x: f"₹{x:,.0f}" if x > 0 else "")
    display_df['net_amount_formatted'] = display_df['net_amount'].apply(lambda x: f"₹{x:,.0f}")
    display_df['outstanding_balance_formatted'] = display_df['outstanding_balance'].apply(lambda x: f"₹{x:,.0f}")
    display_df['payments_applied_formatted'] = display_df['payments_applied'].apply(lambda x: f"₹{x:,.0f}" if x > 0 else "")
    display_df['new_debt_formatted'] = display_df['new_debt'].apply(lambda x: f"₹{x:,.0f}" if x > 0 else "")
    display_df['interest_formatted'] = display_df['interest'].apply(lambda x: f"₹{x:,.0f}")
    display_df['cumulative_interest_formatted'] = display_df['cumulative_interest'].apply(lambda x: f"₹{x:,.0f}")
    
    table_df = display_df[[
        'date_str', 'debit_formatted', 'credit_formatted', 'net_amount_formatted', 
        'outstanding_balance_formatted', 'payments_applied_formatted', 'new_debt_formatted',
        'interest_formatted', 'cumulative_interest_formatted'
    ]].copy()
    
    table_df.columns = [
        'Date', 'New Debt', 'Payments', 'Net Amount', 
        'Outstanding Balance', 'Payments Applied', 'New Debt Added',
        'Daily Interest', 'Cumulative Interest'
    ]
    
    st.dataframe(table_df, width='stretch', height=400)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Balance & Interest Trend")
        balance_chart = create_balance_interest_chart(daily_summary)
        st.plotly_chart(balance_chart, width='stretch')
    
    with col2:
        st.subheader("📊 Daily Transaction Activity")
        activity_chart = create_daily_activity_chart(daily_summary)
        st.plotly_chart(activity_chart, width='stretch')
    
    # Interest calculation summary
    st.subheader("💰 Interest Calculation Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_days = len(daily_summary)
        st.info(f"**Analysis Period:** {total_days} days")
    
    with col2:
        avg_balance = daily_summary['outstanding_balance'].mean()
        st.info(f"**Average Outstanding Balance:** {format_currency(avg_balance)}")
    
    with col3:
        max_balance = daily_summary['outstanding_balance'].max()
        st.info(f"**Peak Outstanding Balance:** {format_currency(max_balance)}")
    
    # Interest breakdown
    st.subheader("📋 Interest Breakdown")
    
    # Calculate old vs new interest
    old_calculation = group_transactions_by_date(selected_customer['transactions'])
    old_interest = old_calculation['balance'].sum() * (interest_rate / 365 / 100) * len(old_calculation)
    new_interest = daily_summary['cumulative_interest'].iloc[-1] if not daily_summary.empty else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"**Old Calculation (Wrong):** {format_currency(old_interest)}")
    
    with col2:
        st.success(f"**New Calculation (Correct):** {format_currency(new_interest)}")
    
    with col3:
        difference = new_interest - old_interest
        st.warning(f"**Difference:** {format_currency(difference)}")
    
    interest_summary = daily_summary[daily_summary['interest'] > 0].copy()
    
    if not interest_summary.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Days with Interest Calculation:**")
            # Show only first 10 days to avoid overwhelming display
            display_days = interest_summary.head(10)
            for _, row in display_days.iterrows():
                st.write(f"• {row['date'].strftime('%Y-%m-%d')}: Balance ₹{row['outstanding_balance']:,.0f} → Interest ₹{row['interest']:,.0f}")
            if len(interest_summary) > 10:
                st.write(f"... and {len(interest_summary) - 10} more days")
        
        with col2:
            st.write("**Interest Statistics:**")
            st.write(f"• Total Interest: {format_currency(daily_summary['cumulative_interest'].iloc[-1])}")
            st.write(f"• Average Daily Interest: {format_currency(daily_summary['interest'].mean())}")
            st.write(f"• Maximum Daily Interest: {format_currency(daily_summary['interest'].max())}")
            st.write(f"• Total Days with Interest: {len(interest_summary)}")
    else:
        st.info("No interest calculated for the selected period (no outstanding balances)")
    
    # Export options
    st.subheader("📥 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export daily summary
        csv_data = daily_summary.to_csv(index=False)
        st.download_button(
            label="📊 Download Daily Summary (CSV)",
            data=csv_data,
            file_name=f"{selected_customer['customer_name']}_daily_summary.csv",
            mime="text/csv"
        )
    
    with col2:
        # Export interest calculation
        interest_data = daily_summary[['date', 'balance', 'interest', 'cumulative_interest']].to_csv(index=False)
        st.download_button(
            label="💰 Download Interest Calculation (CSV)",
            data=interest_data,
            file_name=f"{selected_customer['customer_name']}_interest_calculation.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
