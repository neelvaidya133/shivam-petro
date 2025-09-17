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
    page_title="Shivam Petroleum - Financial Intelligence",
    page_icon="💰",
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

def calculate_financial_metrics(all_customer_metrics, expenses, fy_start_date, fy_end_date):
    """Calculate comprehensive financial metrics including expenses"""
    
    # Basic revenue metrics
    total_revenue = sum(customer['total_sales_amount'] for customer in all_customer_metrics)
    total_profit = sum(customer['total_profit'] for customer in all_customer_metrics)
    total_interest = sum(customer['total_interest'] for customer in all_customer_metrics)
    
    # Calculate expenses
    total_expenses = sum(expenses.values())
    
    # Financial ratios and metrics
    gross_profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    operating_profit = total_profit - total_interest
    operating_margin = (operating_profit / total_revenue * 100) if total_revenue > 0 else 0
    net_profit = operating_profit - total_expenses
    net_profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Expense ratios
    expense_ratio = (total_expenses / total_revenue * 100) if total_revenue > 0 else 0
    interest_ratio = (total_interest / total_revenue * 100) if total_revenue > 0 else 0
    
    # Customer metrics
    total_customers = len(all_customer_metrics)
    revenue_per_customer = total_revenue / total_customers if total_customers > 0 else 0
    profit_per_customer = total_profit / total_customers if total_customers > 0 else 0
    expense_per_customer = total_expenses / total_customers if total_customers > 0 else 0
    
    # Break-even analysis
    break_even_revenue = total_expenses / (gross_profit_margin / 100) if gross_profit_margin > 0 else 0
    break_even_customers = break_even_revenue / revenue_per_customer if revenue_per_customer > 0 else 0
    
    # Working capital metrics
    total_outstanding = sum(customer['closing_balance'] for customer in all_customer_metrics)
    working_capital_turnover = total_revenue / total_outstanding if total_outstanding > 0 else 0
    
    return {
        'total_revenue': total_revenue,
        'total_profit': total_profit,
        'total_interest': total_interest,
        'total_expenses': total_expenses,
        'gross_profit_margin': gross_profit_margin,
        'operating_profit': operating_profit,
        'operating_margin': operating_margin,
        'net_profit': net_profit,
        'net_profit_margin': net_profit_margin,
        'expense_ratio': expense_ratio,
        'interest_ratio': interest_ratio,
        'total_customers': total_customers,
        'revenue_per_customer': revenue_per_customer,
        'profit_per_customer': profit_per_customer,
        'expense_per_customer': expense_per_customer,
        'break_even_revenue': break_even_revenue,
        'break_even_customers': break_even_customers,
        'total_outstanding': total_outstanding,
        'working_capital_turnover': working_capital_turnover
    }

def create_financial_charts(financial_metrics, expenses, all_customer_metrics):
    """Create comprehensive financial charts"""
    charts = {}
    
    # 1. Revenue vs Expenses vs Profit
    categories = ['Total Revenue', 'Total Expenses', 'Operating Profit', 'Net Profit']
    values = [
        financial_metrics['total_revenue'],
        financial_metrics['total_expenses'],
        financial_metrics['operating_profit'],
        financial_metrics['net_profit']
    ]
    colors = ['#2E8B57', '#DC143C', '#4169E1', '#32CD32']
    
    fig_revenue_expense = go.Figure()
    fig_revenue_expense.add_trace(go.Bar(
        x=categories,
        y=values,
        marker_color=colors,
        text=[format_currency(v) for v in values],
        textposition='auto'
    ))
    fig_revenue_expense.update_layout(
        title="Revenue vs Expenses vs Profit Analysis",
        xaxis_title="Category",
        yaxis_title="Amount (₹)",
        height=400
    )
    fig_revenue_expense.update_yaxes(tickformat='₹,.0f')
    charts['revenue_expense_analysis'] = fig_revenue_expense
    
    # 2. Expense Breakdown Pie Chart
    if expenses:
        expense_data = {
            'Category': list(expenses.keys()),
            'Amount': list(expenses.values())
        }
        
        fig_expenses = px.pie(
            expense_data,
            values='Amount',
            names='Category',
            title="Expense Breakdown",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_expenses.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Amount: ₹%{value:,.0f}<br>Percentage: %{percent}<extra></extra>'
        )
        charts['expense_breakdown'] = fig_expenses
    
    # 3. Profit Margin Analysis
    margin_data = {
        'Margin Type': ['Gross Profit', 'Operating', 'Net Profit'],
        'Percentage': [
            financial_metrics['gross_profit_margin'],
            financial_metrics['operating_margin'],
            financial_metrics['net_profit_margin']
        ]
    }
    
    fig_margins = px.bar(
        margin_data,
        x='Margin Type',
        y='Percentage',
        title="Profit Margin Analysis",
        color='Percentage',
        color_continuous_scale='RdYlGn'
    )
    fig_margins.update_layout(height=400)
    charts['profit_margins'] = fig_margins
    
    # 4. Customer Profitability Scatter
    df = pd.DataFrame(all_customer_metrics)
    fig_customer_profit = px.scatter(
        df,
        x='total_sales_amount',
        y='total_profit',
        size='closing_balance',
        hover_name='customer_name',
        title="Customer Profitability Analysis",
        labels={
            'total_sales_amount': 'Sales Revenue (₹)',
            'total_profit': 'Profit (₹)',
            'closing_balance': 'Outstanding Balance'
        }
    )
    fig_customer_profit.update_xaxes(tickformat='₹,.0f')
    fig_customer_profit.update_yaxes(tickformat='₹,.0f')
    charts['customer_profitability'] = fig_customer_profit
    
    # 5. Monthly Revenue Trend (if we have date data)
    # This would require date-based analysis of transactions
    charts['monthly_trend'] = None  # Placeholder for future implementation
    
    return charts

def main():
    st.title("💰 Shivam Petroleum - Financial Intelligence Dashboard")
    st.markdown("---")
    
    # Load data
    ledger_customers = load_ledger_data()
    sales_customers = load_customer_data()
    
    # Sidebar for expense input
    st.sidebar.header("💰 Expense Management")
    st.sidebar.subheader("Annual Expenses (₹)")
    
    # Single total expense input
    total_expenses = st.sidebar.number_input(
        "Total Annual Expenses:",
        min_value=0,
        value=350000,  # Default value
        step=10000,
        help="Enter your total annual operating expenses (rent, salaries, utilities, etc.)"
    )
    
    st.sidebar.metric("Total Annual Expenses", format_currency(total_expenses))
    
    # Interest rate setting
    st.sidebar.subheader("💹 Interest Settings")
    interest_rate = st.sidebar.number_input(
        "Annual Interest Rate (%):",
        min_value=0.0,
        max_value=50.0,
        value=12.0,
        step=0.1,
        help="Interest rate used for calculations"
    )
    
    # Create a simple expenses dict for compatibility
    expenses = {'Total Annual Expenses': total_expenses}
    
    # Financial year settings
    st.sidebar.subheader("📅 Financial Year")
    fy_start_date = pd.to_datetime('2024-04-01')
    fy_end_date = pd.to_datetime('2025-03-31')
    fy_display = "2024-2025"
    
    # Calculate basic customer metrics (simplified version)
    all_customer_metrics = []
    for ledger_customer in ledger_customers:
        # Find matching sales customer
        sales_customer = next(
            (sc for sc in sales_customers if sc['customer_name'] == ledger_customer['customer_name']), 
            None
        )
        
        if sales_customer:
            # Calculate basic metrics
            total_sales_amount = sum(transaction['amount'] for transaction in sales_customer['transactions'])
            total_profit = sum(
                calculate_profit(transaction['product_name'], transaction['qty'], transaction['amount'], {
                    'diesel_per_liter': 3.0,
                    'petrol_per_liter': 2.0,
                    'oil_percentage': 15.0,
                    'others_per_liter': 1.0
                })
                for transaction in sales_customer['transactions']
            )
            
            # Calculate simple interest (approximation)
            # For financial intelligence, we'll use a simple calculation
            closing_balance = ledger_customer['summary']['final_balance']
            # Estimate interest based on user-defined rate
            estimated_interest = closing_balance * (interest_rate / 100)  # Annual interest
            
            all_customer_metrics.append({
                'customer_name': ledger_customer['customer_name'],
                'total_sales_amount': total_sales_amount,
                'total_profit': total_profit,
                'total_interest': estimated_interest,
                'closing_balance': closing_balance
            })
    
    # Calculate financial metrics
    financial_metrics = calculate_financial_metrics(all_customer_metrics, expenses, fy_start_date, fy_end_date)
    
    # Main content
    st.header(f"📊 Financial Analysis - FY {fy_display}")
    st.info(f"📅 **Analysis Period:** {fy_start_date.strftime('%d-%m-%Y')} to {fy_end_date.strftime('%d-%m-%Y')}")
    
    # Key Financial Metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Revenue",
            format_currency(financial_metrics['total_revenue']),
            help="Total sales revenue from all customers"
        )
    
    with col2:
        st.metric(
            "Total Expenses",
            format_currency(financial_metrics['total_expenses']),
            help="Total annual operating expenses"
        )
    
    with col3:
        st.metric(
            "Operating Profit",
            format_currency(financial_metrics['operating_profit']),
            help="Profit after interest but before expenses"
        )
    
    with col4:
        st.metric(
            "Net Profit",
            format_currency(financial_metrics['net_profit']),
            help="Final profit after all expenses"
        )
    
    with col5:
        st.metric(
            "Net Profit Margin",
            f"{financial_metrics['net_profit_margin']:.1f}%",
            help="Net profit as percentage of revenue"
        )
    
    # Financial Health Metrics
    st.markdown("### 💊 Financial Health Indicators")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Gross Profit Margin",
            f"{financial_metrics['gross_profit_margin']:.1f}%",
            help="Profit margin before interest and expenses"
        )
    
    with col2:
        st.metric(
            "Operating Margin",
            f"{financial_metrics['operating_margin']:.1f}%",
            help="Operating profit as percentage of revenue"
        )
    
    with col3:
        st.metric(
            "Expense Ratio",
            f"{financial_metrics['expense_ratio']:.1f}%",
            help="Expenses as percentage of revenue"
        )
    
    with col4:
        st.metric(
            "Break-even Revenue",
            format_currency(financial_metrics['break_even_revenue']),
            help="Minimum revenue needed to cover all expenses"
        )
    
    with col5:
        st.metric(
            "Revenue per Customer",
            format_currency(financial_metrics['revenue_per_customer']),
            help="Average revenue generated per customer"
        )
    
    st.markdown("---")
    
    # Detailed Analysis Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Financial Overview",
        "💰 Expense Analysis", 
        "👥 Customer Profitability",
        "📊 Financial Ratios",
        "📄 Export Data"
    ])
    
    with tab1:
        st.subheader("Financial Performance Overview")
        
        # Create charts
        charts = create_financial_charts(financial_metrics, expenses, all_customer_metrics)
        
        # Revenue vs Expenses chart
        if 'revenue_expense_analysis' in charts:
            st.plotly_chart(charts['revenue_expense_analysis'], use_container_width=True)
        
        # Financial summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"**Total Revenue:** {format_currency(financial_metrics['total_revenue'])}")
            st.info(f"**Gross Profit:** {format_currency(financial_metrics['total_profit'])}")
        
        with col2:
            st.success(f"**Operating Profit:** {format_currency(financial_metrics['operating_profit'])}")
            st.success(f"**Net Profit:** {format_currency(financial_metrics['net_profit'])}")
        
        with col3:
            st.warning(f"**Total Expenses:** {format_currency(financial_metrics['total_expenses'])}")
            st.warning(f"**Total Interest:** {format_currency(financial_metrics['total_interest'])}")
    
    with tab2:
        st.subheader("Expense Analysis")
        
        # Expense overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Total Annual Expenses",
                format_currency(total_expenses),
                help="Total operating expenses for the year"
            )
        
        with col2:
            st.metric(
                "Expense Ratio",
                f"{financial_metrics['expense_ratio']:.1f}%",
                help="Expenses as percentage of total revenue"
            )
        
        with col3:
            st.metric(
                "Expense per Customer",
                format_currency(financial_metrics['expense_per_customer']),
                help="Average expense per customer"
            )
        
        # Expense insights
        st.subheader("💡 Expense Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📊 Expense Analysis:**")
            if financial_metrics['expense_ratio'] > 50:
                st.error("• High expense ratio - consider cost reduction")
                st.write("• Your expenses are more than 50% of revenue")
            elif financial_metrics['expense_ratio'] > 30:
                st.warning("• Moderate expense ratio - monitor costs")
                st.write("• Your expenses are 30-50% of revenue")
            else:
                st.success("• Good expense ratio - well controlled")
                st.write("• Your expenses are less than 30% of revenue")
            
            st.info(f"• Break-even revenue needed: {format_currency(financial_metrics['break_even_revenue'])}")
        
        with col2:
            st.write("**🎯 Cost Management:**")
            if financial_metrics['expense_per_customer'] > financial_metrics['profit_per_customer']:
                st.error("• Expenses per customer exceed profit per customer")
                st.write("• You're spending more on each customer than they generate in profit")
            else:
                st.success("• Profit per customer exceeds expenses per customer")
                st.write("• Each customer generates more profit than the cost to serve them")
            
            st.write(f"• Average expense per customer: {format_currency(financial_metrics['expense_per_customer'])}")
            st.write(f"• Average profit per customer: {format_currency(financial_metrics['profit_per_customer'])}")
        
        # Expense vs Revenue comparison
        st.subheader("📈 Revenue vs Expenses Comparison")
        
        comparison_data = {
            'Category': ['Total Revenue', 'Total Expenses', 'Net Profit'],
            'Amount (₹)': [
                financial_metrics['total_revenue'],
                financial_metrics['total_expenses'],
                financial_metrics['net_profit']
            ],
            'Color': ['#2E8B57', '#DC143C', '#4169E1']
        }
        
        fig_comparison = px.bar(
            comparison_data,
            x='Category',
            y='Amount (₹)',
            title="Revenue vs Expenses vs Net Profit",
            color='Category',
            color_discrete_sequence=['#2E8B57', '#DC143C', '#4169E1']
        )
        fig_comparison.update_layout(height=400)
        fig_comparison.update_yaxes(tickformat='₹,.0f')
        st.plotly_chart(fig_comparison, use_container_width=True)
    
    with tab3:
        st.subheader("Customer Profitability Analysis")
        
        # Customer profitability scatter plot
        if 'customer_profitability' in charts:
            st.plotly_chart(charts['customer_profitability'], use_container_width=True)
        
        # Customer profitability table
        st.subheader("Customer Profitability Details")
        df = pd.DataFrame(all_customer_metrics)
        df['profit_margin'] = (df['total_profit'] / df['total_sales_amount'] * 100).round(2)
        df['profitability_ratio'] = (df['total_profit'] / financial_metrics['expense_per_customer']).round(2)
        df = df.sort_values('total_profit', ascending=False)
        
        # Format for display
        display_df = df.copy()
        display_df['total_sales_amount'] = display_df['total_sales_amount'].apply(lambda x: format_currency(x))
        display_df['total_profit'] = display_df['total_profit'].apply(lambda x: format_currency(x))
        display_df['closing_balance'] = display_df['closing_balance'].apply(lambda x: format_currency(x))
        
        st.dataframe(display_df, use_container_width=True)
    
    with tab4:
        st.subheader("Financial Ratios & Analysis")
        
        # Profit margin analysis
        if 'profit_margins' in charts:
            st.plotly_chart(charts['profit_margins'], use_container_width=True)
        
        # Financial ratios table
        st.subheader("Key Financial Ratios")
        
        ratios_data = {
            'Ratio': [
                'Gross Profit Margin',
                'Operating Margin', 
                'Net Profit Margin',
                'Expense Ratio',
                'Interest Ratio',
                'Working Capital Turnover',
                'Revenue per Customer',
                'Profit per Customer'
            ],
            'Value': [
                f"{financial_metrics['gross_profit_margin']:.2f}%",
                f"{financial_metrics['operating_margin']:.2f}%",
                f"{financial_metrics['net_profit_margin']:.2f}%",
                f"{financial_metrics['expense_ratio']:.2f}%",
                f"{financial_metrics['interest_ratio']:.2f}%",
                f"{financial_metrics['working_capital_turnover']:.2f}x",
                format_currency(financial_metrics['revenue_per_customer']),
                format_currency(financial_metrics['profit_per_customer'])
            ],
            'Interpretation': [
                'Profit before expenses',
                'Profit after interest',
                'Final profit margin',
                'Expenses as % of revenue',
                'Interest as % of revenue',
                'Revenue efficiency',
                'Average customer value',
                'Average customer profit'
            ]
        }
        
        ratios_df = pd.DataFrame(ratios_data)
        st.dataframe(ratios_df, use_container_width=True)
        
        # Financial health assessment
        st.subheader("💊 Financial Health Assessment")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**Profitability:**")
            if financial_metrics['net_profit_margin'] > 20:
                st.success("✅ Excellent profitability")
            elif financial_metrics['net_profit_margin'] > 10:
                st.info("ℹ️ Good profitability")
            elif financial_metrics['net_profit_margin'] > 5:
                st.warning("⚠️ Moderate profitability")
            else:
                st.error("❌ Low profitability")
        
        with col2:
            st.write("**Cost Control:**")
            if financial_metrics['expense_ratio'] < 30:
                st.success("✅ Excellent cost control")
            elif financial_metrics['expense_ratio'] < 50:
                st.info("ℹ️ Good cost control")
            elif financial_metrics['expense_ratio'] < 70:
                st.warning("⚠️ Moderate cost control")
            else:
                st.error("❌ Poor cost control")
        
        with col3:
            st.write("**Efficiency:**")
            if financial_metrics['working_capital_turnover'] > 2:
                st.success("✅ High efficiency")
            elif financial_metrics['working_capital_turnover'] > 1:
                st.info("ℹ️ Moderate efficiency")
            else:
                st.warning("⚠️ Low efficiency")
    
    with tab5:
        st.subheader("Export Financial Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Export financial metrics
            financial_data = {
                'Financial Year': fy_display,
                'Total Revenue (₹)': financial_metrics['total_revenue'],
                'Total Expenses (₹)': financial_metrics['total_expenses'],
                'Total Interest (₹)': financial_metrics['total_interest'],
                'Operating Profit (₹)': financial_metrics['operating_profit'],
                'Net Profit (₹)': financial_metrics['net_profit'],
                'Gross Profit Margin (%)': financial_metrics['gross_profit_margin'],
                'Operating Margin (%)': financial_metrics['operating_margin'],
                'Net Profit Margin (%)': financial_metrics['net_profit_margin'],
                'Expense Ratio (%)': financial_metrics['expense_ratio'],
                'Interest Ratio (%)': financial_metrics['interest_ratio'],
                'Break-even Revenue (₹)': financial_metrics['break_even_revenue'],
                'Revenue per Customer (₹)': financial_metrics['revenue_per_customer'],
                'Profit per Customer (₹)': financial_metrics['profit_per_customer'],
                'Expense per Customer (₹)': financial_metrics['expense_per_customer'],
                'Working Capital Turnover': financial_metrics['working_capital_turnover']
            }
            
            financial_df = pd.DataFrame([financial_data])
            csv_data = financial_df.to_csv(index=False)
            
            st.download_button(
                label="💰 Download Financial Metrics (CSV)",
                data=csv_data,
                file_name=f"Financial_Analysis_{fy_display.replace('-', '_')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Export expense summary
            expense_data = {
                'Financial Year': fy_display,
                'Total Annual Expenses (₹)': total_expenses,
                'Expense Ratio (%)': financial_metrics['expense_ratio'],
                'Expense per Customer (₹)': financial_metrics['expense_per_customer'],
                'Break-even Revenue (₹)': financial_metrics['break_even_revenue']
            }
            
            expense_df = pd.DataFrame([expense_data])
            expense_csv = expense_df.to_csv(index=False)
            
            st.download_button(
                label="📊 Download Expense Summary (CSV)",
                data=expense_csv,
                file_name=f"Expense_Summary_{fy_display.replace('-', '_')}.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()
