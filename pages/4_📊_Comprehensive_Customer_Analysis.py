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
    page_title="Shivam Petroleum - Comprehensive Customer Analysis",
    page_icon="📊",
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

def calculate_comprehensive_metrics(merged_customer, profit_margins, interest_rate):
    """Calculate all comprehensive metrics for a customer"""
    ledger_data = merged_customer['ledger_data']
    sales_data = merged_customer['sales_data']
    
    # 1. Total Quantity Sale
    total_quantity_sale = sales_data['summary']['total_qty']
    
    # 2. Total Profit per Customer
    total_profit = sum(
        calculate_profit(transaction['product_name'], transaction['qty'], transaction['amount'], profit_margins)
        for transaction in sales_data['transactions']
    )
    
    # 3. Total Interest per Customer
    daily_summary = group_transactions_by_date(ledger_data['transactions'])
    daily_summary = calculate_daily_interest(daily_summary, interest_rate)
    total_interest = daily_summary['cumulative_interest'].iloc[-1] if not daily_summary.empty else 0
    
    # 4. Opening Balance
    opening_balance = ledger_data['opening_balance']['amount']
    
    # 5. Closing Balance
    closing_balance = ledger_data['summary']['final_balance']
    
    # 6. Average Outstanding of Customer
    avg_outstanding = daily_summary['outstanding_balance'].mean() if not daily_summary.empty else 0
    
    # 7. High Outstanding Amount of Customer
    high_outstanding = daily_summary['outstanding_balance'].max() if not daily_summary.empty else 0
    
    # 8. Payment Time Analysis (NEW)
    payment_analysis = calculate_payment_time_analysis(ledger_data)
    
    # Calculate payment time metrics
    paid_debts = [debt for debt in payment_analysis if debt['days_to_pay'] is not None]
    unpaid_debts = [debt for debt in payment_analysis if debt['days_to_pay'] is None]
    
    avg_payment_time = np.mean([debt['days_to_pay'] for debt in paid_debts]) if paid_debts else 0
    max_payment_time = max([debt['days_to_pay'] for debt in paid_debts]) if paid_debts else 0
    min_payment_time = min([debt['days_to_pay'] for debt in paid_debts]) if paid_debts else 0
    
    # 9. Profit Efficiency (PE) Ratio - NEW
    pe_ratio = (total_interest / total_profit * 100) if total_profit > 0 else 0
    
    # 10. Customer Risk Score (0-100, lower is better)
    # Based on payment time, outstanding amount, and payment rate
    avg_payment_time_score = min(100, max(0, 100 - (avg_payment_time / 30 * 100)))  # Penalty for longer payment times
    outstanding_ratio = (closing_balance / total_profit * 100) if total_profit > 0 else 0
    outstanding_score = min(100, max(0, 100 - outstanding_ratio))  # Penalty for high outstanding
    payment_rate_score = (len(paid_debts) / len(payment_analysis) * 100) if payment_analysis else 0
    
    risk_score = (avg_payment_time_score * 0.4 + outstanding_score * 0.4 + payment_rate_score * 0.2)
    
    # 11. Investment Efficiency Ratio
    # How much we need to invest (outstanding) to make ₹100 profit
    investment_efficiency = (closing_balance / total_profit * 100) if total_profit > 0 else 0
    
    # 12. Customer Profitability Score (0-100, higher is better)
    # Based on profit, payment behavior, and risk
    profit_score = min(100, (total_profit / 100000 * 100))  # Normalize profit (₹1L = 100 points)
    payment_behavior_score = min(100, max(0, 100 - (avg_payment_time / 30 * 50)))  # Payment time impact
    profitability_score = (profit_score * 0.5 + payment_behavior_score * 0.3 + (100 - risk_score) * 0.2)
    
    # 13. Return on Investment (ROI) for this customer
    total_investment = opening_balance + sum([debt['amount'] for debt in payment_analysis if debt['debt_id'] != 'opening_balance'])
    roi = ((total_profit - total_interest) / total_investment * 100) if total_investment > 0 else 0
    
    # 14. Customer Business Value Rating
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
    
    # 15. Actual Profit and Net Profit
    actual_profit = total_profit  # This is the gross profit from sales
    net_profit = total_profit - total_interest  # Net profit after interest
    
    return {
        'total_quantity_sale': total_quantity_sale,
        'total_profit': total_profit,
        'total_interest': total_interest,
        'opening_balance': opening_balance,
        'closing_balance': closing_balance,
        'avg_outstanding': avg_outstanding,
        'high_outstanding': high_outstanding,
        'avg_payback_period': avg_payment_time,  # Updated to use new calculation
        'pe_ratio': pe_ratio,  # NEW: Profit Efficiency Ratio
        'risk_score': risk_score,  # NEW: Customer Risk Score
        'investment_efficiency': investment_efficiency,  # NEW: Investment Efficiency
        'profitability_score': profitability_score,  # NEW: Customer Profitability Score
        'roi': roi,  # NEW: Return on Investment
        'business_rating': business_rating,  # NEW: Business Value Rating
        'rating_color': rating_color,  # NEW: Rating Color
        'actual_profit': actual_profit,
        'net_profit': net_profit,
        'daily_summary': daily_summary,
        'payment_analysis': payment_analysis,
        'paid_debts': paid_debts,
        'unpaid_debts': unpaid_debts,
        'max_payment_time': max_payment_time,
        'min_payment_time': min_payment_time
    }

def create_comprehensive_charts(metrics, daily_summary):
    """Create comprehensive charts for the dashboard"""
    charts = {}
    
    # 1. Outstanding Balance Trend
    if not daily_summary.empty:
        fig_balance = go.Figure()
        fig_balance.add_trace(go.Scatter(
            x=daily_summary['date'],
            y=daily_summary['outstanding_balance'],
            mode='lines+markers',
            name='Outstanding Balance',
            line=dict(color='#1f77b4', width=2)
        ))
        fig_balance.update_layout(
            title="Outstanding Balance Over Time",
            xaxis_title="Date",
            yaxis_title="Balance (₹)",
            height=400
        )
        fig_balance.update_yaxes(tickformat='₹,.0f')
        charts['balance_trend'] = fig_balance
    
    # 2. Interest Accumulation
    if not daily_summary.empty:
        fig_interest = go.Figure()
        fig_interest.add_trace(go.Scatter(
            x=daily_summary['date'],
            y=daily_summary['cumulative_interest'],
            mode='lines+markers',
            name='Cumulative Interest',
            line=dict(color='#ff7f0e', width=2)
        ))
        fig_interest.update_layout(
            title="Interest Accumulation Over Time",
            xaxis_title="Date",
            yaxis_title="Cumulative Interest (₹)",
            height=400
        )
        fig_interest.update_yaxes(tickformat='₹,.0f')
        charts['interest_trend'] = fig_interest
    
    # 3. Payment Time Analysis Chart
    if metrics['paid_debts']:
        payment_times = [debt['days_to_pay'] for debt in metrics['paid_debts']]
        debt_amounts = [debt['amount'] for debt in metrics['paid_debts']]
        
        fig_payment_time = go.Figure()
        fig_payment_time.add_trace(go.Scatter(
            x=payment_times,
            y=debt_amounts,
            mode='markers',
            name='Payment Time vs Debt Amount',
            marker=dict(
                size=10,
                color=payment_times,
                colorscale='RdYlGn_r',
                showscale=True,
                colorbar=dict(title="Days to Pay")
            ),
            text=[f"Debt: {format_currency(amt)}<br>Days: {days}" for amt, days in zip(debt_amounts, payment_times)],
            hovertemplate='%{text}<extra></extra>'
        ))
        fig_payment_time.update_layout(
            title="Payment Time Analysis - Debt Amount vs Days to Pay",
            xaxis_title="Days to Pay",
            yaxis_title="Debt Amount (₹)",
            height=400
        )
        fig_payment_time.update_yaxes(tickformat='₹,.0f')
        charts['payment_time_analysis'] = fig_payment_time
    
    # 4. Payment Time Distribution
    if metrics['paid_debts']:
        payment_times = [debt['days_to_pay'] for debt in metrics['paid_debts']]
        
        fig_distribution = go.Figure()
        fig_distribution.add_trace(go.Histogram(
            x=payment_times,
            nbinsx=20,
            name='Payment Time Distribution',
            marker_color='lightblue'
        ))
        fig_distribution.update_layout(
            title="Distribution of Payment Times",
            xaxis_title="Days to Pay",
            yaxis_title="Number of Debts",
            height=400
        )
        charts['payment_time_distribution'] = fig_distribution
    
    # 5. Outstanding vs Paid Debts
    if metrics['payment_analysis']:
        paid_count = len(metrics['paid_debts'])
        unpaid_count = len(metrics['unpaid_debts'])
        
        fig_debt_status = go.Figure()
        fig_debt_status.add_trace(go.Pie(
            labels=['Paid Debts', 'Unpaid Debts'],
            values=[paid_count, unpaid_count],
            hole=0.3,
            marker_colors=['#2E8B57', '#DC143C']
        ))
        fig_debt_status.update_layout(
            title="Debt Payment Status",
            height=400
        )
        charts['debt_status_pie'] = fig_debt_status
    
    # 6. Profit vs Interest Comparison
    fig_comparison = go.Figure()
    categories = ['Total Profit', 'Total Interest', 'Net Profit']
    values = [metrics['total_profit'], metrics['total_interest'], metrics['net_profit']]
    colors = ['green', 'orange', 'blue']
    
    fig_comparison.add_trace(go.Bar(
        x=categories,
        y=values,
        marker_color=colors,
        text=[format_currency(v) for v in values],
        textposition='auto'
    ))
    fig_comparison.update_layout(
        title="Profit vs Interest Analysis",
        xaxis_title="Category",
        yaxis_title="Amount (₹)",
        height=400
    )
    fig_comparison.update_yaxes(tickformat='₹,.0f')
    charts['profit_interest_comparison'] = fig_comparison
    
    return charts

def main():
    st.title("📊 Shivam Petroleum - Comprehensive Customer Analysis")
    st.markdown("---")
    
    # Add custom CSS for better text visibility
    st.markdown("""
    <style>
    .metric-container {
        word-wrap: break-word;
        white-space: normal;
    }
    .metric-container .metric-value {
        font-size: 1.2rem !important;
        line-height: 1.3 !important;
    }
    .metric-container .metric-label {
        font-size: 0.9rem !important;
        line-height: 1.2 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Load data
    ledger_customers = load_ledger_data()
    sales_customers = load_customer_data()
    
    # Merge data
    merged_customers = merge_customer_data(ledger_customers, sales_customers)
    
    # Sidebar
    st.sidebar.header("🔧 Analysis Settings")
    
    # Customer selection
    customer_options = [f"{c['customer_id']} - {c['customer_name']}" for c in merged_customers]
    selected_customer_idx = st.sidebar.selectbox(
        "Select Customer:",
        range(len(customer_options)),
        format_func=lambda x: customer_options[x]
    )
    
    selected_customer = merged_customers[selected_customer_idx]
    
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
    
    # Calculate comprehensive metrics
    metrics = calculate_comprehensive_metrics(selected_customer, profit_margins, interest_rate)
    
    # Main content
    st.header(f"📊 Comprehensive Analysis - {selected_customer['customer_name']}")
    st.info(f"📅 **Analysis Period:** {fy_start_date.strftime('%d-%m-%Y')} to {fy_end_date.strftime('%d-%m-%Y')} (FY {fy_display})")
    
    # Key Metrics Row 1
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Quantity Sale",
            f"{metrics['total_quantity_sale']:,.2f} L"
        )
    
    with col2:
        st.metric(
            "Total Profit",
            format_currency(metrics['total_profit'])
        )
    
    with col3:
        st.metric(
            "Total Interest",
            format_currency(metrics['total_interest'])
        )
    
    with col4:
        st.metric(
            "Opening Balance",
            format_currency(metrics['opening_balance'])
        )
    
    with col5:
        st.metric(
            "Closing Balance",
            format_currency(metrics['closing_balance'])
        )
    
    # Key Metrics Row 2
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Avg Outstanding",
            format_currency(metrics['avg_outstanding'])
        )
    
    with col2:
        st.metric(
            "High Outstanding",
            format_currency(metrics['high_outstanding'])
        )
    
    with col3:
        st.metric(
            "Avg Payment Time",
            f"{metrics['avg_payback_period']:.1f} days"
        )
    
    with col4:
        st.metric(
            "PE Ratio",
            f"{metrics['pe_ratio']:.1f}%"
        )
    
    with col5:
        st.metric(
            "Net Profit",
            format_currency(metrics['net_profit'])
        )
    
    # Key Metrics Row 3 - Payment Time Analysis
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Paid Debts",
            f"{len(metrics['paid_debts'])}"
        )
    
    with col2:
        st.metric(
            "Unpaid Debts",
            f"{len(metrics['unpaid_debts'])}"
        )
    
    with col3:
        st.metric(
            "Max Payment Time",
            f"{metrics['max_payment_time']:.0f} days"
        )
    
    with col4:
        st.metric(
            "Min Payment Time",
            f"{metrics['min_payment_time']:.0f} days"
        )
    
    with col5:
        total_debts = len(metrics['paid_debts']) + len(metrics['unpaid_debts'])
        payment_rate = (len(metrics['paid_debts']) / total_debts * 100) if total_debts > 0 else 0
        st.metric(
            "Payment Rate",
            f"{payment_rate:.1f}%"
        )
    
    # Key Metrics Row 4 - Business Intelligence
    st.markdown("### 🎯 Business Intelligence Metrics")
    col1, col2, col3, col4, col5 = st.columns([1.2, 1.2, 1.5, 1, 1.1])
    
    with col1:
        st.metric(
            "Risk Score",
            f"{metrics['risk_score']:.0f}/100",
            delta=f"{'Low Risk' if metrics['risk_score'] <= 30 else 'High Risk' if metrics['risk_score'] >= 70 else 'Medium Risk'}"
        )
    
    with col2:
        st.metric(
            "Profitability Score",
            f"{metrics['profitability_score']:.0f}/100"
        )
    
    with col3:
        st.metric(
            "Investment Efficiency",
            f"₹{metrics['investment_efficiency']:.0f}",
            help="Amount invested per ₹100 profit"
        )
    
    with col4:
        st.metric(
            "ROI",
            f"{metrics['roi']:.1f}%"
        )
    
    with col5:
        # Business Rating with color
        rating_color_map = {
            'green': '🟢',
            'blue': '🔵', 
            'orange': '🟠',
            'red': '🔴'
        }
        st.metric(
            "Business Rating",
            f"{rating_color_map.get(metrics['rating_color'], '⚪')} {metrics['business_rating']}"
        )
    
    st.markdown("---")
    
    # Detailed Analysis Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Financial Overview", "📊 Charts & Trends", "📋 Detailed Breakdown", "📄 Export Data"])
    
    with tab1:
        st.subheader("Financial Overview")
        
        # Financial Summary Cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"**Actual Profit:** {format_currency(metrics['actual_profit'])}")
            st.info(f"**Total Interest:** {format_currency(metrics['total_interest'])}")
        
        with col2:
            st.success(f"**Net Profit:** {format_currency(metrics['net_profit'])}")
            st.success(f"**Profit Margin:** {(metrics['total_profit']/metrics['total_quantity_sale']):.2f} ₹/L" if metrics['total_quantity_sale'] > 0 else "**Profit Margin:** N/A")
        
        with col3:
            st.warning(f"**Interest Rate:** {interest_rate}% p.a.")
            st.warning(f"**PE Ratio:** {metrics['pe_ratio']:.1f}%")
    
    # Business Intelligence Insights
    st.subheader("🎯 Business Intelligence Insights")
    
    col1, col2, col3 = st.columns([1.2, 1.5, 1.3])
    
    with col1:
        st.info(f"**PE Ratio Analysis:** {metrics['pe_ratio']:.1f}%")
        if metrics['pe_ratio'] <= 10:
            st.success("✅ Excellent: Low interest burden on customer")
        elif metrics['pe_ratio'] <= 20:
            st.info("ℹ️ Good: Reasonable interest burden")
        elif metrics['pe_ratio'] <= 30:
            st.warning("⚠️ Average: Moderate interest burden")
        else:
            st.error("❌ Poor: High interest burden on customer")
    
    with col2:
        st.info(f"**Investment Efficiency:**\n₹{metrics['investment_efficiency']:.0f} per ₹100 profit")
        if metrics['investment_efficiency'] <= 50:
            st.success("✅ Excellent:\nLow investment required for high profit")
        elif metrics['investment_efficiency'] <= 100:
            st.info("ℹ️ Good:\nReasonable investment for profit")
        elif metrics['investment_efficiency'] <= 200:
            st.warning("⚠️ Average:\nHigher investment needed")
        else:
            st.error("❌ Poor:\nVery high investment required")
    
    with col3:
        st.info(f"**Business Rating:** {metrics['business_rating']}")
        if metrics['business_rating'] == "Excellent":
            st.success("✅ This customer is highly profitable and low risk")
        elif metrics['business_rating'] == "Good":
            st.info("ℹ️ This customer is profitable with manageable risk")
        elif metrics['business_rating'] == "Average":
            st.warning("⚠️ This customer needs monitoring")
        else:
            st.error("❌ Consider reducing credit limit or improving terms")
    
    with tab2:
        st.subheader("Charts & Trends")
        
        # Create charts
        charts = create_comprehensive_charts(metrics, metrics['daily_summary'])
        
        # Display charts
        if 'balance_trend' in charts:
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(charts['balance_trend'], use_container_width=True)
            with col2:
                st.plotly_chart(charts['interest_trend'], use_container_width=True)
        
        # Payment Time Analysis Charts
        if 'payment_time_analysis' in charts:
            st.subheader("🕒 Payment Time Analysis")
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(charts['payment_time_analysis'], use_container_width=True)
            with col2:
                st.plotly_chart(charts['payment_time_distribution'], use_container_width=True)
        
        if 'debt_status_pie' in charts:
            st.plotly_chart(charts['debt_status_pie'], use_container_width=True)
        
        if 'profit_interest_comparison' in charts:
            st.plotly_chart(charts['profit_interest_comparison'], use_container_width=True)
    
    with tab3:
        st.subheader("Detailed Breakdown")
        
        # Transaction Summary
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Ledger Summary:**")
            st.write(f"• Total Ledger Transactions: {selected_customer['total_transactions_ledger']}")
            st.write(f"• Total Debits: {format_currency(selected_customer['ledger_data']['summary']['total_debits'])}")
            st.write(f"• Total Credits: {format_currency(selected_customer['ledger_data']['summary']['total_credits'])}")
            st.write(f"• Net Position: {format_currency(selected_customer['ledger_data']['summary']['total_debits'] - selected_customer['ledger_data']['summary']['total_credits'])}")
        
        with col2:
            st.write("**Sales Summary:**")
            st.write(f"• Total Sales Transactions: {selected_customer['total_transactions_sales']}")
            st.write(f"• Total Sales Amount: {format_currency(selected_customer['sales_data']['summary']['total_amount'])}")
            st.write(f"• Total Quantity Sold: {metrics['total_quantity_sale']:,.2f} L")
            st.write(f"• Unique Vehicles: {selected_customer['sales_data']['summary']['unique_vehicles']}")
        
        # Payment Time Analysis Table
        if metrics['payment_analysis']:
            st.write("**🕒 Payment Time Analysis:**")
            
            # Create payment analysis dataframe
            payment_data = []
            for debt in metrics['payment_analysis']:
                payment_data.append({
                    'Debt ID': debt['debt_id'],
                    'Amount': format_currency(debt['amount']),
                    'Date Created': debt['date_created'].strftime('%Y-%m-%d'),
                    'Amount Paid': format_currency(debt['amount_paid']),
                    'Amount Remaining': format_currency(debt['amount_remaining']),
                    'Days to Pay': f"{debt['days_to_pay']:.0f}" if debt['days_to_pay'] is not None else "Unpaid",
                    'Status': 'Paid' if debt['days_to_pay'] is not None else 'Unpaid',
                    'Payment Dates': ', '.join([d.strftime('%Y-%m-%d') for d in debt['payment_dates']]) if debt['payment_dates'] else 'None'
                })
            
            payment_df = pd.DataFrame(payment_data)
            st.dataframe(payment_df, use_container_width=True, height=400)
            
            # Payment Summary Statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"**Total Debts:** {len(metrics['payment_analysis'])}")
                st.info(f"**Paid Debts:** {len(metrics['paid_debts'])}")
            with col2:
                st.warning(f"**Unpaid Debts:** {len(metrics['unpaid_debts'])}")
                st.warning(f"**Avg Payment Time:** {metrics['avg_payback_period']:.1f} days")
            with col3:
                st.success(f"**Max Payment Time:** {metrics['max_payment_time']:.0f} days")
                st.success(f"**Min Payment Time:** {metrics['min_payment_time']:.0f} days")
        
        # Outstanding Analysis
        if not metrics['daily_summary'].empty:
            st.write("**Outstanding Analysis:**")
            outstanding_df = metrics['daily_summary'][['date', 'outstanding_balance', 'interest', 'cumulative_interest']].copy()
            outstanding_df['date'] = outstanding_df['date'].dt.strftime('%Y-%m-%d')
            outstanding_df['outstanding_balance'] = outstanding_df['outstanding_balance'].apply(lambda x: format_currency(x))
            outstanding_df['interest'] = outstanding_df['interest'].apply(lambda x: format_currency(x))
            outstanding_df['cumulative_interest'] = outstanding_df['cumulative_interest'].apply(lambda x: format_currency(x))
            outstanding_df.columns = ['Date', 'Outstanding Balance', 'Daily Interest', 'Cumulative Interest']
            st.dataframe(outstanding_df, use_container_width=True, height=300)
    
    with tab4:
        st.subheader("Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Export comprehensive metrics
            metrics_data = {
                'Customer Name': selected_customer['customer_name'],
                'Total Quantity Sale (L)': metrics['total_quantity_sale'],
                'Total Profit (₹)': metrics['total_profit'],
                'Total Interest (₹)': metrics['total_interest'],
                'Opening Balance (₹)': metrics['opening_balance'],
                'Closing Balance (₹)': metrics['closing_balance'],
                'Average Outstanding (₹)': metrics['avg_outstanding'],
                'High Outstanding (₹)': metrics['high_outstanding'],
                'Average Payback Period (days)': metrics['avg_payback_period'],
                'PE Ratio (%)': metrics['pe_ratio'],
                'Risk Score (0-100)': metrics['risk_score'],
                'Investment Efficiency (₹ per ₹100 profit)': metrics['investment_efficiency'],
                'Profitability Score (0-100)': metrics['profitability_score'],
                'ROI (%)': metrics['roi'],
                'Business Rating': metrics['business_rating'],
                'Actual Profit (₹)': metrics['actual_profit'],
                'Net Profit (₹)': metrics['net_profit']
            }
            
            metrics_df = pd.DataFrame([metrics_data])
            csv_data = metrics_df.to_csv(index=False)
            
            st.download_button(
                label="📊 Download Comprehensive Metrics (CSV)",
                data=csv_data,
                file_name=f"{selected_customer['customer_name']}_comprehensive_metrics.csv",
                mime="text/csv"
            )
        
        with col2:
            # Export daily outstanding data
            if not metrics['daily_summary'].empty:
                daily_data = metrics['daily_summary'].to_csv(index=False)
                st.download_button(
                    label="📈 Download Daily Outstanding Data (CSV)",
                    data=daily_data,
                    file_name=f"{selected_customer['customer_name']}_daily_outstanding.csv",
                    mime="text/csv"
                )
        
        # Export Payment Time Analysis
        if metrics['payment_analysis']:
            st.subheader("🕒 Payment Time Analysis Export")
            col1, col2 = st.columns(2)
            
            with col1:
                # Export payment analysis data
                payment_data = []
                for debt in metrics['payment_analysis']:
                    payment_data.append({
                        'Debt ID': debt['debt_id'],
                        'Amount': debt['amount'],
                        'Date Created': debt['date_created'].strftime('%Y-%m-%d'),
                        'Amount Paid': debt['amount_paid'],
                        'Amount Remaining': debt['amount_remaining'],
                        'Days to Pay': debt['days_to_pay'] if debt['days_to_pay'] is not None else 'Unpaid',
                        'Status': 'Paid' if debt['days_to_pay'] is not None else 'Unpaid',
                        'Payment Dates': ', '.join([d.strftime('%Y-%m-%d') for d in debt['payment_dates']]) if debt['payment_dates'] else 'None'
                    })
                
                payment_df = pd.DataFrame(payment_data)
                payment_csv = payment_df.to_csv(index=False)
                st.download_button(
                    label="🕒 Download Payment Time Analysis (CSV)",
                    data=payment_csv,
                    file_name=f"{selected_customer['customer_name']}_payment_analysis.csv",
                    mime="text/csv"
                )
            
            with col2:
                # Export payment summary
                summary_data = {
                    'Customer Name': selected_customer['customer_name'],
                    'Total Debts': len(metrics['payment_analysis']),
                    'Paid Debts': len(metrics['paid_debts']),
                    'Unpaid Debts': len(metrics['unpaid_debts']),
                    'Average Payment Time (days)': metrics['avg_payback_period'],
                    'Max Payment Time (days)': metrics['max_payment_time'],
                    'Min Payment Time (days)': metrics['min_payment_time'],
                    'Payment Rate (%)': (len(metrics['paid_debts']) / len(metrics['payment_analysis']) * 100) if metrics['payment_analysis'] else 0
                }
                
                summary_df = pd.DataFrame([summary_data])
                summary_csv = summary_df.to_csv(index=False)
                st.download_button(
                    label="📊 Download Payment Summary (CSV)",
                    data=summary_csv,
                    file_name=f"{selected_customer['customer_name']}_payment_summary.csv",
                    mime="text/csv"
                )

if __name__ == "__main__":
    main()
