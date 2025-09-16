import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Page config
st.set_page_config(
    page_title="Shivam Petroleum - Account Ledger Dashboard",
    page_icon="📊",
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

def get_balance_color(balance, balance_type):
    """Get color based on balance type and amount"""
    if balance_type == "Dr" and balance > 0:
        return "🔴"  # Red for debit (customer owes)
    elif balance_type == "Cr" and balance > 0:
        return "🟢"  # Green for credit (company owes)
    else:
        return "⚪"  # White for zero balance

def create_balance_trend_chart(customer_data):
    """Create balance trend chart for a customer"""
    df = pd.DataFrame(customer_data['transactions'])
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    fig = go.Figure()
    
    # Add balance line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['balance'],
        mode='lines+markers',
        name='Balance',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=6)
    ))
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    fig.update_layout(
        title=f"Balance Trend - {customer_data['customer_name']}",
        xaxis_title="Date",
        yaxis_title="Balance (₹)",
        hovermode='x unified',
        height=400
    )
    
    # Format y-axis as currency
    fig.update_yaxes(tickformat='₹,.0f')
    
    return fig

def create_transaction_analysis(customer_data):
    """Create transaction analysis charts"""
    df = pd.DataFrame(customer_data['transactions'])
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M')
    
    # Monthly transaction amounts
    monthly_debits = df.groupby('month')['debit'].sum().reset_index()
    monthly_credits = df.groupby('month')['credit'].sum().reset_index()
    monthly_debits['month_str'] = monthly_debits['month'].astype(str)
    monthly_credits['month_str'] = monthly_credits['month'].astype(str)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=monthly_debits['month_str'],
        y=monthly_debits['debit'],
        name='Debits',
        marker_color='#ff7f0e'
    ))
    
    fig.add_trace(go.Bar(
        x=monthly_credits['month_str'],
        y=monthly_credits['credit'],
        name='Credits',
        marker_color='#2ca02c'
    ))
    
    fig.update_layout(
        title="Monthly Transaction Analysis",
        xaxis_title="Month",
        yaxis_title="Amount (₹)",
        barmode='group',
        height=400
    )
    
    fig.update_yaxes(tickformat='₹,.0f')
    
    return fig

def main():
    st.title("📊 Shivam Petroleum - Account Ledger Dashboard")
    st.markdown("---")
    
    # Load data
    customers = load_ledger_data()
    
    # Sidebar
    st.sidebar.header("🔍 Analysis Options")
    
    # Customer selection
    customer_options = [f"{c['customer_id']} - {c['customer_name']}" for c in customers]
    selected_customer_idx = st.sidebar.selectbox(
        "Select Customer:",
        range(len(customer_options)),
        format_func=lambda x: customer_options[x]
    )
    
    selected_customer = customers[selected_customer_idx]
    
    # Analysis type selection
    analysis_type = st.sidebar.selectbox(
        "Analysis Type:",
        ["Customer Overview", "Transaction Details", "Balance Analysis", "All Customers Summary"]
    )
    
    # Main content
    if analysis_type == "Customer Overview":
        display_customer_overview(selected_customer)
    elif analysis_type == "Transaction Details":
        display_transaction_details(selected_customer)
    elif analysis_type == "Balance Analysis":
        display_balance_analysis(selected_customer)
    elif analysis_type == "All Customers Summary":
        display_all_customers_summary(customers)

def display_customer_overview(customer):
    """Display customer overview"""
    st.header(f"👤 {customer['customer_name']} (ID: {customer['customer_id']})")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Transactions",
            customer['total_transactions'],
            help="Total number of transactions"
        )
    
    with col2:
        opening_balance = customer['opening_balance']['amount']
        opening_type = customer['opening_balance']['type']
        st.metric(
            "Opening Balance",
            f"{format_currency(opening_balance)} {opening_type}",
            help="Balance at the start of the period"
        )
    
    with col3:
        final_balance = customer['summary']['final_balance']
        final_type = customer['summary']['final_balance_type']
        st.metric(
            "Final Balance",
            f"{format_currency(final_balance)} {final_type}",
            help="Current outstanding balance"
        )
    
    with col4:
        net_amount = customer['summary']['total_debits'] - customer['summary']['total_credits']
        status = "Customer owes" if net_amount > 0 else "Company owes" if net_amount < 0 else "Settled"
        st.metric(
            "Net Position",
            f"{format_currency(abs(net_amount))}",
            delta=status,
            help="Net amount after all transactions"
        )
    
    # Summary cards
    st.subheader("📈 Transaction Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"**Total Debits:** {format_currency(customer['summary']['total_debits'])}")
    
    with col2:
        st.success(f"**Total Credits:** {format_currency(customer['summary']['total_credits'])}")
    
    with col3:
        balance_icon = get_balance_color(customer['summary']['final_balance'], customer['summary']['final_balance_type'])
        st.warning(f"**Final Balance:** {balance_icon} {format_currency(customer['summary']['final_balance'])} {customer['summary']['final_balance_type']}")
    
    # Balance trend chart
    st.subheader("📊 Balance Trend")
    balance_chart = create_balance_trend_chart(customer)
    st.plotly_chart(balance_chart, width='stretch')
    
    # Transaction analysis
    st.subheader("📅 Monthly Transaction Analysis")
    transaction_chart = create_transaction_analysis(customer)
    st.plotly_chart(transaction_chart, width='stretch')

def display_transaction_details(customer):
    """Display detailed transaction table"""
    st.header(f"📋 Transaction Details - {customer['customer_name']}")
    
    # Convert to DataFrame
    df = pd.DataFrame(customer['transactions'])
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date', ascending=False)
    
    # Format columns
    df['debit_formatted'] = df['debit'].apply(lambda x: f"₹{x:,.0f}" if x > 0 else "")
    df['credit_formatted'] = df['credit'].apply(lambda x: f"₹{x:,.0f}" if x > 0 else "")
    df['balance_formatted'] = df.apply(lambda x: f"₹{x['balance']:,.0f} {x['balance_type']}", axis=1)
    
    # Display table
    display_df = df[['date', 'debit_formatted', 'credit_formatted', 'balance_formatted']].copy()
    display_df.columns = ['Date', 'Debit', 'Credit', 'Balance']
    
    st.dataframe(
        display_df,
        width='stretch',
        height=400
    )
    
    # Download option
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download Transaction Data as CSV",
        data=csv,
        file_name=f"{customer['customer_name']}_transactions.csv",
        mime="text/csv"
    )

def display_balance_analysis(customer):
    """Display balance analysis"""
    st.header(f"💰 Balance Analysis - {customer['customer_name']}")
    
    df = pd.DataFrame(customer['transactions'])
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Balance distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Balance Distribution")
        
        # Create balance categories
        df['balance_category'] = pd.cut(
            df['balance'],
            bins=[-np.inf, -100000, 0, 100000, 500000, np.inf],
            labels=['High Credit', 'Credit', 'Zero', 'Low Debit', 'High Debit']
        )
        
        balance_counts = df['balance_category'].value_counts()
        
        fig = px.pie(
            values=balance_counts.values,
            names=balance_counts.index,
            title="Balance Distribution"
        )
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        st.subheader("Transaction Frequency")
        
        # Daily transaction counts
        daily_counts = df.groupby(df['date'].dt.date).size()
        
        fig = px.bar(
            x=daily_counts.index,
            y=daily_counts.values,
            title="Daily Transaction Count",
            labels={'x': 'Date', 'y': 'Transaction Count'}
        )
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, width='stretch')
    
    # Balance statistics
    st.subheader("📊 Balance Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Average Balance", format_currency(df['balance'].mean()))
    
    with col2:
        st.metric("Max Balance", format_currency(df['balance'].max()))
    
    with col3:
        st.metric("Min Balance", format_currency(df['balance'].min()))
    
    with col4:
        st.metric("Balance Std Dev", format_currency(df['balance'].std()))

def display_all_customers_summary(customers):
    """Display summary of all customers"""
    st.header("🏢 All Customers Summary")
    
    # Create summary DataFrame
    summary_data = []
    for customer in customers:
        summary_data.append({
            'Customer ID': customer['customer_id'],
            'Customer Name': customer['customer_name'],
            'Transactions': customer['total_transactions'],
            'Total Debits': customer['summary']['total_debits'],
            'Total Credits': customer['summary']['total_credits'],
            'Final Balance': customer['summary']['final_balance'],
            'Balance Type': customer['summary']['final_balance_type'],
            'Net Amount': customer['summary']['total_debits'] - customer['summary']['total_credits']
        })
    
    df = pd.DataFrame(summary_data)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Customers", len(customers))
    
    with col2:
        total_debits = df['Total Debits'].sum()
        st.metric("Total Debits", format_currency(total_debits))
    
    with col3:
        total_credits = df['Total Credits'].sum()
        st.metric("Total Credits", format_currency(total_credits))
    
    with col4:
        net_outstanding = df['Net Amount'].sum()
        st.metric("Net Outstanding", format_currency(net_outstanding))
    
    # Top customers by outstanding amount
    st.subheader("🔝 Top Customers by Outstanding Amount")
    
    df_sorted = df.sort_values('Net Amount', ascending=False)
    df_sorted['Outstanding'] = df_sorted['Net Amount'].apply(lambda x: f"₹{x:,.0f}")
    df_sorted['Status'] = df_sorted['Net Amount'].apply(
        lambda x: "Customer owes" if x > 0 else "Company owes" if x < 0 else "Settled"
    )
    
    display_df = df_sorted[['Customer Name', 'Transactions', 'Outstanding', 'Status']].head(10)
    st.dataframe(display_df, width='stretch')
    
    # Outstanding amount chart
    st.subheader("📊 Outstanding Amounts by Customer")
    
    fig = px.bar(
        df_sorted.head(15),
        x='Customer Name',
        y='Net Amount',
        title="Outstanding Amounts (Top 15 Customers)",
        color='Net Amount',
        color_continuous_scale='RdYlGn_r'
    )
    fig.update_xaxes(tickangle=45)
    fig.update_yaxes(tickformat='₹,.0f')
    st.plotly_chart(fig, width='stretch')
    
    # Download summary
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download All Customers Summary as CSV",
        data=csv,
        file_name="all_customers_summary.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    main()
