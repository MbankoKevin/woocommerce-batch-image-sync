import os
import re
import requests
from requests.auth import HTTPBasicAuth

# --- CONFIGURATION ---
STORE_URL = "https://containersvent.com/wp-json/wc/v3"
WC_CONSUMER_KEY = "ck_b8cd59a153048f0392f82f397669a28cf3f527e5"
WC_CONSUMER_SECRET = "cs_e68f6c7e51157d9147077716d4c2270f3bf3d66e"

wc_auth = HTTPBasicAuth(WC_CONSUMER_KEY, WC_CONSUMER_SECRET)

def generate_sku_from_name(name):
    """
    Converts a product name into a clean SKU format.
    Example: '20ft Standard Shipping Container' -> 'CONT-20FT-STANDARD-SHIPPING'
    """
    # Remove special characters, convert to uppercase
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', name).upper()
    words = clean_name.split()
    
    # Prefix with 'CONT-' and join up to the first 4 words to keep it clean
    sku_base = "-".join(words[:4])
    return f"CONT-{sku_base}"

print("Starting SKU auto-generation and update process...\n")

page = 1
total_updated = 0

while True:
    # Fetch products page by page (50 per batch)
    response = requests.get(
        f"{STORE_URL}/products", 
        params={"per_page": 50, "page": page}, 
        auth=wc_auth
    )
    
    if response.status_code != 200:
        print(f"[Error] Failed to fetch products: {response.text}")
        break
        
    products = response.json()
    if not products:
        break # No more products left to check
        
    for product in products:
        product_id = product["id"]
        name = product["name"]
        current_sku = product.get("sku", "").strip()
        
        # Only update if the SKU field is currently empty
        if not current_sku:
            new_sku = generate_sku_from_name(name)
            print(f"Product: '{name}' (ID: {product_id})")
            print(f"   -> Assigning new SKU: {new_sku}")
            
            update_data = {"sku": new_sku}
            update_response = requests.put(
                f"{STORE_URL}/products/{product_id}", 
                json=update_data, 
                auth=wc_auth
            )
            
            if update_response.status_code == 200:
                print("   -> Successfully updated!\n")
                total_updated += 1
            else:
                print(f"   -> [Error] Failed to update: {update_response.text}\n")
        else:
            print(f"Skipping '{name}' (Already has SKU: {current_sku})")
            
    page += 1

print(f"Finished! Total products updated with new SKUs: {total_updated}")