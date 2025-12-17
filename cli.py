import sqlite3
import os
from datetime import datetime

# CONFIGURATION
DB_NAME = "type43.db"

def get_db_connection():
    return sqlite3.connect(DB_NAME)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    clear_screen()
    print("==========================================")
    print("   TYPE43 // UMBRELLA FIELD TERMINAL v1   ")
    print("==========================================")

def add_receipt():
    print_header()
    print(">> MODE: RECEIPT INGESTION\n")
    
    vendor = input("Vendor (e.g., Home Depot): ")
    date = input("Date (YYYY-MM-DD) [Enter for Today]: ")
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
        
    try:
        amount = float(input("Total Amount ($): "))
    except ValueError:
        print("Invalid amount. Aborting.")
        input("Press Enter...")
        return

    notes = input("Notes: ")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO receipts (vendor_name, purchase_date, total_amount, notes) VALUES (?, ?, ?, ?)",
        (vendor, date, amount, notes)
    )
    conn.commit()
    conn.close()
    print("\n[SUCCESS] Receipt Logged.")
    input("Press Enter to continue...")

def add_inventory():
    print_header()
    print(">> MODE: PHYSICAL ASSET LOG\n")
    
    name = input("Item Name (e.g., DeWalt Drill): ")
    category = input("Category (Tool/Material): ")
    qty = input("Quantity [1]: ") or "1"
    
    try:
        est_price = float(input("Estimated Purchase Price ($): "))
    except ValueError:
        est_price = 0.0

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO inventory (name, category, quantity_on_hand, purchase_price, date_acquired) VALUES (?, ?, ?, ?, ?)",
        (name, category, int(qty), est_price, datetime.now().strftime("%Y-%m-%d"))
    )
    conn.commit()
    conn.close()
    print("\n[SUCCESS] Asset Tracked.")
    input("Press Enter to continue...")

def view_report():
    print_header()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Simple Sums
    cursor.execute("SELECT COUNT(*), SUM(total_amount) FROM receipts")
    r_count, r_total = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*), SUM(purchase_price * quantity_on_hand) FROM inventory")
    i_count, i_total = cursor.fetchone()
    
    conn.close()
    
    print(">> SESSION REPORT\n")
    print(f"Receipts Logged:  {r_count}   |  Value: ${r_total if r_total else 0:,.2f}")
    print(f"Physical Items:   {i_count}   |  Value: ${i_total if i_total else 0:,.2f}")
    print("------------------------------------------")
    print(f"TOTAL AUDIT VALUE: ${(r_total if r_total else 0) + (i_total if i_total else 0):,.2f}")
    print("\n(This is the number you show Dad)")
    input("\nPress Enter to return...")

def main_menu():
    while True:
        print_header()
        print("1. Log a RECEIPT (Paper)")
        print("2. Log an ITEM (Physical)")
        print("3. View Valuation Report")
        print("4. Exit")
        
        choice = input("\nSelect Option: ")
        
        if choice == '1':
            add_receipt()
        elif choice == '2':
            add_inventory()
        elif choice == '3':
            view_report()
        elif choice == '4':
            print("Syncing data... Goodbye.")
            break

if __name__ == "__main__":
    main_menu()