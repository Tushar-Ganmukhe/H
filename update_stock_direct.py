"""
Simple script to update stock in Excel file using openpyxl.
This bypasses the locked file issue.
"""
import openpyxl

PRODUCT_FILE = r"C:\Users\hp\Downloads\products-export.xlsx"

def update_stock_in_excel(product_name: str, new_stock: int):
    """Update stock directly in Excel using openpyxl."""
    try:
        # Load workbook
        wb = openpyxl.load_workbook(PRODUCT_FILE)
        ws = wb.active
        
        # Get headers from first row
        headers = {}
        for col_idx, cell in enumerate(ws[1], 1):
            if cell.value:
                header_name = str(cell.value).lower().strip()
                headers[header_name] = col_idx
        
        print(f"Headers found: {list(headers.keys())}")
        print(f"Looking for columns: product name, stock")
        
        # Find required columns
        product_col = None
        stock_col = None
        
        for key, col_idx in headers.items():
            if 'product name' in key or key == 'name':
                product_col = col_idx
            if 'stock' in key:
                stock_col = col_idx
        
        if not product_col:
            print("ERROR: Could not find 'product name' column")
            return False
        if not stock_col:
            print("ERROR: Could not find 'stock' column")
            return False
        
        print(f"Product column: {product_col}, Stock column: {stock_col}")
        
        # Search for product and update stock
        found = False
        for row_idx in range(2, ws.max_row + 1):
            product_cell = ws.cell(row=row_idx, column=product_col)
            stock_cell = ws.cell(row=row_idx, column=stock_col)
            
            if product_cell.value:
                cell_value_normalized = str(product_cell.value).lower().strip()
                search_normalized = product_name.lower().strip()
                
                # Check for exact match or partial match
                if cell_value_normalized == search_normalized or search_normalized in cell_value_normalized:
                    print(f"✓ Found: {product_cell.value} at row {row_idx}")
                    print(f"  Old stock: {stock_cell.value}")
                    stock_cell.value = new_stock
                    print(f"  New stock: {stock_cell.value}")
                    wb.save(PRODUCT_FILE)
                    print(f"✓ Stock updated and saved to Excel!")
                    found = True
                    break
        
        if not found:
            print(f"✗ ERROR: Product '{product_name}' not found in Excel")
        
        return found
        wb.close()
        return False
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    # Test update
    print("Testing stock update...")
    update_stock_in_excel("NORSAN Omega-3", 18)
