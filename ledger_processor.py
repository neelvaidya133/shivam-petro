import json
import re
from datetime import datetime
from typing import List, Dict, Any

def parse_indian_number(number_str: str) -> float:
    """
    Convert Indian number format (e.g., "11,32,357.00") to float
    """
    if not number_str or number_str.strip() == "":
        return 0.0
    
    # Remove commas and convert to float
    try:
        cleaned = number_str.replace(',', '').strip()
        return float(cleaned)
    except ValueError:
        return 0.0

def parse_date(date_str: str) -> str:
    """
    Convert DD/MM/YYYY to YYYY-MM-DD format
    """
    try:
        if not date_str or date_str.strip() == "":
            return ""
        
        # Parse DD/MM/YYYY format
        date_obj = datetime.strptime(date_str.strip(), '%d/%m/%Y')
        return date_obj.strftime('%Y-%m-%d')
    except ValueError:
        return date_str

def extract_balance_info(balance_str: str) -> tuple:
    """
    Extract balance amount and type (Dr/Cr) from balance string
    """
    if not balance_str or balance_str.strip() == "":
        return 0.0, ""
    
    balance_str = balance_str.strip()
    
    # Check for Dr or Cr at the end
    if balance_str.endswith(' Dr'):
        amount = parse_indian_number(balance_str[:-3])
        return amount, "Dr"
    elif balance_str.endswith(' Cr'):
        amount = parse_indian_number(balance_str[:-3])
        return amount, "Cr"
    else:
        # Just a number without Dr/Cr
        amount = parse_indian_number(balance_str)
        return amount, ""

def process_ledger_data(tsv_file_path: str) -> List[Dict[str, Any]]:
    """
    Process the Account Ledger TSV file and convert it to structured JSON format
    """
    print("Reading Account Ledger TSV file...")
    
    with open(tsv_file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    customers = []
    current_customer = None
    current_transactions = []
    
    print("Processing customer ledger data...")
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Split by tab
        parts = line.split('\t')
        
        # Check if this is a customer header line (format: (ID) CUSTOMER NAME)
        if len(parts) >= 1 and re.match(r'^\(\d+\)', parts[0]):
            # Save previous customer if exists
            if current_customer:
                current_customer['transactions'] = current_transactions
                current_customer['total_transactions'] = len(current_transactions)
                customers.append(current_customer)
            
            # Extract customer ID and name
            customer_header = parts[0].strip()
            match = re.match(r'^\((\d+)\)\s+(.+)', customer_header)
            
            if match:
                customer_id = match.group(1)
                customer_name = match.group(2).strip()
                
                current_customer = {
                    "customer_id": customer_id,
                    "customer_name": customer_name,
                    "account_period": {
                        "start_date": "2024-04-01",
                        "end_date": "2025-03-31"
                    },
                    "opening_balance": {
                        "amount": 0.0,
                        "type": ""
                    },
                    "transactions": [],
                    "total_transactions": 0,
                    "summary": {
                        "total_debits": 0.0,
                        "total_credits": 0.0,
                        "final_balance": 0.0,
                        "final_balance_type": ""
                    }
                }
                current_transactions = []
        
        # Check if this is a transaction line (has date in DD/MM/YYYY format)
        elif (len(parts) >= 4 and 
              re.match(r'^\d{2}/\d{2}/\d{4}', parts[0]) and 
              parts[0] != "Date"):
            
            try:
                date = parse_date(parts[0])
                debit_str = parts[1] if len(parts) > 1 else ""
                credit_str = parts[2] if len(parts) > 2 else ""
                balance_str = parts[3] if len(parts) > 3 else ""
                
                # Parse amounts
                debit = parse_indian_number(debit_str)
                credit = parse_indian_number(credit_str)
                balance, balance_type = extract_balance_info(balance_str)
                
                transaction = {
                    "date": date,
                    "debit": debit,
                    "credit": credit,
                    "balance": balance,
                    "balance_type": balance_type
                }
                
                if current_customer:
                    current_transactions.append(transaction)
                    
            except Exception as e:
                print(f"Error processing transaction line {i+1}: {e}")
                continue
        
        # Check if this is a Total line
        elif len(parts) >= 4 and parts[0].strip() == "Total :":
            if current_customer:
                try:
                    total_debits = parse_indian_number(parts[1])
                    total_credits = parse_indian_number(parts[2])
                    final_balance, final_balance_type = extract_balance_info(parts[3])
                    
                    current_customer['summary'] = {
                        "total_debits": total_debits,
                        "total_credits": total_credits,
                        "final_balance": final_balance,
                        "final_balance_type": final_balance_type
                    }
                except Exception as e:
                    print(f"Error processing total line {i+1}: {e}")
    
    # Don't forget the last customer
    if current_customer:
        current_customer['transactions'] = current_transactions
        current_customer['total_transactions'] = len(current_transactions)
        customers.append(current_customer)
    
    # Set opening balance for each customer (first transaction's balance)
    for customer in customers:
        if customer['transactions']:
            first_transaction = customer['transactions'][0]
            customer['opening_balance'] = {
                "amount": first_transaction['balance'],
                "type": first_transaction['balance_type']
            }
    
    print(f"Processed {len(customers)} customers")
    return customers

def save_to_json(customers: List[Dict[str, Any]], output_file: str):
    """Save customers data to JSON file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(customers, f, indent=2, ensure_ascii=False)
    print(f"Ledger data saved to {output_file}")

def print_customer_summary(customers: List[Dict[str, Any]]):
    """Print summary of all customers"""
    print("\n" + "="*60)
    print("ACCOUNT LEDGER SUMMARY")
    print("="*60)
    
    for customer in customers:
        print(f"\nCustomer ID: {customer['customer_id']}")
        print(f"Customer Name: {customer['customer_name']}")
        print(f"Total Transactions: {customer['total_transactions']}")
        
        if customer['opening_balance']['amount'] > 0:
            print(f"Opening Balance: ₹{customer['opening_balance']['amount']:,.2f} {customer['opening_balance']['type']}")
        
        summary = customer['summary']
        print(f"Total Debits: ₹{summary['total_debits']:,.2f}")
        print(f"Total Credits: ₹{summary['total_credits']:,.2f}")
        print(f"Final Balance: ₹{summary['final_balance']:,.2f} {summary['final_balance_type']}")
        
        # Calculate net position
        net_amount = summary['total_debits'] - summary['total_credits']
        print(f"Net Amount: ₹{net_amount:,.2f} {'(Customer owes)' if net_amount > 0 else '(Company owes)'}")

def main():
    """Main function to process the ledger data"""
    # Process the Account Ledger TSV file
    tsv_file = "Shivam Petroleum-Account Ledger_010424-310325.xlsx - Account Ledger.tsv"
    
    try:
        customers = process_ledger_data(tsv_file)
        
        # Save to JSON
        save_to_json(customers, "ledger_data.json")
        
        # Print summary
        print_customer_summary(customers)
        
        print(f"\n✅ Successfully processed {len(customers)} customers from the Account Ledger")
        
    except FileNotFoundError:
        print(f"❌ Error: File '{tsv_file}' not found!")
    except Exception as e:
        print(f"❌ Error processing file: {e}")

if __name__ == "__main__":
    main()
