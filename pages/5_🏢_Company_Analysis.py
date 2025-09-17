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

def calculate_payment_time_analysis(ledger_data):
    """Calculate detailed payment time analysis using FIFO logic"""
    transactions_df = pd.DataFrame(ledger_data['transactions'])
    transactions_df['date'] = pd.to_datetime(transactions_df['date'])
    
    # Sort by date to ensure chronological order
    transactions_df = transactions_df.sort_values('date').reset_index(drop=True)
    
    # Track individual debts and their payment status
    debt_queue = []  # FIFO queue of outstanding debts
    payment_analysis = []  # Store payment time analysis
    
    # Process opening balance as first debt if it exists
    opening_balance = ledger_data['opening_balance']['amount']
    if opening_balance > 0:
        debt_queue.append({
            'debt_id': 'opening_balance',
            'amount': opening_balance,
            'date_created': transactions_df['date'].iloc[0],
            'amount_paid': 0,
            'amount_remaining': opening_balance,
            'payment_dates': [],
            'days_to_pay': None
        })
    
    # Process each transaction
    for idx, row in transactions_df.iterrows():
        current_date = row['date']
        debit_amount = row['debit']
        credit_amount = row['credit']
        
        # Add new debt if there's a debit
        if debit_amount > 0:
            debt_queue.append({
                'debt_id': f'debt_{idx}',
                'amount': debit_amount,
                'date_created': current_date,
                'amount_paid': 0,
                'amount_remaining': debit_amount,
                'payment_dates': [],
                'days_to_pay': None
            })
        
        # Process payment if there's a credit
        if credit_amount > 0:
            remaining_payment = credit_amount
            
            # Apply payment using FIFO (First In, First Out)
            while remaining_payment > 0 and debt_queue:
                current_debt = debt_queue[0]
                
                if current_debt['amount_remaining'] <= remaining_payment:
                    # This debt is fully paid
                    payment_amount = current_debt['amount_remaining']
                    current_debt['amount_paid'] += payment_amount
                    current_debt['amount_remaining'] = 0
                    current_debt['payment_dates'].append(current_date)
                    current_debt['days_to_pay'] = (current_date - current_debt['date_created']).days
                    
                    # Move to completed analysis
                    payment_analysis.append(current_debt.copy())
                    
                    # Remove from queue
                    debt_queue.pop(0)
                    remaining_payment -= payment_amount
                    
                else:
                    # Partial payment on this debt
                    current_debt['amount_paid'] += remaining_payment
                    current_debt['amount_remaining'] -= remaining_payment
                    current_debt['payment_dates'].append(current_date)
                    remaining_payment = 0
    
    # Add any remaining unpaid debts
    for debt in debt_queue:
        payment_analysis.append(debt)
    
    return payment_analysis

def calculate_customer_metrics(merged_customer, profit_margins, interest_rate, fy_start_date=None, fy_end_date=None):
    """Calculate comprehensive metrics for a single customer with business intelligence"""
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
    
    # NEW: Business Intelligence Metrics
    # 1. PE Ratio (Profit Efficiency Ratio)
    pe_ratio = (total_interest / total_profit * 100) if total_profit > 0 else 0
    
    # 2. Payment Time Analysis
    payment_analysis = calculate_payment_time_analysis(ledger_data) if ledger_transactions else []
    paid_debts = [debt for debt in payment_analysis if debt['days_to_pay'] is not None]
    unpaid_debts = [debt for debt in payment_analysis if debt['days_to_pay'] is None]
    
    avg_payment_time = np.mean([debt['days_to_pay'] for debt in paid_debts]) if paid_debts else 0
    max_payment_time = max([debt['days_to_pay'] for debt in paid_debts]) if paid_debts else 0
    min_payment_time = min([debt['days_to_pay'] for debt in paid_debts]) if paid_debts else 0
    
    # 3. Customer Risk Score (0-100, lower is better)
    avg_payment_time_score = min(100, max(0, 100 - (avg_payment_time / 30 * 100)))  # Penalty for longer payment times
    outstanding_ratio = (closing_balance / total_profit * 100) if total_profit > 0 else 0
    outstanding_score = min(100, max(0, 100 - outstanding_ratio))  # Penalty for high outstanding
    payment_rate_score = (len(paid_debts) / len(payment_analysis) * 100) if payment_analysis else 0
    
    risk_score = (avg_payment_time_score * 0.4 + outstanding_score * 0.4 + payment_rate_score * 0.2)
    
    # 4. Investment Efficiency Ratio
    investment_efficiency = (closing_balance / total_profit * 100) if total_profit > 0 else 0
    
    # 5. Customer Profitability Score (0-100, higher is better)
    profit_score = min(100, (total_profit / 100000 * 100))  # Normalize profit (₹1L = 100 points)
    payment_behavior_score = min(100, max(0, 100 - (avg_payment_time / 30 * 50)))  # Payment time impact
    profitability_score = (profit_score * 0.5 + payment_behavior_score * 0.3 + (100 - risk_score) * 0.2)
    
    # 6. Return on Investment (ROI) for this customer
    total_investment = opening_balance + sum([debt['amount'] for debt in payment_analysis if debt['debt_id'] != 'opening_balance'])
    roi = ((total_profit - total_interest) / total_investment * 100) if total_investment > 0 else 0
    
    # 7. Customer Business Value Rating
    if profitability_score >= 80 and risk_score <= 30:
        business_rating = "Excellent"
        rating_color = "green"
    elif profitability_score >= 60 and risk_score <= 50:
        business_rating = "Good"
        rating_color = "blue"
    elif profitability_score >= 40 and risk_score <= 70:
        business_rating = "Average"
        rating_color = "orange"
    else:
        business_rating = "Poor"
        rating_color = "red"
    
    return {
        'customer_name': merged_customer['customer_name'],
        'total_profit': total_profit,
        'total_interest': total_interest,
        'actual_profit': total_profit,
        'net_profit': total_profit - total_interest,
        'profit_interest_ratio': total_profit / total_interest if total_interest > 0 else 0,
        'pe_ratio': pe_ratio,  # NEW
        'risk_score': risk_score,  # NEW
        'investment_efficiency': investment_efficiency,  # NEW
        'profitability_score': profitability_score,  # NEW
        'roi': roi,  # NEW
        'business_rating': business_rating,  # NEW
        'rating_color': rating_color,  # NEW
        'total_quantity': total_quantity,
        'total_sales_amount': total_sales_amount,
        'opening_balance': opening_balance,
        'closing_balance': closing_balance,
        'avg_outstanding': avg_outstanding,
        'high_outstanding': high_outstanding,
        'avg_payback_period': avg_payback_period,
        'avg_payment_time': avg_payment_time,  # NEW
        'max_payment_time': max_payment_time,  # NEW
        'min_payment_time': min_payment_time,  # NEW
        'total_repayments': total_repayments,
        'total_transactions': merged_customer['total_transactions_ledger'] + merged_customer['total_transactions_sales'],
        'paid_debts_count': len(paid_debts),  # NEW
        'unpaid_debts_count': len(unpaid_debts),  # NEW
        'payment_rate': (len(paid_debts) / len(payment_analysis) * 100) if payment_analysis else 0  # NEW
    }

def calculate_company_metrics(all_customer_metrics):
    """Calculate company-wide aggregated metrics with business intelligence"""
    if not all_customer_metrics:
        return {}
    
    df = pd.DataFrame(all_customer_metrics)
    
    # Basic metrics
    total_profit = df['total_profit'].sum()
    total_interest = df['total_interest'].sum()
    total_sales_amount = df['total_sales_amount'].sum()
    
    # NEW: Business Intelligence Company Metrics
    # 1. Company PE Ratio
    company_pe_ratio = (total_interest / total_profit * 100) if total_profit > 0 else 0
    
    # 2. Average Risk Score
    avg_risk_score = df['risk_score'].mean()
    
    # 3. Average Investment Efficiency
    avg_investment_efficiency = df['investment_efficiency'].mean()
    
    # 4. Average Profitability Score
    avg_profitability_score = df['profitability_score'].mean()
    
    # 5. Average ROI
    avg_roi = df['roi'].mean()
    
    # 6. Customer Segmentation
    excellent_customers = len(df[df['business_rating'] == 'Excellent'])
    good_customers = len(df[df['business_rating'] == 'Good'])
    average_customers = len(df[df['business_rating'] == 'Average'])
    poor_customers = len(df[df['business_rating'] == 'Poor'])
    
    # 7. Risk Distribution
    low_risk_customers = len(df[df['risk_score'] <= 30])
    medium_risk_customers = len(df[(df['risk_score'] > 30) & (df['risk_score'] <= 70)])
    high_risk_customers = len(df[df['risk_score'] > 70])
    
    # 8. Payment Performance
    avg_payment_time = df['avg_payment_time'].mean()
    avg_payment_rate = df['payment_rate'].mean()
    
    # 9. Investment Analysis
    total_investment = df['closing_balance'].sum()
    investment_efficiency_ratio = (total_investment / total_profit * 100) if total_profit > 0 else 0
    
    return {
        'total_profit': total_profit,
        'total_interest': total_interest,
        'actual_profit': df['actual_profit'].sum(),
        'net_profit': df['net_profit'].sum(),
        'profit_interest_ratio': total_profit / total_interest if total_interest > 0 else 0,
        'company_pe_ratio': company_pe_ratio,  # NEW
        'avg_risk_score': avg_risk_score,  # NEW
        'avg_investment_efficiency': avg_investment_efficiency,  # NEW
        'avg_profitability_score': avg_profitability_score,  # NEW
        'avg_roi': avg_roi,  # NEW
        'excellent_customers': excellent_customers,  # NEW
        'good_customers': good_customers,  # NEW
        'average_customers': average_customers,  # NEW
        'poor_customers': poor_customers,  # NEW
        'low_risk_customers': low_risk_customers,  # NEW
        'medium_risk_customers': medium_risk_customers,  # NEW
        'high_risk_customers': high_risk_customers,  # NEW
        'avg_payment_time': avg_payment_time,  # NEW
        'avg_payment_rate': avg_payment_rate,  # NEW
        'total_investment': total_investment,  # NEW
        'investment_efficiency_ratio': investment_efficiency_ratio,  # NEW
        'total_quantity': df['total_quantity'].sum(),
        'total_sales_amount': total_sales_amount,
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
            "Company PE Ratio",
            f"{company_metrics['company_pe_ratio']:.1f}%",
            help="Company-wide Profit Efficiency Ratio. Shows what percentage of your total profit goes to interest charges. Lower is better."
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
            format_currency(company_metrics['avg_debt']),
            help="Average amount of money each customer owes you (closing balance). This is your total investment in customers."
        )
    
    with col3:
        st.metric(
            "Avg Outstanding",
            format_currency(company_metrics['avg_outstanding']),
            help="Average outstanding balance across all customers over time. Shows how much money is typically tied up."
        )
    
    with col4:
        st.metric(
            "Highest Outstanding",
            format_currency(company_metrics['highest_outstanding']),
            help="The highest outstanding amount any single customer has had. Shows your maximum exposure to one customer."
        )
    
    with col5:
        st.metric(
            "Avg Payback Period",
            f"{company_metrics['avg_payback_period']:.1f} days",
            help="Average number of days it takes customers to pay back their debts. Lower is better for cash flow."
        )
    
    # Business Intelligence Metrics Row
    st.markdown("### 🎯 Company Business Intelligence Overview")
    col1, col2, col3, col4, col5 = st.columns([1.2, 1.2, 1.5, 1, 1.1])
    
    with col1:
        st.metric(
            "Avg Risk Score",
            f"{company_metrics['avg_risk_score']:.0f}/100",
            delta=f"{'Low Risk' if company_metrics['avg_risk_score'] <= 30 else 'High Risk' if company_metrics['avg_risk_score'] >= 70 else 'Medium Risk'}",
            help="Average risk score across all customers (0-100, lower is better). Based on payment time, outstanding amount, and payment rate."
        )
    
    with col2:
        st.metric(
            "Avg Profitability",
            f"{company_metrics['avg_profitability_score']:.0f}/100",
            help="Average profitability score across all customers (0-100, higher is better). Based on total profit, payment behavior, and risk level."
        )
    
    with col3:
        st.metric(
            "Investment Efficiency",
            f"₹{company_metrics['avg_investment_efficiency']:.0f}",
            help="Average amount of money you need to invest (outstanding balance) to make ₹100 profit. Lower is better."
        )
    
    with col4:
        st.metric(
            "Avg ROI",
            f"{company_metrics['avg_roi']:.1f}%",
            help="Average Return on Investment across all customers. Shows how much profit you get back for every ₹100 invested."
        )
    
    with col5:
        st.metric(
            "Payment Rate",
            f"{company_metrics['avg_payment_rate']:.1f}%",
            help="Average percentage of debts that customers have paid off. Higher percentage means better payment behavior."
        )
    
    st.markdown("---")
    
    # Detailed Analysis Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Company Overview", 
        "🥧 Customer Contributions", 
        "🏆 Top & Worst Customers", 
        "🎯 Business Intelligence",
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
        st.subheader("🎯 Business Intelligence & Customer Segmentation")
        
        # Customer Segmentation Overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "🟢 Excellent Customers",
                company_metrics['excellent_customers'],
                help="Customers with high profitability (≥80/100) and low risk (≤30/100). These are your best customers - consider increasing their credit limits."
            )
        
        with col2:
            st.metric(
                "🔵 Good Customers", 
                company_metrics['good_customers'],
                help="Customers with good profitability (≥60/100) and manageable risk (≤50/100). These are solid customers with good potential."
            )
        
        with col3:
            st.metric(
                "🟠 Average Customers",
                company_metrics['average_customers'],
                help="Customers with average profitability (≥40/100) and moderate risk (≤70/100). These customers need monitoring and may need attention."
            )
        
        with col4:
            st.metric(
                "🔴 Poor Customers",
                company_metrics['poor_customers'],
                help="Customers with low profitability (<40/100) or high risk (>70/100). Consider reducing their credit limits or improving payment terms."
            )
        
        # Risk Distribution
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Risk Distribution")
            risk_data = {
                'Risk Level': ['Low Risk', 'Medium Risk', 'High Risk'],
                'Count': [
                    company_metrics['low_risk_customers'],
                    company_metrics['medium_risk_customers'], 
                    company_metrics['high_risk_customers']
                ],
                'Color': ['#2E8B57', '#FFA500', '#DC143C']
            }
            
            fig_risk = px.bar(
                risk_data,
                x='Risk Level',
                y='Count',
                color='Risk Level',
                color_discrete_sequence=['#2E8B57', '#FFA500', '#DC143C'],
                title="Customer Risk Distribution"
            )
            st.plotly_chart(fig_risk, use_container_width=True)
        
        with col2:
            st.subheader("Business Rating Distribution")
            rating_data = {
                'Rating': ['Excellent', 'Good', 'Average', 'Poor'],
                'Count': [
                    company_metrics['excellent_customers'],
                    company_metrics['good_customers'],
                    company_metrics['average_customers'],
                    company_metrics['poor_customers']
                ]
            }
            
            fig_rating = px.pie(
                rating_data,
                values='Count',
                names='Rating',
                title="Customer Business Rating Distribution",
                color_discrete_sequence=['#2E8B57', '#4169E1', '#FFA500', '#DC143C']
            )
            st.plotly_chart(fig_rating, use_container_width=True)
        
        # Company Performance Insights
        st.subheader("📊 Company Performance Insights")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"**Company PE Ratio:** {company_metrics['company_pe_ratio']:.1f}%")
            if company_metrics['company_pe_ratio'] <= 10:
                st.success("✅ Excellent: Low interest burden across all customers")
            elif company_metrics['company_pe_ratio'] <= 20:
                st.info("ℹ️ Good: Reasonable interest burden")
            elif company_metrics['company_pe_ratio'] <= 30:
                st.warning("⚠️ Average: Moderate interest burden")
            else:
                st.error("❌ Poor: High interest burden across customers")
        
        with col2:
            st.info(f"**Investment Efficiency:** ₹{company_metrics['investment_efficiency_ratio']:.0f} per ₹100 profit")
            if company_metrics['investment_efficiency_ratio'] <= 50:
                st.success("✅ Excellent: Low investment required for high profit")
            elif company_metrics['investment_efficiency_ratio'] <= 100:
                st.info("ℹ️ Good: Reasonable investment for profit")
            elif company_metrics['investment_efficiency_ratio'] <= 200:
                st.warning("⚠️ Average: Higher investment needed")
            else:
                st.error("❌ Poor: Very high investment required")
        
        with col3:
            st.info(f"**Average Risk Score:** {company_metrics['avg_risk_score']:.0f}/100")
            if company_metrics['avg_risk_score'] <= 30:
                st.success("✅ Low Risk: Most customers are low risk")
            elif company_metrics['avg_risk_score'] <= 70:
                st.warning("⚠️ Medium Risk: Mixed risk profile")
            else:
                st.error("❌ High Risk: Many customers are high risk")
        
        # Customer Segmentation Table
        st.subheader("📋 Customer Segmentation Details")
        df = pd.DataFrame(all_customer_metrics)
        
        # Create segmentation table
        segmentation_df = df[['customer_name', 'business_rating', 'risk_score', 'profitability_score', 'pe_ratio', 'roi', 'total_profit', 'net_profit']].copy()
        segmentation_df = segmentation_df.sort_values('profitability_score', ascending=False)
        
        # Add color coding for business rating
        def color_rating(val):
            if val == 'Excellent':
                return 'background-color: #d4edda'
            elif val == 'Good':
                return 'background-color: #d1ecf1'
            elif val == 'Average':
                return 'background-color: #fff3cd'
            else:
                return 'background-color: #f8d7da'
        
        styled_df = segmentation_df.style.applymap(color_rating, subset=['business_rating'])
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        # Actionable Insights
        st.subheader("💡 Actionable Business Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**🎯 Focus Areas:**")
            if company_metrics['poor_customers'] > 0:
                st.warning(f"• {company_metrics['poor_customers']} customers need immediate attention")
            if company_metrics['high_risk_customers'] > 0:
                st.warning(f"• {company_metrics['high_risk_customers']} high-risk customers require monitoring")
            if company_metrics['company_pe_ratio'] > 25:
                st.warning("• Consider reducing interest rates or improving payment terms")
            if company_metrics['avg_payment_rate'] < 70:
                st.warning("• Payment collection needs improvement")
        
        with col2:
            st.write("**🚀 Growth Opportunities:**")
            if company_metrics['excellent_customers'] > 0:
                st.success(f"• {company_metrics['excellent_customers']} excellent customers - increase credit limits")
            if company_metrics['low_risk_customers'] > company_metrics['high_risk_customers']:
                st.success("• Good risk profile - consider expanding customer base")
            if company_metrics['avg_roi'] > 50:
                st.success("• Strong ROI - consider increasing investment in top customers")
            if company_metrics['avg_profitability_score'] > 70:
                st.success("• High overall profitability - maintain current strategy")
    
    with tab5:
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
                'Company PE Ratio (%)': company_metrics['company_pe_ratio'],
                'Average Risk Score (0-100)': company_metrics['avg_risk_score'],
                'Average Investment Efficiency (₹ per ₹100 profit)': company_metrics['avg_investment_efficiency'],
                'Average Profitability Score (0-100)': company_metrics['avg_profitability_score'],
                'Average ROI (%)': company_metrics['avg_roi'],
                'Excellent Customers': company_metrics['excellent_customers'],
                'Good Customers': company_metrics['good_customers'],
                'Average Customers': company_metrics['average_customers'],
                'Poor Customers': company_metrics['poor_customers'],
                'Low Risk Customers': company_metrics['low_risk_customers'],
                'Medium Risk Customers': company_metrics['medium_risk_customers'],
                'High Risk Customers': company_metrics['high_risk_customers'],
                'Average Payment Time (days)': company_metrics['avg_payment_time'],
                'Average Payment Rate (%)': company_metrics['avg_payment_rate'],
                'Total Investment (₹)': company_metrics['total_investment'],
                'Investment Efficiency Ratio (₹ per ₹100 profit)': company_metrics['investment_efficiency_ratio'],
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
