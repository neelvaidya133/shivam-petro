import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Shivam Petroleum - Customer Analysis",
    page_icon="⛽",
    layout="wide"
)

@st.cache_data
def load_customer_data():
    """Load customer data from JSON file"""
    with open('customer_data.json', 'r', encoding='utf-8') as f:
        return json.load(f)

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

def main():
    st.title("⛽ Shivam Petroleum - Customer Analysis Dashboard")
    st.markdown("---")
    
    # Load data
    customers = load_customer_data()
    
    # Sidebar for customer selection and profit settings
    st.sidebar.header("📊 Analysis Options")
    
    # Profit margin settings
    st.sidebar.subheader("💰 Profit Margins")
    profit_margins = {
        'diesel_per_liter': st.sidebar.number_input(
            "Diesel (₹ per liter):",
            min_value=0.0,
            max_value=50.0,
            value=3.0,
            step=0.1,
            help="Profit margin per liter of diesel"
        ),
        'petrol_per_liter': st.sidebar.number_input(
            "Petrol (₹ per liter):",
            min_value=0.0,
            max_value=50.0,
            value=2.0,
            step=0.1,
            help="Profit margin per liter of petrol"
        ),
        'oil_percentage': st.sidebar.number_input(
            "Oil (percentage):",
            min_value=0.0,
            max_value=100.0,
            value=15.0,
            step=0.1,
            help="Profit margin as percentage for oil products"
        ),
        'others_per_liter': st.sidebar.number_input(
            "Others (₹ per liter):",
            min_value=0.0,
            max_value=50.0,
            value=1.0,
            step=0.1,
            help="Profit margin per liter for other products"
        )
    }
    
    st.sidebar.markdown("---")
    
    # Customer selection
    customer_names = [customer['customer_name'] for customer in customers]
    selected_customer = st.sidebar.selectbox(
        "Select Customer:",
        customer_names,
        index=0
    )
    
    # Get selected customer data
    selected_customer_data = next(
        (c for c in customers if c['customer_name'] == selected_customer), 
        None
    )
    
    if selected_customer_data:
        # Customer Overview
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Total Transactions",
                selected_customer_data['total_transactions']
            )
        
        with col2:
            st.metric(
                "Total Amount",
                f"₹{selected_customer_data['summary']['total_amount']:,.2f}"
            )
        
        with col3:
            st.metric(
                "Total Quantity",
                f"{selected_customer_data['summary']['total_qty']:,.2f} L"
            )
        
        with col4:
            st.metric(
                "Unique Vehicles",
                selected_customer_data['summary']['unique_vehicles']
            )
        
        with col5:
            # Calculate total profit for this customer
            total_profit = sum(
                calculate_profit(transaction['product_name'], transaction['qty'], transaction['amount'], profit_margins)
                for transaction in selected_customer_data['transactions']
            )
            st.metric(
                "Total Profit",
                f"₹{total_profit:,.2f}"
            )
        
        st.markdown("---")
        
        # Convert transactions to DataFrame for analysis
        transactions_df = pd.DataFrame(selected_customer_data['transactions'])
        transactions_df['date'] = pd.to_datetime(transactions_df['date'], format='%d/%m/%Y')
        
        # Add profit column
        transactions_df['profit'] = transactions_df.apply(
            lambda row: calculate_profit(row['product_name'], row['qty'], row['amount'], profit_margins), 
            axis=1
        )
        
        # Tabs for different analyses
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Transactions", "🚛 Vehicles", "⛽ Products", "📊 Summary"])
        
        with tab1:
            st.subheader("Transaction History")
            
            # Date range filter
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=transactions_df['date'].min())
            with col2:
                end_date = st.date_input("End Date", value=transactions_df['date'].max())
            
            # Filter data
            filtered_df = transactions_df[
                (transactions_df['date'].dt.date >= start_date) & 
                (transactions_df['date'].dt.date <= end_date)
            ]
            
            # Display transactions table
            st.dataframe(
                filtered_df[['date', 'product_name', 'vehicle_no', 'qty', 'rate', 'amount', 'profit']],
                use_container_width=True
            )
            
            # Amount and Profit trend charts
            col1, col2 = st.columns(2)
            
            with col1:
                daily_amounts = filtered_df.groupby('date')['amount'].sum().reset_index()
                fig = px.line(daily_amounts, x='date', y='amount', title='Daily Amount Trend')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                daily_profits = filtered_df.groupby('date')['profit'].sum().reset_index()
                fig = px.line(daily_profits, x='date', y='profit', title='Daily Profit Trend')
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.subheader("Vehicle Analysis")
            
            # Vehicle summary
            vehicle_summary = filtered_df.groupby('vehicle_no').agg({
                'amount': 'sum',
                'qty': 'sum',
                'profit': 'sum',
                'date': 'count'
            }).rename(columns={'date': 'transaction_count'}).reset_index()
            
            vehicle_summary = vehicle_summary.sort_values('amount', ascending=False)
            
            st.dataframe(vehicle_summary, use_container_width=True)
            
            # Vehicle charts
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(vehicle_summary.head(10), x='vehicle_no', y='amount', 
                            title='Top 10 Vehicles by Amount')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(vehicle_summary.head(10), x='vehicle_no', y='profit', 
                            title='Top 10 Vehicles by Profit')
                st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            st.subheader("Product Analysis")
            
            # Product summary
            product_summary = filtered_df.groupby('product_name').agg({
                'amount': 'sum',
                'qty': 'sum',
                'profit': 'sum',
                'date': 'count'
            }).rename(columns={'date': 'transaction_count'}).reset_index()
            
            product_summary = product_summary.sort_values('amount', ascending=False)
            
            st.dataframe(product_summary, use_container_width=True)
            
            # Product charts
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(product_summary, values='amount', names='product_name', 
                            title='Amount Distribution by Product')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.pie(product_summary, values='profit', names='product_name', 
                            title='Profit Distribution by Product')
                st.plotly_chart(fig, use_container_width=True)
        
        with tab4:
            st.subheader("Overall Summary")
            
            # All customers summary
            all_customers_summary = []
            for customer in customers:
                # Calculate total profit for this customer
                total_profit = sum(
                    calculate_profit(transaction['product_name'], transaction['qty'], transaction['amount'], profit_margins)
                    for transaction in customer['transactions']
                )
                
                all_customers_summary.append({
                    'Customer': customer['customer_name'],
                    'Transactions': customer['total_transactions'],
                    'Total Amount': customer['summary']['total_amount'],
                    'Total Quantity': customer['summary']['total_qty'],
                    'Total Profit': total_profit,
                    'Unique Vehicles': customer['summary']['unique_vehicles']
                })
            
            summary_df = pd.DataFrame(all_customers_summary)
            summary_df = summary_df.sort_values('Total Amount', ascending=False)
            
            st.dataframe(summary_df, use_container_width=True)
            
            # Top customers charts
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(summary_df.head(10), x='Customer', y='Total Amount',
                            title='Top 10 Customers by Total Amount')
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(summary_df.head(10), x='Customer', y='Total Profit',
                            title='Top 10 Customers by Total Profit')
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
