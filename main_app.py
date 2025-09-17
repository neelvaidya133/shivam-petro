import streamlit as st
import json
import os
import pandas as pd
import plotly.express as px

# Page config
st.set_page_config(
    page_title="Shivam Petroleum - Dashboard Suite",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_ledger_data():
    """Load ledger data from JSON file"""
    try:
        with open('ledger_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def load_customer_data():
    """Load customer data from JSON file"""
    try:
        with open('customer_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def main():
    st.title("⛽ Shivam Petroleum - Dashboard Suite")
    st.markdown("---")
    
    # Load data and show summary
    ledger_customers = load_ledger_data()
    customer_data = load_customer_data()
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Ledger Customers", len(ledger_customers))
    
    with col2:
        st.metric("Transaction Customers", len(customer_data))
    
    with col3:
        if ledger_customers:
            total_outstanding = sum(c['summary']['final_balance'] for c in ledger_customers)
            st.metric("Total Outstanding", f"₹{total_outstanding:,.0f}")
        else:
            st.metric("Total Outstanding", "N/A")
    
    with col4:
        if customer_data:
            total_transactions = sum(c['total_transactions'] for c in customer_data)
            st.metric("Total Transactions", total_transactions)
        else:
            st.metric("Total Transactions", "N/A")
    
    st.markdown("---")
    
    # Dashboard selection
    st.subheader("🚀 Select Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📊 Account Ledger")
        st.markdown("""
        - View customer account balances
        - Analyze transaction trends
        - Track outstanding amounts
        - Download transaction data
        """)
        
        if st.button("Open Ledger Dashboard", use_container_width=True):
            st.info("Please navigate to the Account Ledger page from the sidebar or use the direct link.")
            st.markdown("[📊 Account Ledger](pages/1_📊_Account_Ledger.py)")
    
    with col2:
        st.markdown("### 💰 Interest Calculator")
        st.markdown("""
        - Group transactions by date
        - Calculate compound interest
        - Daily interest analysis
        - Export interest reports
        """)
        
        if st.button("Open Interest Calculator", use_container_width=True):
            st.info("Please navigate to the Interest Calculator page from the sidebar or use the direct link.")
            st.markdown("[💰 Interest Calculator](pages/2_💰_Interest_Calculator.py)")
    
    with col3:
        st.markdown("### 📈 Customer Analysis")
        st.markdown("""
        - Analyze product sales
        - Calculate profits
        - View customer transactions
        - Generate reports
        """)
        
        if st.button("Open Analysis Dashboard", use_container_width=True):
            st.info("Please navigate to the Customer Analysis page from the sidebar or use the direct link.")
            st.markdown("[📈 Customer Analysis](pages/3_📈_Customer_Analysis.py)")
    
    st.markdown("---")
    
    # Advanced Analysis Section
    st.subheader("🚀 Advanced Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Comprehensive Analysis")
        st.markdown("""
        - Merged interest & sales data
        - Complete customer metrics
        - Profit vs interest analysis
        - Comprehensive reporting
        """)
        
        if st.button("Open Comprehensive Dashboard", use_container_width=True):
            st.info("Please navigate to the Comprehensive Analysis page from the sidebar or use the direct link.")
            st.markdown("[📊 Comprehensive Analysis](pages/4_📊_Comprehensive_Customer_Analysis.py)")
    
    with col2:
        st.markdown("### 🏢 Company Analysis")
        st.markdown("""
        - Company-wide metrics
        - Customer contribution analysis
        - Top & worst customers
        - Financial year analysis
        - Pie charts & visualizations
        """)
        
        if st.button("Open Company Dashboard", use_container_width=True):
            st.info("Please navigate to the Company Analysis page from the sidebar or use the direct link.")
            st.markdown("[🏢 Company Analysis](pages/5_🏢_Company_Analysis.py)")
    
    st.markdown("---")
    
    # Financial Intelligence Section
    st.subheader("💰 Financial Intelligence")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💰 Financial Intelligence")
        st.markdown("""
        - Expense tracking & analysis
        - Financial variance analysis
        - Profit & Loss statements
        - Break-even analysis
        - Financial health indicators
        - EBITDA-like calculations
        """)
        
        if st.button("Open Financial Dashboard", use_container_width=True):
            st.info("Please navigate to the Financial Intelligence page from the sidebar or use the direct link.")
            st.markdown("[💰 Financial Intelligence](pages/6_💰_Financial_Intelligence.py)")
    
    with col2:
        st.markdown("### 🤖 AI Assistant")
        st.markdown("""
        - AI-powered business insights
        - Natural language queries
        - Customer analysis
        - Financial explanations
        - Business recommendations
        - Interactive Q&A
        """)
        
        if st.button("Open AI Assistant", use_container_width=True):
            st.info("Please navigate to the AI Assistant page from the sidebar or use the direct link.")
            st.markdown("[🤖 AI Assistant](pages/7_🤖_AI_Assistant.py)")
    
    st.markdown("---")
    
    # Business Intelligence Section
    st.subheader("📊 Business Intelligence")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Business Intelligence")
        st.markdown("""
        - Customer segmentation
        - Risk assessment
        - Investment efficiency
        - Payment time analysis
        - Business rating system
        - Actionable insights
        """)
        
        if st.button("Open BI Dashboard", use_container_width=True):
            st.info("Please navigate to the Comprehensive Analysis page for business intelligence features.")
            st.markdown("[📊 Business Intelligence](pages/4_📊_Comprehensive_Customer_Analysis.py)")
    
    with col2:
        st.markdown("### 🎯 Quick AI Queries")
        st.markdown("""
        **Try asking the AI:**
        • "Show me Kush Structure's performance"
        • "What is investment efficiency?"
        • "Explain PE ratio"
        • "Give me business advice"
        • "What's my business overview?"
        """)
        
        if st.button("Ask AI Now", use_container_width=True):
            st.info("Please navigate to the AI Assistant page to start chatting with the AI.")
            st.markdown("[🤖 Start AI Chat](pages/7_🤖_AI_Assistant.py)")
    
    st.markdown("---")
    
    # Quick stats
    if ledger_customers:
        st.subheader("📈 Quick Statistics")
        
        # Top customers by outstanding amount
        outstanding_data = []
        for customer in ledger_customers:
            outstanding_data.append({
                'Customer': customer['customer_name'],
                'Outstanding': customer['summary']['final_balance'],
                'Transactions': customer['total_transactions']
            })
        
        outstanding_df = pd.DataFrame(outstanding_data)
        outstanding_df = outstanding_df.sort_values('Outstanding', ascending=False).head(5)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Top 5 Customers by Outstanding Amount:**")
            st.dataframe(outstanding_df, use_container_width=True)
        
        with col2:
            # Outstanding amount chart
            fig = px.bar(
                outstanding_df.head(5),
                x='Customer',
                y='Outstanding',
                title="Top 5 Outstanding Amounts"
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>🏢 <strong>Shivam Petroleum Dashboard Suite</strong></p>
        <p>Built with Streamlit & Python | Interest Calculator with Compound Interest & FIFO Payments</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
