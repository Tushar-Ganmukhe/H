"""
Test script to verify stock update with retry logic for locked files.
"""
import openpyxl
import time

PRODUCT_FILE = r"C:\Users\hp\Downloads\products-export.xlsx"

def update_stock_with_retry(product_name, target_stock, max_retries=3):
    """Update stock using openpyxl with retry logic for locked files"""
    
    try:
        print(f"\n{'='*60}")
        print(f"Updating stock: {product_name} → {target_stock}")
        print(f"{'='*60}")
        
        # Load workbook
        wb = openpyxl.load_workbook(PRODUCT_FILE)
        ws = wb.active
        
        # Find column indices
        product_col = None
        stock_col = None
        
        for col_idx in range(1, ws.max_column + 1):
            header = ws.cell(row=1, column=col_idx).value
            if header and 'product name' in str(header).lower():
                product_col = col_idx
            if header and 'stock' in str(header).lower():
                stock_col = col_idx
        
        if not product_col or not stock_col:
            print("ERROR: Could not find 'product name' or 'stock' column")
            return False
        
        # Search for product
        for row_idx in range(2, ws.max_row + 1):
            product_cell = ws.cell(row=row_idx, column=product_col)
            stock_cell = ws.cell(row=row_idx, column=stock_col)
            
            if product_cell.value:
                cell_normalized = str(product_cell.value).lower().strip()
                search_normalized = product_name.lower().strip()
                
                if cell_normalized == search_normalized or search_normalized in cell_normalized:
                    old_stock = stock_cell.value
                    print(f"✓ Found: {product_cell.value}")
                    print(f"  Old stock: {old_stock} → New stock: {target_stock}")
                    
                    stock_cell.value = target_stock
                    
                    # Try to save with retry logic
                    success = False
                    for attempt in range(max_retries):
                        try:
                            wb.save(PRODUCT_FILE)
                            print(f"✓ Successfully saved to Excel!")
                            success = True
                            break
                        except PermissionError:
                            if attempt < max_retries - 1:
                                wait_time = 1 + attempt  # 1s, 2s, 3s
                                print(f"  ⏳ File locked, waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                                time.sleep(wait_time)
                            else:
                                print(f"✗ File still locked after {max_retries} attempts")
                                print("  → Close Excel and try again, or run with 'read_only=True'")
                    
                    wb.close()
                    return success
        
        print(f"✗ Product '{product_name}' not found")
        wb.close()
        return False
        
    except Exception as e:
        print(f"✗ ERROR: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    # Test: Update NORSAN Omega-3 Total stock to 18
    result = update_stock_with_retry("NORSAN Omega-3 Total", 18)
    print(f"\nResult: {'SUCCESS' if result else 'FAILED'}")
