import streamlit as st

def main():
    st.set_page_config(
        page_title="Shivam Petroleum - Dashboard Launcher",
        page_icon="⛽",
        layout="centered"
    )
    
    st.title("⛽ Shivam Petroleum - Dashboard Launcher")
    st.markdown("---")
    
    st.subheader("Choose your dashboard:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📊 Account Ledger Dashboard")
        st.markdown("""
        - View customer account balances
        - Analyze transaction trends
        - Track outstanding amounts
        - Download transaction data
        """)
        
        if st.button("🚀 Launch Ledger Dashboard", use_container_width=True):
            st.markdown("**Ledger Dashboard:** `streamlit run ledger_app.py`")
    
    with col2:
        st.markdown("### 💰 Interest Calculator Dashboard")
        st.markdown("""
        - Group transactions by date
        - Calculate interest on balances
        - Daily interest analysis
        - Export interest reports
        """)
        
        if st.button("🚀 Launch Interest Calculator", use_container_width=True):
            st.markdown("**Interest Calculator:** `streamlit run interest_calculator_app.py`")
    
    with col3:
        st.markdown("### 📈 Customer Analysis Dashboard")
        st.markdown("""
        - Analyze product sales
        - Calculate profits
        - View customer transactions
        - Generate reports
        """)
        
        if st.button("🚀 Launch Analysis Dashboard", use_container_width=True):
            st.markdown("**Analysis Dashboard:** `streamlit run streamlit_app.py`")
    
    st.markdown("---")
    
    st.subheader("📁 Available Data Files:")
    
    import os
    data_files = []
    if os.path.exists("ledger_data.json"):
        data_files.append("✅ ledger_data.json (Account Ledger - 13 customers)")
    if os.path.exists("customer_data.json"):
        data_files.append("✅ customer_data.json (Customer Transactions)")
    
    for file in data_files:
        st.markdown(f"- {file}")
    
    st.markdown("---")
    
    st.subheader("🛠️ Quick Commands:")
    
    st.code("""
# Run Interest Calculator (NEW!)
streamlit run interest_calculator_app.py

# Run Ledger Dashboard
streamlit run ledger_app.py

# Run Analysis Dashboard  
streamlit run streamlit_app.py

# Process new ledger data
python ledger_processor.py
    """, language="bash")
    
    st.markdown("---")
    
    st.info("""
    💡 **Interest Calculator Features:**
    - Groups same-date transactions into single entries
    - Calculates daily interest on outstanding balances
    - Configurable interest rates
    - Date range filtering
    - Export capabilities for interest reports
    """)

if __name__ == "__main__":
    main()
