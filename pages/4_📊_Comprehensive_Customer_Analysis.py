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
    
    # 8. Average Payback Period (in days)
    # Calculate days between transactions and payments
    transactions_df = pd.DataFrame(ledger_data['transactions'])
    transactions_df['date'] = pd.to_datetime(transactions_df['date'])
    
    # Find days between debit and credit transactions
    debit_dates = transactions_df[transactions_df['debit'] > 0]['date']
    credit_dates = transactions_df[transactions_df['credit'] > 0]['date']
    
    payback_periods = []
    for debit_date in debit_dates:
        # Find next credit date after this debit
        future_credits = credit_dates[credit_dates > debit_date]
        if not future_credits.empty:
            next_credit = future_credits.min()
            days_diff = (next_credit - debit_date).days
            payback_periods.append(days_diff)
    
    avg_payback_period = np.mean(payback_periods) if payback_periods else 0
    
    # 9. Profit to Interest Ratio
    profit_to_interest_ratio = total_profit / total_interest if total_interest > 0 else 0
    
    # 10. Actual Profit and Net Profit
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
        'avg_payback_period': avg_payback_period,
        'profit_to_interest_ratio': profit_to_interest_ratio,
        'actual_profit': actual_profit,
        'net_profit': net_profit,
        'daily_summary': daily_summary
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
    
    # 3. Profit vs Interest Comparison
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
    
    # Calculate comprehensive metrics
    metrics = calculate_comprehensive_metrics(selected_customer, profit_margins, interest_rate)
    
    # Main content
    st.header(f"📊 Comprehensive Analysis - {selected_customer['customer_name']}")
    
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
            "Avg Payback Period",
            f"{metrics['avg_payback_period']:.1f} days"
        )
    
    with col4:
        st.metric(
            "Profit/Interest Ratio",
            f"{metrics['profit_to_interest_ratio']:.2f}"
        )
    
    with col5:
        st.metric(
            "Net Profit",
            format_currency(metrics['net_profit'])
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
            st.warning(f"**Payback Efficiency:** {metrics['profit_to_interest_ratio']:.2f}")
    
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
                'Profit to Interest Ratio': metrics['profit_to_interest_ratio'],
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

if __name__ == "__main__":
    main()
