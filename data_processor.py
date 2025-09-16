import json
import pandas as pd
from datetime import datetime

def process_customer_data(tsv_file_path):
    """
    Process the TSV file and convert it to structured JSON format
    """
    print("Reading TSV file...")
    
    # Read the TSV file
    with open(tsv_file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    customers = []
    current_customer = None
    current_transactions = []
    
    print("Processing customer data...")
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Split by tab
        parts = line.split('\t')
        
        # Check if this is a customer header line
        if len(parts) >= 2 and parts[0].startswith('To, '):
            # Save previous customer if exists
            if current_customer:
                current_customer['transactions'] = current_transactions
                current_customer['total_transactions'] = len(current_transactions)
                customers.append(current_customer)
            
            # Start new customer
            customer_name = parts[0].replace('To, ', '').strip()
            statement_date = parts[-1].strip() if len(parts) > 1 else ""
            
            current_customer = {
                "customer_name": customer_name,
                "statement_date": statement_date,
                "transactions": [],
                "total_transactions": 0
            }
            current_transactions = []
            
        # Check if this is a transaction line (has Product Name, Date, etc.)
        elif (len(parts) >= 6 and 
              parts[0] and 
              parts[1] and 
              parts[0] not in ['Product Name', 'Date', 'Vehicle No.', 'Qty.', 'Rate', 'Amount'] and
              not parts[0].startswith('To, ')):
            
            try:
                # Parse transaction data
                product_name = parts[0].strip()
                date = parts[1].strip()
                vehicle_no = parts[2].strip()
                qty = parts[3].strip()
                rate = parts[4].strip()
                amount = parts[5].strip()
                
                # Convert numeric fields
                try:
                    qty_num = float(qty) if qty else 0
                except:
                    qty_num = 0
                    
                try:
                    rate_num = float(rate) if rate else 0
                except:
                    rate_num = 0
                    
                try:
                    amount_num = float(amount) if amount else 0
                except:
                    amount_num = 0
                
                transaction = {
                    "product_name": product_name,
                    "date": date,
                    "vehicle_no": vehicle_no,
                    "qty": qty_num,
                    "rate": rate_num,
                    "amount": amount_num
                }
                
                if current_customer:
                    current_transactions.append(transaction)
                    
            except Exception as e:
                print(f"Error processing line {i+1}: {e}")
                continue
    
    # Don't forget the last customer
    if current_customer:
        current_customer['transactions'] = current_transactions
        current_customer['total_transactions'] = len(current_transactions)
        customers.append(current_customer)
    
    print(f"Processed {len(customers)} customers")
    
    # Calculate additional statistics for each customer
    for customer in customers:
        transactions = customer['transactions']
        if transactions:
            total_amount = sum(t['amount'] for t in transactions)
            total_qty = sum(t['qty'] for t in transactions)
            
            # Get unique products
            products = list(set(t['product_name'] for t in transactions))
            
            # Get unique vehicles
            vehicles = list(set(t['vehicle_no'] for t in transactions if t['vehicle_no']))
            
            customer['summary'] = {
                "total_amount": total_amount,
                "total_qty": total_qty,
                "unique_products": len(products),
                "unique_vehicles": len(vehicles),
                "products": products,
                "vehicles": vehicles
            }
    
    return customers

def save_to_json(customers, output_file):
    """Save customers data to JSON file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(customers, f, indent=2, ensure_ascii=False)
    print(f"Data saved to {output_file}")

def main():
    # Process the TSV file
    tsv_file = "Shivam Petroleum-Account Statement_301299-301299.xlsx - Account Statement.tsv"
    customers = process_customer_data(tsv_file)
    
    # Save to JSON
    save_to_json(customers, "customer_data.json")
    
    # Print summary
    print("\n=== CUSTOMER SUMMARY ===")
    for customer in customers:
        print(f"Customer: {customer['customer_name']}")
        print(f"  Transactions: {customer['total_transactions']}")
        if 'summary' in customer:
            print(f"  Total Amount: ₹{customer['summary']['total_amount']:,.2f}")
            print(f"  Total Quantity: {customer['summary']['total_qty']:,.2f}")
        print()

if __name__ == "__main__":
    main()
