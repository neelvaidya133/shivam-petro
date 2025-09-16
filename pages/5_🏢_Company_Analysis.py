import streamlit as st
import sys
import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Add parent directory to path to import from main files
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Page config
st.set_page_config(
    page_title="Shivam Petroleum - Company Analysis",
    page_icon="🏢",
    layout="wide"
)

@st.cache_data
def load_ledger_data():
    """Load ledger data from JSON file"""
    with open('ledger_data.json', 'r', encoding='utf-8') as f:
        return json.load(f)

@st.cache_data
def load_customer_data():
    """Load customer data from JSON file"""
    with open('customer_data.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def format_currency(amount):
    """Format amount in Indian currency format"""
    if amount >= 10000000:  # 1 crore
        return f"₹{amount/10000000:.2f} Cr"
    elif amount >= 100000:  # 1 lakh
        return f"₹{amount/100000:.2f} L"
    else:
        return f"₹{amount:,.0f}"

def calculate_profit(product_name, qty, amount, profit_margins):
    """Calculate profit based on product type and dynamic profit margins"""
    if product_name == "Diesel":
        return qty * profit_margins['diesel_per_liter']
    elif product_name == "Petrol":
        return qty * profit_margins['petrol_per_liter']
    elif product_name == "4T 20W-40 - 1Ltr":
        return amount * profit_margins['oil_percentage'] / 100
    else:
        # For other products - use the "others" margin
        return qty * profit_margins['others_per_liter']

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

def merge_customer_data(ledger_customers, sales_customers):
    """Merge ledger and sales data for comprehensive analysis"""
    merged_data = []
    
    # First, merge customers who have both ledger and sales data
    for ledger_customer in ledger_customers:
        # Find matching sales customer
        sales_customer = next(
            (sc for sc in sales_customers if sc['customer_name'] == ledger_customer['customer_name']), 
            None
        )
        
        if sales_customer:
            # Merge the data
            merged_customer = {
                'customer_id': ledger_customer['customer_id'],
                'customer_name': ledger_customer['customer_name'],
                'ledger_data': ledger_customer,
                'sales_data': sales_customer,
                'opening_balance': ledger_customer['opening_balance'],
                'closing_balance': ledger_customer['summary']['final_balance'],
                'total_transactions_ledger': ledger_customer['total_transactions'],
                'total_transactions_sales': sales_customer['total_transactions']
            }
            merged_data.append(merged_customer)
    
    # Then, add customers who have only sales data (no ledger data)
    ledger_names = {c['customer_name'] for c in ledger_customers}
    for sales_customer in sales_customers:
        if sales_customer['customer_name'] not in ledger_names:
            # Create a dummy ledger entry for sales-only customers
            dummy_ledger = {
                'customer_id': 'SALES_ONLY',
                'customer_name': sales_customer['customer_name'],
                'account_period': {'start_date': '2024-04-01', 'end_date': '2025-03-31'},
                'opening_balance': {'amount': 0.0, 'type': ''},
                'transactions': [],
                'total_transactions': 0,
                'summary': {'total_debits': 0.0, 'total_credits': 0.0, 'final_balance': 0.0, 'final_balance_type': ''}
            }
            
            merged_customer = {
                'customer_id': 'SALES_ONLY',
                'customer_name': sales_customer['customer_name'],
                'ledger_data': dummy_ledger,
                'sales_data': sales_customer,
                'opening_balance': {'amount': 0.0, 'type': ''},
                'closing_balance': 0.0,
                'total_transactions_ledger': 0,
                'total_transactions_sales': sales_customer['total_transactions']
            }
            merged_data.append(merged_customer)
    
    return merged_data

def calculate_customer_metrics(merged_customer, profit_margins, interest_rate, fy_start_date=None, fy_end_date=None):
    """Calculate comprehensive metrics for a single customer"""
    ledger_data = merged_customer['ledger_data']
    sales_data = merged_customer['sales_data']
    
    # Filter transactions by financial year if dates provided
    if fy_start_date and fy_end_date:
        # Filter sales transactions
        sales_transactions = []
        for transaction in sales_data['transactions']:
            trans_date = pd.to_datetime(transaction['date'], format='%d/%m/%Y')
            if fy_start_date <= trans_date <= fy_end_date:
                sales_transactions.append(transaction)
        
        # Filter ledger transactions
        ledger_transactions = []
        for transaction in ledger_data['transactions']:
            trans_date = pd.to_datetime(transaction['date'])
            if fy_start_date <= trans_date <= fy_end_date:
                ledger_transactions.append(transaction)
    else:
        sales_transactions = sales_data['transactions']
        ledger_transactions = ledger_data['transactions']
    
    # Calculate profit from filtered sales transactions
    total_profit = sum(
        calculate_profit(transaction['product_name'], transaction['qty'], transaction['amount'], profit_margins)
        for transaction in sales_transactions
    )
    
    # Calculate interest from filtered ledger transactions
    if ledger_transactions:
        daily_summary = group_transactions_by_date(ledger_transactions)
        daily_summary = calculate_daily_interest(daily_summary, interest_rate)
        total_interest = daily_summary['cumulative_interest'].iloc[-1] if not daily_summary.empty else 0
    else:
        daily_summary = pd.DataFrame()
        total_interest = 0
    
    # Calculate other metrics from filtered data
    total_quantity = sum(transaction['qty'] for transaction in sales_transactions)
    total_sales_amount = sum(transaction['amount'] for transaction in sales_transactions)
    opening_balance = ledger_data['opening_balance']['amount']
    closing_balance = ledger_data['summary']['final_balance']
    avg_outstanding = daily_summary['outstanding_balance'].mean() if not daily_summary.empty else 0
    high_outstanding = daily_summary['outstanding_balance'].max() if not daily_summary.empty else 0
    
    # Calculate payback period from filtered data
    if ledger_transactions:
        transactions_df = pd.DataFrame(ledger_transactions)
        transactions_df['date'] = pd.to_datetime(transactions_df['date'])
        
        debit_dates = transactions_df[transactions_df['debit'] > 0]['date']
        credit_dates = transactions_df[transactions_df['credit'] > 0]['date']
        
        payback_periods = []
        for debit_date in debit_dates:
            future_credits = credit_dates[credit_dates > debit_date]
            if not future_credits.empty:
                next_credit = future_credits.min()
                days_diff = (next_credit - debit_date).days
                payback_periods.append(days_diff)
        
        avg_payback_period = np.mean(payback_periods) if payback_periods else 0
        
        # Calculate repayments from filtered data
        total_repayments = sum(transaction['credit'] for transaction in ledger_transactions)
    else:
        avg_payback_period = 0
        total_repayments = 0
    
    return {
        'customer_name': merged_customer['customer_name'],
        'total_profit': total_profit,
        'total_interest': total_interest,
        'actual_profit': total_profit,
        'net_profit': total_profit - total_interest,
        'profit_interest_ratio': total_profit / total_interest if total_interest > 0 else 0,
        'total_quantity': total_quantity,
        'total_sales_amount': total_sales_amount,
        'opening_balance': opening_balance,
        'closing_balance': closing_balance,
        'avg_outstanding': avg_outstanding,
        'high_outstanding': high_outstanding,
        'avg_payback_period': avg_payback_period,
        'total_repayments': total_repayments,
        'total_transactions': merged_customer['total_transactions_ledger'] + merged_customer['total_transactions_sales']
    }

def calculate_company_metrics(all_customer_metrics):
    """Calculate company-wide aggregated metrics"""
    if not all_customer_metrics:
        return {}
    
    df = pd.DataFrame(all_customer_metrics)
    
    return {
        'total_profit': df['total_profit'].sum(),
        'total_interest': df['total_interest'].sum(),
        'actual_profit': df['actual_profit'].sum(),
        'net_profit': df['net_profit'].sum(),
        'profit_interest_ratio': df['total_profit'].sum() / df['total_interest'].sum() if df['total_interest'].sum() > 0 else 0,
        'total_quantity': df['total_quantity'].sum(),
        'total_sales_amount': df['total_sales_amount'].sum(),
        'avg_debt': df['closing_balance'].mean(),
        'avg_outstanding': df['avg_outstanding'].mean(),
        'highest_outstanding': df['high_outstanding'].max(),
        'avg_payback_period': df['avg_payback_period'].mean(),
        'avg_repayments': df['total_repayments'].mean(),
        'total_customers': len(df),
        'total_transactions': df['total_transactions'].sum()
    }

def create_company_charts(all_customer_metrics, company_metrics):
    """Create comprehensive charts for company analysis"""
    charts = {}
    
    df = pd.DataFrame(all_customer_metrics)
    
    # Filter out customers with zero profit to avoid misleading pie charts
    df_profit = df[df['total_profit'] > 0].copy()
    df_interest = df[df['total_interest'] > 0].copy()
    
    # 1. Customer Net Profit Contribution Pie Chart (based on net profit, not total profit)
    if not df_profit.empty:
        fig_profit_pie = px.pie(
            df_profit, 
            values='net_profit', 
            names='customer_name',
            title="Net Profit Contribution by Customer",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_profit_pie.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Net Profit: ₹%{value:,.0f}<br>Percentage: %{percent}<extra></extra>'
        )
        charts['profit_contribution'] = fig_profit_pie
    
    # 2. Customer Interest Burden Pie Chart
    if not df_interest.empty:
        fig_interest_pie = px.pie(
            df_interest, 
            values='total_interest', 
            names='customer_name',
            title="Interest Burden by Customer",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_interest_pie.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Interest: ₹%{value:,.0f}<br>Percentage: %{percent}<extra></extra>'
        )
        charts['interest_burden'] = fig_interest_pie
    
    # 3. Top 10 Customers by Net Profit
    top_customers = df.nlargest(10, 'net_profit')
    fig_top_profit = px.bar(
        top_customers,
        x='customer_name',
        y='net_profit',
        title="Top 10 Customers by Net Profit",
        color='net_profit',
        color_continuous_scale='Greens'
    )
    fig_top_profit.update_xaxes(tickangle=45)
    charts['top_customers_profit'] = fig_top_profit
    
    # 4. Top 10 Customers by Outstanding
    top_outstanding = df.nlargest(10, 'high_outstanding')
    fig_top_outstanding = px.bar(
        top_outstanding,
        x='customer_name',
        y='high_outstanding',
        title="Top 10 Customers by Highest Outstanding",
        color='high_outstanding',
        color_continuous_scale='Reds'
    )
    fig_top_outstanding.update_xaxes(tickangle=45)
    charts['top_customers_outstanding'] = fig_top_outstanding
    
    # 5. Profit vs Interest Scatter Plot
    fig_scatter = px.scatter(
        df,
        x='total_interest',
        y='total_profit',
        size='total_quantity',
        hover_name='customer_name',
        title="Profit vs Interest Analysis",
        labels={'total_interest': 'Total Interest (₹)', 'total_profit': 'Total Profit (₹)'}
    )
    charts['profit_vs_interest'] = fig_scatter
    
    # 6. Payback Period Analysis
    fig_payback = px.bar(
        df.nlargest(10, 'avg_payback_period'),
        x='customer_name',
        y='avg_payback_period',
        title="Top 10 Customers by Average Payback Period (Days)",
        color='avg_payback_period',
        color_continuous_scale='Oranges'
    )
    fig_payback.update_xaxes(tickangle=45)
    charts['payback_analysis'] = fig_payback
    
    # 7. Company Performance Overview
    performance_data = {
        'Metric': ['Total Profit', 'Total Interest', 'Net Profit', 'Total Sales', 'Avg Outstanding'],
        'Amount (₹)': [
            company_metrics['total_profit'],
            company_metrics['total_interest'],
            company_metrics['net_profit'],
            company_metrics['total_sales_amount'],
            company_metrics['avg_outstanding']
        ]
    }
    
    fig_performance = px.bar(
        performance_data,
        x='Metric',
        y='Amount (₹)',
        title="Company Performance Overview",
        color='Amount (₹)',
        color_continuous_scale='Blues'
    )
    charts['company_performance'] = fig_performance
    
    return charts

def main():
    st.title("🏢 Shivam Petroleum - Company Analysis Dashboard")
    st.markdown("---")
    
    # Load data
    ledger_customers = load_ledger_data()
    sales_customers = load_customer_data()
    
    # Merge data
    merged_customers = merge_customer_data(ledger_customers, sales_customers)
    
    # Sidebar
    st.sidebar.header("🔧 Analysis Settings")
    
    # Profit margin settings
    st.sidebar.subheader("💰 Profit Margins")
    profit_margins = {
        'diesel_per_liter': st.sidebar.number_input(
            "Diesel (₹ per liter):",
            min_value=0.0,
            max_value=50.0,
            value=3.0,
            step=0.1
        ),
        'petrol_per_liter': st.sidebar.number_input(
            "Petrol (₹ per liter):",
            min_value=0.0,
            max_value=50.0,
            value=2.0,
            step=0.1
        ),
        'oil_percentage': st.sidebar.number_input(
            "Oil (percentage):",
            min_value=0.0,
            max_value=100.0,
            value=15.0,
            step=0.1
        ),
        'others_per_liter': st.sidebar.number_input(
            "Others (₹ per liter):",
            min_value=0.0,
            max_value=50.0,
            value=1.0,
            step=0.1
        )
    }
    
    # Interest rate input
    interest_rate = st.sidebar.number_input(
        "Interest Rate (% per annum):",
        min_value=0.0,
        max_value=50.0,
        value=12.0,
        step=0.1
    )
    
    # Financial year filter
    st.sidebar.subheader("📅 Financial Year Filter")
    st.info("📅 **Current Data Period:** 01-04-2024 to 31-03-2025 (FY 2024-2025)")
    
    # Set the actual date range - only 2024-2025 is available
    fy_start_date = pd.to_datetime('2024-04-01')
    fy_end_date = pd.to_datetime('2025-03-31')
    fy_display = "2024-2025"
    
    # Calculate all customer metrics with financial year filtering
    all_customer_metrics = []
    missing_data_warnings = []
    
    for merged_customer in merged_customers:
        customer_metrics = calculate_customer_metrics(merged_customer, profit_margins, interest_rate, fy_start_date, fy_end_date)
        all_customer_metrics.append(customer_metrics)
        
        # Check for missing data warnings
        if merged_customer['customer_id'] == 'SALES_ONLY':
            missing_data_warnings.append(f"⚠️ {merged_customer['customer_name']}: No ledger data available (sales-only customer)")
        elif customer_metrics['total_profit'] == 0:
            missing_data_warnings.append(f"⚠️ {merged_customer['customer_name']}: No sales data available (ledger-only customer)")
    
    # Display warnings if any
    if missing_data_warnings:
        st.sidebar.subheader("⚠️ Data Availability Warnings")
        for warning in missing_data_warnings:
            st.sidebar.warning(warning)
    
    # Calculate company metrics
    company_metrics = calculate_company_metrics(all_customer_metrics)
    
    # Main content
    st.header(f"📊 Company Analysis - Financial Year {fy_display}")
    st.info(f"📅 **Analysis Period:** {fy_start_date.strftime('%d-%m-%Y')} to {fy_end_date.strftime('%d-%m-%Y')}")
    
    # Company Overview Metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Profit",
            format_currency(company_metrics['total_profit'])
        )
    
    with col2:
        st.metric(
            "Total Interest",
            format_currency(company_metrics['total_interest'])
        )
    
    with col3:
        st.metric(
            "Net Profit",
            format_currency(company_metrics['net_profit'])
        )
    
    with col4:
        st.metric(
            "Profit/Interest Ratio",
            f"{company_metrics['profit_interest_ratio']:.2f}"
        )
    
    with col5:
        st.metric(
            "Total Customers",
            company_metrics['total_customers']
        )
    
    # Second row of metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Product Sales",
            f"{company_metrics['total_quantity']:,.2f} L"
        )
    
    with col2:
        st.metric(
            "Avg Debt per Customer",
            format_currency(company_metrics['avg_debt'])
        )
    
    with col3:
        st.metric(
            "Avg Outstanding",
            format_currency(company_metrics['avg_outstanding'])
        )
    
    with col4:
        st.metric(
            "Highest Outstanding",
            format_currency(company_metrics['highest_outstanding'])
        )
    
    with col5:
        st.metric(
            "Avg Payback Period",
            f"{company_metrics['avg_payback_period']:.1f} days"
        )
    
    st.markdown("---")
    
    # Detailed Analysis Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Company Overview", 
        "🥧 Customer Contributions", 
        "🏆 Top & Worst Customers", 
        "📊 Detailed Analysis", 
        "📄 Export Data"
    ])
    
    with tab1:
        st.subheader("Company Performance Overview")
        
        # Performance summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"**Total Sales Revenue:** {format_currency(company_metrics['total_sales_amount'])}")
            st.info(f"**Total Transactions:** {company_metrics['total_transactions']:,}")
        
        with col2:
            st.success(f"**Actual Profit:** {format_currency(company_metrics['actual_profit'])}")
            st.success(f"**Net Profit Margin:** {(company_metrics['net_profit']/company_metrics['total_sales_amount']*100):.2f}%" if company_metrics['total_sales_amount'] > 0 else "**Net Profit Margin:** N/A")
        
        with col3:
            st.warning(f"**Interest Burden:** {format_currency(company_metrics['total_interest'])}")
            st.warning(f"**Interest as % of Sales:** {(company_metrics['total_interest']/company_metrics['total_sales_amount']*100):.2f}%" if company_metrics['total_sales_amount'] > 0 else "**Interest as % of Sales:** N/A")
        
        # Company performance chart
        charts = create_company_charts(all_customer_metrics, company_metrics)
        if 'company_performance' in charts:
            st.plotly_chart(charts['company_performance'], use_container_width=True)
    
    with tab2:
        st.subheader("Customer Contribution Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(charts['profit_contribution'], use_container_width=True)
        
        with col2:
            st.plotly_chart(charts['interest_burden'], use_container_width=True)
        
        # Customer contribution table
        st.subheader("Customer Contribution Details")
        df = pd.DataFrame(all_customer_metrics)
        
        # Calculate percentages based on net profit for profit contribution
        df['net_profit_contribution_pct'] = (df['net_profit'] / df['net_profit'].sum() * 100).round(2)
        df['interest_contribution_pct'] = (df['total_interest'] / df['total_interest'].sum() * 100).round(2)
        
        contribution_df = df[['customer_name', 'total_profit', 'net_profit', 'net_profit_contribution_pct', 'total_interest', 'interest_contribution_pct']].copy()
        contribution_df.columns = ['Customer', 'Total Profit (₹)', 'Net Profit (₹)', 'Net Profit %', 'Total Interest (₹)', 'Interest %']
        contribution_df = contribution_df.sort_values('Net Profit (₹)', ascending=False)
        
        # Add data availability status
        contribution_df['Data Status'] = contribution_df.apply(lambda row: 
            'Complete' if row['Total Profit (₹)'] > 0 and row['Total Interest (₹)'] > 0
            else 'Sales Only' if row['Total Profit (₹)'] > 0 and row['Total Interest (₹)'] == 0
            else 'Ledger Only' if row['Total Profit (₹)'] == 0 and row['Total Interest (₹)'] > 0
            else 'No Data', axis=1
        )
        
        st.dataframe(contribution_df, use_container_width=True)
        
        # Show summary statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Total Net Profit:** ₹{df['net_profit'].sum():,.2f}")
        with col2:
            st.info(f"**Customers with Complete Data:** {len(df[(df['total_profit'] > 0) & (df['total_interest'] > 0)])}")
        with col3:
            st.info(f"**Sales-Only Customers:** {len(df[(df['total_profit'] > 0) & (df['total_interest'] == 0)])}")
    
    with tab3:
        st.subheader("Top & Worst Customers Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(charts['top_customers_profit'], use_container_width=True)
        
        with col2:
            st.plotly_chart(charts['top_customers_outstanding'], use_container_width=True)
        
        # Top and worst customers tables
        df = pd.DataFrame(all_customer_metrics)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**🏆 Top 5 Customers by Net Profit:**")
            top_profit = df.nlargest(5, 'net_profit')[['customer_name', 'total_profit', 'net_profit', 'profit_interest_ratio']].copy()
            top_profit.columns = ['Customer', 'Total Profit (₹)', 'Net Profit (₹)', 'P/I Ratio']
            st.dataframe(top_profit, use_container_width=True)
        
        with col2:
            st.write("**⚠️ Top 5 Customers by Outstanding:**")
            top_outstanding = df.nlargest(5, 'high_outstanding')[['customer_name', 'high_outstanding', 'avg_outstanding', 'avg_payback_period']].copy()
            top_outstanding.columns = ['Customer', 'Highest Outstanding (₹)', 'Avg Outstanding (₹)', 'Avg Payback (Days)']
            st.dataframe(top_outstanding, use_container_width=True)
        
        # Worst customers (lowest profit, highest interest burden)
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📉 Lowest 5 Customers by Net Profit:**")
            worst_profit = df.nsmallest(5, 'net_profit')[['customer_name', 'total_profit', 'net_profit', 'profit_interest_ratio']].copy()
            worst_profit.columns = ['Customer', 'Total Profit (₹)', 'Net Profit (₹)', 'P/I Ratio']
            st.dataframe(worst_profit, use_container_width=True)
        
        with col2:
            st.write("**⏰ Longest Payback Periods:**")
            longest_payback = df.nlargest(5, 'avg_payback_period')[['customer_name', 'avg_payback_period', 'high_outstanding', 'total_interest']].copy()
            longest_payback.columns = ['Customer', 'Avg Payback (Days)', 'Highest Outstanding (₹)', 'Total Interest (₹)']
            st.dataframe(longest_payback, use_container_width=True)
    
    with tab4:
        st.subheader("Detailed Analysis")
        
        # Profit vs Interest scatter plot
        st.plotly_chart(charts['profit_vs_interest'], use_container_width=True)
        
        # Payback period analysis
        st.plotly_chart(charts['payback_analysis'], use_container_width=True)
        
        # All customers detailed table
        st.subheader("All Customers Detailed Metrics")
        df = pd.DataFrame(all_customer_metrics)
        df = df.sort_values('total_profit', ascending=False)
        
        # Format the dataframe for display
        display_df = df.copy()
        for col in ['total_profit', 'total_interest', 'actual_profit', 'net_profit', 'total_sales_amount', 'opening_balance', 'closing_balance', 'avg_outstanding', 'high_outstanding', 'total_repayments']:
            display_df[col] = display_df[col].apply(lambda x: format_currency(x))
        
        display_df['avg_payback_period'] = display_df['avg_payback_period'].apply(lambda x: f"{x:.1f} days")
        display_df['profit_interest_ratio'] = display_df['profit_interest_ratio'].apply(lambda x: f"{x:.2f}")
        
        st.dataframe(display_df, use_container_width=True, height=400)
    
    with tab5:
        st.subheader("Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Export company metrics
            company_data = {
                'Financial Year': fy_display,
                'Total Profit (₹)': company_metrics['total_profit'],
                'Total Interest (₹)': company_metrics['total_interest'],
                'Actual Profit (₹)': company_metrics['actual_profit'],
                'Net Profit (₹)': company_metrics['net_profit'],
                'Profit Interest Ratio': company_metrics['profit_interest_ratio'],
                'Total Product Sales (L)': company_metrics['total_quantity'],
                'Total Sales Amount (₹)': company_metrics['total_sales_amount'],
                'Average Debt (₹)': company_metrics['avg_debt'],
                'Average Outstanding (₹)': company_metrics['avg_outstanding'],
                'Highest Outstanding (₹)': company_metrics['highest_outstanding'],
                'Average Payback Period (days)': company_metrics['avg_payback_period'],
                'Average Repayments (₹)': company_metrics['avg_repayments'],
                'Total Customers': company_metrics['total_customers'],
                'Total Transactions': company_metrics['total_transactions']
            }
            
            company_df = pd.DataFrame([company_data])
            csv_data = company_df.to_csv(index=False)
            
            st.download_button(
                label="🏢 Download Company Metrics (CSV)",
                data=csv_data,
                file_name=f"Company_Analysis_{fy_display.replace('-', '_')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Export all customers data
            customers_df = pd.DataFrame(all_customer_metrics)
            customers_csv = customers_df.to_csv(index=False)
            
            st.download_button(
                label="👥 Download All Customers Data (CSV)",
                data=customers_csv,
                file_name=f"All_Customers_Analysis_{fy_display.replace('-', '_')}.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()
