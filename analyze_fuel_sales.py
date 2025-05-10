import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns

# Read the CSV files
statement_df = pd.read_csv('data/account_statement.csv')
ledger_df = pd.read_csv('data/account_ledger.csv')

# Convert date columns to datetime
statement_df['Date'] = pd.to_datetime(statement_df['Date'], format='%d-%m-%Y')
ledger_df['Date'] = pd.to_datetime(ledger_df['Date'], format='%d/%m/%Y')

# Calculate direct profit (₹3 per liter)
statement_df['Direct_Profit'] = statement_df['Qty.'] * 3

# Function to calculate daily interest
def calculate_daily_interest(amount, days):
    monthly_rate = 0.01  # 1% per month
    daily_rate = monthly_rate / 30  # Approximate daily rate
    return amount * daily_rate * days

# Function to calculate net profit for a transaction
def calculate_transaction_profit(row, payment_date):
    days_to_payment = (payment_date - row['Date']).days
    if days_to_payment <= 0:
        return row['Direct_Profit']
    
    interest_earned = calculate_daily_interest(row['Amount'], days_to_payment)
    bank_interest = calculate_daily_interest(row['Amount'], days_to_payment)
    return row['Direct_Profit'] + interest_earned - bank_interest

# Group transactions by 15-day periods
statement_df['Period'] = statement_df['Date'].dt.to_period('M')
statement_df['Half_Month'] = np.where(statement_df['Date'].dt.day <= 15, 'First', 'Second')

# Calculate period-wise statistics
period_stats = statement_df.groupby(['Period', 'Half_Month']).agg({
    'Amount': 'sum',
    'Direct_Profit': 'sum',
    'Qty.': 'sum'
}).reset_index()

# Calculate vehicle-wise statistics
vehicle_stats = statement_df.groupby('Vehicle No.').agg({
    'Amount': 'sum',
    'Direct_Profit': 'sum',
    'Qty.': 'sum'
}).reset_index()

# Create visualizations
plt.figure(figsize=(15, 10))

# 1. Monthly Sales Trend
plt.subplot(2, 2, 1)
monthly_sales = statement_df.groupby(statement_df['Date'].dt.to_period('M'))['Amount'].sum()
monthly_sales.plot(kind='bar')
plt.title('Monthly Sales Trend')
plt.xlabel('Month')
plt.ylabel('Total Sales (₹)')

# 2. Vehicle-wise Sales Distribution
plt.subplot(2, 2, 2)
vehicle_sales = statement_df.groupby('Vehicle No.')['Amount'].sum().sort_values(ascending=False).head(10)
vehicle_sales.plot(kind='bar')
plt.title('Top 10 Vehicles by Sales')
plt.xlabel('Vehicle Number')
plt.ylabel('Total Sales (₹)')

# 3. Product-wise Sales Distribution
plt.subplot(2, 2, 3)
product_sales = statement_df.groupby('Product Name')['Amount'].sum()
product_sales.plot(kind='pie', autopct='%1.1f%%')
plt.title('Sales Distribution by Product')

# 4. Daily Sales Trend
plt.subplot(2, 2, 4)
daily_sales = statement_df.groupby('Date')['Amount'].sum()
daily_sales.plot(kind='line')
plt.title('Daily Sales Trend')
plt.xlabel('Date')
plt.ylabel('Sales (₹)')

plt.tight_layout()
plt.savefig('sales_analysis.png')

# Print summary statistics
print("\nSummary Statistics:")
print("\nTotal Sales:", statement_df['Amount'].sum())
print("Total Direct Profit:", statement_df['Direct_Profit'].sum())
print("Total Quantity Sold:", statement_df['Qty.'].sum())

print("\nTop 5 Vehicles by Sales:")
print(vehicle_stats.sort_values('Amount', ascending=False).head())

print("\nPeriod-wise Statistics:")
print(period_stats)

# Enhanced Analysis
print("\n=== Enhanced Analysis ===")

# 1. Product-wise Analysis
product_analysis = statement_df.groupby('Product Name').agg({
    'Amount': ['sum', 'mean', 'count'],
    'Qty.': ['sum', 'mean'],
    'Direct_Profit': 'sum'
}).round(2)
print("\nProduct-wise Analysis:")
print(product_analysis)

# 2. Vehicle-wise Detailed Analysis
vehicle_detailed = statement_df.groupby('Vehicle No.').agg({
    'Amount': ['sum', 'mean', 'count'],
    'Qty.': ['sum', 'mean'],
    'Direct_Profit': 'sum'
}).round(2)
print("\nVehicle-wise Detailed Analysis (Top 5):")
print(vehicle_detailed.sort_values(('Amount', 'sum'), ascending=False).head())

# 3. Period-wise Detailed Analysis
period_detailed = statement_df.groupby(['Period', 'Half_Month']).agg({
    'Amount': ['sum', 'mean', 'count'],
    'Qty.': ['sum', 'mean'],
    'Direct_Profit': 'sum'
}).round(2)
print("\nPeriod-wise Detailed Analysis:")
print(period_detailed)

# 4. Daily Analysis
daily_analysis = statement_df.groupby('Date').agg({
    'Amount': ['sum', 'mean', 'count'],
    'Qty.': ['sum', 'mean'],
    'Direct_Profit': 'sum'
}).round(2)
print("\nDaily Analysis (First 5 days):")
print(daily_analysis.head())

# 5. Profit Analysis
print("\nProfit Analysis:")
print(f"Total Direct Profit: ₹{statement_df['Direct_Profit'].sum():.2f}")
print(f"Average Profit per Transaction: ₹{statement_df['Direct_Profit'].mean():.2f}")
print(f"Average Profit per Liter: ₹{statement_df['Direct_Profit'].sum() / statement_df['Qty.'].sum():.2f}")

# 6. Transaction Analysis
print("\nTransaction Analysis:")
print(f"Total Number of Transactions: {len(statement_df)}")
print(f"Average Transaction Amount: ₹{statement_df['Amount'].mean():.2f}")
print(f"Average Quantity per Transaction: {statement_df['Qty.'].mean():.2f} liters")

# 7. Vehicle Usage Analysis
print("\nVehicle Usage Analysis:")
vehicle_usage = statement_df.groupby('Vehicle No.').agg({
    'Date': ['count', 'min', 'max'],
    'Amount': 'sum',
    'Qty.': 'sum'
}).round(2)
print(vehicle_usage.sort_values(('Amount', 'sum'), ascending=False).head())

# 8. Product Price Analysis
print("\nProduct Price Analysis:")
price_analysis = statement_df.groupby('Product Name').agg({
    'Rate': ['mean', 'min', 'max'],
    'Amount': 'sum',
    'Qty.': 'sum'
}).round(2)
print(price_analysis)

# Save detailed analysis to CSV
detailed_analysis = pd.DataFrame({
    'Metric': [
        'Total Sales',
        'Total Direct Profit',
        'Total Quantity Sold',
        'Average Transaction Amount',
        'Average Quantity per Transaction',
        'Average Profit per Liter',
        'Total Number of Transactions'
    ],
    'Value': [
        statement_df['Amount'].sum(),
        statement_df['Direct_Profit'].sum(),
        statement_df['Qty.'].sum(),
        statement_df['Amount'].mean(),
        statement_df['Qty.'].mean(),
        statement_df['Direct_Profit'].sum() / statement_df['Qty.'].sum(),
        len(statement_df)
    ]
})
detailed_analysis.to_csv('detailed_analysis.csv', index=False)

# Create additional visualizations
plt.figure(figsize=(15, 10))

# 1. Profit Distribution
plt.subplot(2, 2, 1)
sns.histplot(data=statement_df, x='Direct_Profit', bins=30)
plt.title('Distribution of Direct Profit per Transaction')
plt.xlabel('Direct Profit (₹)')
plt.ylabel('Frequency')

# 2. Quantity vs Amount Scatter
plt.subplot(2, 2, 2)
sns.scatterplot(data=statement_df, x='Qty.', y='Amount', hue='Product Name')
plt.title('Quantity vs Amount by Product')
plt.xlabel('Quantity (Liters)')
plt.ylabel('Amount (₹)')

# 3. Daily Profit Trend
plt.subplot(2, 2, 3)
daily_profit = statement_df.groupby('Date')['Direct_Profit'].sum()
daily_profit.plot(kind='line')
plt.title('Daily Profit Trend')
plt.xlabel('Date')
plt.ylabel('Profit (₹)')

# 4. Product-wise Profit Distribution
plt.subplot(2, 2, 4)
sns.boxplot(data=statement_df, x='Product Name', y='Direct_Profit')
plt.title('Product-wise Profit Distribution')
plt.xlabel('Product')
plt.ylabel('Direct Profit (₹)')

plt.tight_layout()
plt.savefig('detailed_analysis.png') 