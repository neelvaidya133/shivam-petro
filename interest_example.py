"""
Example demonstrating the compound interest calculation logic
"""

def demonstrate_interest_calculation():
    """Show how the compound interest calculation works"""
    
    print("🧮 COMPOUND INTEREST CALCULATION EXAMPLE")
    print("=" * 50)
    
    # Example scenario
    daily_rate = 12 / 365 / 100  # 12% annual, daily compound
    print(f"Daily Interest Rate: {daily_rate:.6f} ({daily_rate*100:.4f}%)")
    print()
    
    # Track balance
    # Start with opening balance (if any)
    opening_balance = 500.0  # Example opening balance
    running_balance = opening_balance
    cumulative_interest = 0.0
    
    print(f"Opening Balance: ₹{opening_balance:,.2f}")
    print()
    
    # Day 1: Customer takes ₹1000 debt
    print("Day 1: Customer takes ₹1000 debt")
    running_balance += 1000.0
    print(f"  New Debt Added: ₹1000.00")
    print(f"  Outstanding Balance: ₹{running_balance:,.2f}")
    print()
    
    # Day 2: No transactions, just interest
    print("Day 2: No transactions")
    daily_interest = running_balance * daily_rate
    running_balance += daily_interest
    cumulative_interest += daily_interest
    print(f"  Daily Interest: ₹{daily_interest:.2f}")
    print(f"  Outstanding Balance: ₹{running_balance:,.2f}")
    print(f"  Cumulative Interest: ₹{cumulative_interest:.2f}")
    print()
    
    # Day 3: Customer pays ₹300 (FIFO)
    print("Day 3: Customer pays ₹300 (FIFO)")
    payments_today = 300.0
    
    # Apply payment at beginning of day
    if payments_today >= running_balance:
        payments_applied = running_balance
        running_balance = 0.0
    else:
        payments_applied = payments_today
        running_balance -= payments_today
    
    print(f"  Payment Applied: ₹{payments_applied:.2f}")
    print(f"  Remaining Balance: ₹{running_balance:,.2f}")
    
    # Calculate interest on remaining balance
    if running_balance > 0:
        daily_interest = running_balance * daily_rate
        running_balance += daily_interest
        cumulative_interest += daily_interest
        print(f"  Daily Interest: ₹{daily_interest:.2f}")
        print(f"  Outstanding Balance: ₹{running_balance:,.2f}")
    else:
        print("  No interest (balance cleared)")
    
    print(f"  Cumulative Interest: ₹{cumulative_interest:.2f}")
    print()
    
    # Day 4: Customer takes new debt ₹500
    print("Day 4: Customer takes new debt ₹500")
    new_debt = 500.0
    
    # Add new debt at end of day
    running_balance += new_debt
    print(f"  New Debt Added: ₹{new_debt:.2f}")
    print(f"  Outstanding Balance: ₹{running_balance:,.2f}")
    print()
    
    # Day 5: Calculate interest on total balance
    print("Day 5: Calculate interest on total balance")
    daily_interest = running_balance * daily_rate
    running_balance += daily_interest
    cumulative_interest += daily_interest
    print(f"  Daily Interest: ₹{daily_interest:.2f}")
    print(f"  Outstanding Balance: ₹{running_balance:,.2f}")
    print(f"  Cumulative Interest: ₹{cumulative_interest:.2f}")
    print()
    
    print("📊 SUMMARY:")
    print(f"  Opening Balance: ₹{opening_balance:.2f}")
    print(f"  Total Interest Charged: ₹{cumulative_interest:.2f}")
    print(f"  Final Outstanding Balance: ₹{running_balance:,.2f}")
    print(f"  Interest as % of Total Debt: {(cumulative_interest/(opening_balance+1000))*100:.2f}%")

if __name__ == "__main__":
    demonstrate_interest_calculation()
