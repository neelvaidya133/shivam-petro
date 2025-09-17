import streamlit as st
import sys
import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import google.generativeai as genai
import requests

# Add parent directory to path to import from main files
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Page config
st.set_page_config(
    page_title="Shivam Petroleum - AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# Configure Gemini API
def configure_gemini():
    """Configure Gemini API with API key"""
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        return True
    return False

# Initialize Gemini model
def get_gemini_model():
    """Get Gemini model instance"""
    try:
        return genai.GenerativeModel('gemini-2.0-flash')
    except Exception as e:
        st.error(f"Error initializing Gemini: {e}")
        return None

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
        return qty * profit_margins['others_per_liter']

def get_business_insights():
    """Get comprehensive business insights for AI responses"""
    ledger_customers = load_ledger_data()
    sales_customers = load_customer_data()
    
    # Calculate basic metrics
    total_outstanding = sum(c['summary']['final_balance'] for c in ledger_customers)
    total_customers = len(ledger_customers)
    avg_outstanding = total_outstanding / total_customers if total_customers > 0 else 0
    
    # Calculate sales metrics
    total_sales = 0
    total_profit = 0
    for sales_customer in sales_customers:
        for transaction in sales_customer['transactions']:
            total_sales += transaction['amount']
            total_profit += calculate_profit(
                transaction['product_name'], 
                transaction['qty'], 
                transaction['amount'], 
                {'diesel_per_liter': 3.0, 'petrol_per_liter': 2.0, 'oil_percentage': 15.0, 'others_per_liter': 1.0}
            )
    
    # Calculate comprehensive customer metrics
    customer_insights = []
    for ledger_customer in ledger_customers:
        customer_name = ledger_customer['customer_name']
        
        # Find corresponding sales data
        sales_customer = next((c for c in sales_customers if c['customer_name'].upper() == customer_name.upper()), None)
        
        # Calculate metrics
        closing_balance = ledger_customer['summary']['final_balance']
        total_transactions = ledger_customer['total_transactions']
        
        total_sales_amount = 0
        total_profit_amount = 0
        if sales_customer:
            for transaction in sales_customer['transactions']:
                total_sales_amount += transaction['amount']
                total_profit_amount += calculate_profit(
                    transaction['product_name'], 
                    transaction['qty'], 
                    transaction['amount'], 
                    {'diesel_per_liter': 3.0, 'petrol_per_liter': 2.0, 'oil_percentage': 15.0, 'others_per_liter': 1.0}
                )
        
        # Calculate investment efficiency
        investment_efficiency = (closing_balance / total_profit_amount * 100) if total_profit_amount > 0 else 0
        
        # Calculate risk score (simplified)
        risk_score = min(100, max(0, (closing_balance / avg_outstanding * 50) + (30 - total_transactions * 2)))
        
        # Calculate profitability score
        profitability_score = min(100, max(0, (total_profit_amount / total_sales_amount * 100) if total_sales_amount > 0 else 0))
        
        customer_insights.append({
            'customer_name': customer_name,
            'closing_balance': closing_balance,
            'total_sales': total_sales_amount,
            'total_profit': total_profit_amount,
            'total_transactions': total_transactions,
            'investment_efficiency': investment_efficiency,
            'risk_score': risk_score,
            'profitability_score': profitability_score,
            'avg_outstanding': avg_outstanding
        })
    
    return {
        'total_customers': total_customers,
        'total_outstanding': total_outstanding,
        'avg_outstanding': avg_outstanding,
        'total_sales': total_sales,
        'total_profit': total_profit,
        'ledger_customers': ledger_customers,
        'sales_customers': sales_customers,
        'customer_insights': customer_insights
    }

def analyze_customer_performance(customer_name, insights):
    """Analyze specific customer performance"""
    # Find customer in ledger data
    ledger_customer = next((c for c in insights['ledger_customers'] if c['customer_name'].upper() == customer_name.upper()), None)
    
    if not ledger_customer:
        return None
    
    # Find customer in sales data
    sales_customer = next((c for c in insights['sales_customers'] if c['customer_name'].upper() == customer_name.upper()), None)
    
    # Calculate metrics
    closing_balance = ledger_customer['summary']['final_balance']
    total_transactions = ledger_customer['total_transactions']
    
    total_sales = 0
    total_profit = 0
    if sales_customer:
        for transaction in sales_customer['transactions']:
            total_sales += transaction['amount']
            total_profit += calculate_profit(
                transaction['product_name'], 
                transaction['qty'], 
                transaction['amount'], 
                {'diesel_per_liter': 3.0, 'petrol_per_liter': 2.0, 'oil_percentage': 15.0, 'others_per_liter': 1.0}
            )
    
    # Calculate investment efficiency
    investment_efficiency = (closing_balance / total_profit * 100) if total_profit > 0 else 0
    
    return {
        'customer_name': ledger_customer['customer_name'],
        'closing_balance': closing_balance,
        'total_sales': total_sales,
        'total_profit': total_profit,
        'total_transactions': total_transactions,
        'investment_efficiency': investment_efficiency
    }

def get_ai_response(user_question, insights, progress_bar=None):
    """Generate AI response using Gemini API with business data context"""
    
    # Check if Gemini is configured
    if not configure_gemini():
        return """
        ⚠️ **Gemini API Not Configured**
        
        To use the advanced AI features, please:
        1. Get a Gemini API key from Google AI Studio
        2. Add it to your Streamlit secrets or environment variables
        3. Restart the application
        
        For now, here's a basic response to your question.
        """
    
    # Get Gemini model
    model = get_gemini_model()
    if not model:
        return "❌ Error: Could not initialize Gemini model. Please check your API key."
    
    # Prepare comprehensive business context for Gemini
    business_context = f"""
    You are an AI business analyst for Shivam Petroleum, a fuel distribution company. 
    
    CURRENT BUSINESS OVERVIEW:
    - Total Customers: {insights['total_customers']}
    - Total Outstanding: {format_currency(insights['total_outstanding'])}
    - Average Outstanding per Customer: {format_currency(insights['avg_outstanding'])}
    - Total Sales: {format_currency(insights['total_sales'])}
    - Total Profit: {format_currency(insights['total_profit'])}
    
    BUSINESS CONTEXT:
    - This is a fuel distribution business (diesel, petrol, oil)
    - All customers are credit customers (Udhar customers)
    - No interest is charged to customers
    - Company may take bank loans to buy fuel
    - Key metrics: Investment Efficiency, Risk Score, Profitability Score
    
    DETAILED CUSTOMER DATA:
    """
    
    # Add comprehensive customer data
    for customer in insights['customer_insights']:
        business_context += f"""
    CUSTOMER: {customer['customer_name']}
    - Outstanding Balance: ₹{customer['closing_balance']:,.0f}
    - Total Sales: ₹{customer['total_sales']:,.0f}
    - Total Profit: ₹{customer['total_profit']:,.0f}
    - Total Transactions: {customer['total_transactions']}
    - Investment Efficiency: ₹{customer['investment_efficiency']:.0f} per ₹100 profit
    - Risk Score: {customer['risk_score']:.1f}/100 (lower is better)
    - Profitability Score: {customer['profitability_score']:.1f}/100 (higher is better)
    - Risk Level: {'Low' if customer['risk_score'] <= 30 else 'Medium' if customer['risk_score'] <= 70 else 'High'}
    - Profitability Level: {'Excellent' if customer['profitability_score'] >= 80 else 'Good' if customer['profitability_score'] >= 60 else 'Average' if customer['profitability_score'] >= 40 else 'Poor'}
    """
    
    # Create the prompt for Gemini
    prompt = f"""
    {business_context}
    
    USER QUESTION: "{user_question}"
    
    INSTRUCTIONS:
    You are a business analyst with access to ALL customer data. When asked about specific customers (like "Kush Structure"), provide detailed analysis using the exact data provided above.
    
    RESPONSE GUIDELINES:
    1. Use the EXACT customer data provided above for specific customer questions
    2. For customer analysis, include: Outstanding Balance, Sales, Profit, Risk Score, Profitability Score, Investment Efficiency
    3. Compare customers against business averages when relevant
    4. Provide specific recommendations based on the data
    5. Use Indian business context and currency (₹)
    6. Format with clear sections and bullet points
    7. Be conversational but professional
    8. If customer not found, say so clearly
    9. For "how good is X customer" questions, provide comprehensive analysis
    10. Keep responses informative but concise (max 600 words)
    
    EXAMPLES OF GOOD RESPONSES:
    - "Kush Structure has ₹5.85L outstanding with ₹1.29L profit, making them a High Risk but Excellent Profitability customer"
    - "Compared to your average customer (₹4.25L outstanding), Kush Structure has 37% higher outstanding balance"
    - "Their investment efficiency of ₹452 per ₹100 profit means you need to invest ₹452 to make ₹100 profit from them"
    
    Respond as a helpful business analyst with full access to this data.
    """
    
    try:
        # Update progress bar
        if progress_bar:
            progress_bar.progress(0.3, text="🤖 AI is thinking...")
        
        # Generate response using Gemini
        response = model.generate_content(prompt)
        
        # Update progress bar
        if progress_bar:
            progress_bar.progress(0.8, text="📝 AI is writing response...")
        
        # Simulate typing delay for better UX
        import time
        time.sleep(0.5)
        
        # Update progress bar
        if progress_bar:
            progress_bar.progress(1.0, text="✅ Response ready!")
            time.sleep(0.3)
            progress_bar.empty()
        
        return response.text
    except Exception as e:
        if progress_bar:
            progress_bar.empty()
        return f"""
        ❌ **Error generating AI response**: {str(e)}
        
        **Fallback Response**: Please try rephrasing your question or check if the Gemini API is working properly.
        
        **Your Question**: {user_question}
        """

def main():
    st.title("🤖 Shivam Petroleum - AI Business Assistant")
    st.markdown("---")
    
    # Add custom CSS for better UI
    st.markdown("""
    <style>
    .ai-response {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .typing-indicator {
        display: inline-block;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background-color: #4CAF50;
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.1); opacity: 0.7; }
        100% { transform: scale(1); opacity: 1; }
    }
    
    .loading-text {
        color: #4CAF50;
        font-weight: bold;
        animation: fadeInOut 2s ease-in-out infinite;
    }
    
    @keyframes fadeInOut {
        0%, 100% { opacity: 0.5; }
        50% { opacity: 1; }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # API Configuration Section
    with st.expander("🔧 API Configuration", expanded=False):
        st.markdown("### Gemini API Setup")
        st.markdown("""
        To use the advanced AI features, you need to configure the Gemini API:
        
        1. **Get API Key**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
        2. **Add to Secrets**: Add your API key to Streamlit secrets or environment variables
        3. **Restart App**: Restart the Streamlit application
        
        **Method 1 - Streamlit Secrets** (Recommended):
        Create `.streamlit/secrets.toml` file:
        ```toml
        GEMINI_API_KEY = "your_api_key_here"
        ```
        
        **Method 2 - Environment Variables**:
        Set `GEMINI_API_KEY` environment variable
        """)
        
        # Manual API key input (for testing)
        manual_key = st.text_input("Or enter API key manually (for testing only):", type="password")
        if manual_key:
            os.environ["GEMINI_API_KEY"] = manual_key
            st.success("✅ API key set! Please refresh the page.")
    
    # Load business insights
    insights = get_business_insights()
    
    # Sidebar with quick stats
    st.sidebar.header("📊 Quick Business Stats")
    st.sidebar.metric("Total Customers", insights['total_customers'])
    st.sidebar.metric("Total Outstanding", format_currency(insights['total_outstanding']))
    st.sidebar.metric("Total Sales", format_currency(insights['total_sales']))
    st.sidebar.metric("Total Profit", format_currency(insights['total_profit']))
    
    # Main chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 Ask Me Anything About Your Business")
        
        # Initialize chat history
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        # Display chat history
        for i, (question, answer) in enumerate(st.session_state.chat_history):
            with st.expander(f"Q{i+1}: {question[:50]}..." if len(question) > 50 else f"Q{i+1}: {question}", expanded=False):
                st.write("**Question:**", question)
                st.write("**Answer:**", answer)
        
        # Chat form
        with st.form("chat_form", clear_on_submit=True):
            user_question = st.text_input(
                "Type your question here:",
                placeholder="e.g., 'Show me Kush Structure's performance' or 'What is investment efficiency?'",
                key="chat_input"
            )
            
            submitted = st.form_submit_button("Ask AI Assistant", type="primary")
            
            if submitted and user_question:
                # Create loading indicators
                with st.spinner("🤖 AI is analyzing your question..."):
                    # Progress bar
                    progress_bar = st.progress(0, text="🚀 Starting AI analysis...")
                    
                    # Get AI response
                    ai_response = get_ai_response(user_question, insights, progress_bar)
                    
                    # Add to chat history
                    st.session_state.chat_history.append((user_question, ai_response))
                    st.session_state.latest_response = (user_question, ai_response)
                
                # Display response with animation
                st.markdown("---")
                st.markdown("### 🤖 AI Response:")
                
                # Animate the response appearance
                with st.container():
                    # Create a typing effect container
                    response_container = st.empty()
                    response_container.markdown(ai_response)
                    
                    # Success message with animation
                    st.success("✅ Response generated successfully!")
                    
                    # Add a small delay for better UX
                    import time
                    time.sleep(0.2)
        
        # Display latest response if there's one
        if hasattr(st.session_state, 'latest_response') and st.session_state.latest_response:
            latest_question, latest_answer = st.session_state.latest_response
            st.markdown("---")
            st.markdown("### 🤖 Latest AI Response:")
            st.markdown(f"**Question:** {latest_question}")
            st.markdown(f"**Answer:** {latest_answer}")
    
    with col2:
        st.subheader("🎯 Quick Actions")
        
        # Quick question buttons
        if st.button("📊 Business Overview", use_container_width=True):
            question = "Show me complete business overview with all metrics"
            with st.spinner("🤖 Analyzing business data..."):
                progress_bar = st.progress(0, text="📊 Processing business metrics...")
                ai_response = get_ai_response(question, insights, progress_bar)
                st.session_state.chat_history.append((question, ai_response))
                st.session_state.latest_response = (question, ai_response)
        
        if st.button("👤 How Good is Kush Structure?", use_container_width=True):
            question = "How good is Kush Structure? Analyze their performance, risk, and profitability"
            with st.spinner("🤖 Analyzing Kush Structure..."):
                progress_bar = st.progress(0, text="👤 Evaluating customer performance...")
                ai_response = get_ai_response(question, insights, progress_bar)
                st.session_state.chat_history.append((question, ai_response))
                st.session_state.latest_response = (question, ai_response)
        
        if st.button("🏆 Best Customers", use_container_width=True):
            question = "Who are my best customers? Rank them by profitability and low risk"
            with st.spinner("🤖 Ranking customers..."):
                progress_bar = st.progress(0, text="🏆 Identifying top performers...")
                ai_response = get_ai_response(question, insights, progress_bar)
                st.session_state.chat_history.append((question, ai_response))
                st.session_state.latest_response = (question, ai_response)
        
        if st.button("⚠️ Problem Customers", use_container_width=True):
            question = "Which customers are problematic? Show high risk and low profitability customers"
            with st.spinner("🤖 Identifying problem customers..."):
                progress_bar = st.progress(0, text="⚠️ Analyzing risk factors...")
                ai_response = get_ai_response(question, insights, progress_bar)
                st.session_state.chat_history.append((question, ai_response))
                st.session_state.latest_response = (question, ai_response)
        
        if st.button("💰 Investment Efficiency", use_container_width=True):
            question = "Explain investment efficiency with examples from my customers"
            with st.spinner("🤖 Calculating efficiency metrics..."):
                progress_bar = st.progress(0, text="💰 Analyzing investment patterns...")
                ai_response = get_ai_response(question, insights, progress_bar)
                st.session_state.chat_history.append((question, ai_response))
                st.session_state.latest_response = (question, ai_response)
        
        if st.button("💡 Business Strategy", use_container_width=True):
            question = "Give me specific business strategy recommendations based on my customer data"
            with st.spinner("🤖 Developing strategy recommendations..."):
                progress_bar = st.progress(0, text="💡 Crafting business insights...")
                ai_response = get_ai_response(question, insights, progress_bar)
                st.session_state.chat_history.append((question, ai_response))
                st.session_state.latest_response = (question, ai_response)
        
        st.markdown("---")
        st.subheader("🔍 Customer Search")
        
        # Customer search dropdown
        customer_names = [c['customer_name'] for c in insights['customer_insights']]
        selected_customer = st.selectbox(
            "Select a customer to analyze:",
            ["Select a customer..."] + customer_names,
            key="customer_selector"
        )
        
        if selected_customer != "Select a customer...":
            if st.button(f"Analyze {selected_customer}", use_container_width=True):
                question = f"How good is {selected_customer}? Provide detailed analysis of their performance, risk, and profitability"
                with st.spinner(f"🤖 Analyzing {selected_customer}..."):
                    progress_bar = st.progress(0, text=f"👤 Evaluating {selected_customer}...")
                    ai_response = get_ai_response(question, insights, progress_bar)
                    st.session_state.chat_history.append((question, ai_response))
                    st.session_state.latest_response = (question, ai_response)
        
        st.markdown("---")
        st.subheader("🧹 Chat Controls")
        
        if st.button("Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>🤖 <strong>AI Business Assistant</strong> | Ask questions about your business data and get intelligent insights</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
