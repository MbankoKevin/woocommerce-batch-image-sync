import os
import re
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# --- LOAD ENVIRONMENT VARIABLES ---
load_dotenv()

STORE_URL = os.getenv("STORE_URL")
WC_CONSUMER_KEY = os.getenv("WC_CONSUMER_KEY")
WC_CONSUMER_SECRET = os.getenv("WC_CONSUMER_SECRET")

# Request timeout in seconds
TIMEOUT = 30

def generate_unique_sku(base_name, existing_skus):
    """
    Converts a product name into a clean SKU format and ensures uniqueness.
    """
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', base_name).upper()
    words = clean_name.split()
    
    sku_base = "-".join(words[:4])
    candidate_sku = f"CONT-{sku_base}"
    
    # Handle duplicate SKU collisions
    unique_sku = candidate_sku
    counter = 1
    while unique_sku in existing_skus:
        counter += 1
        unique_sku = f"{candidate_sku}-{counter}"
        
    existing_skus.add(unique_sku)
    return unique_sku

def main():
    if not STORE_URL or not WC_CONSUMER_KEY or not WC_CONSUMER_SECRET:
        print("[Error] Missing store URL or WooCommerce credentials in environment variables.")
        return

    # Create a persistent session for connection pooling
    session = requests.Session()
    session.auth = HTTPBasicAuth(WC_CONSUMER_KEY, WC_CONSUMER_SECRET)

    print("Starting SKU auto-generation and update process...\n")

    page = 1
    total_updated = 0
    existing_skus = set()

    # Step 1: Pre-load existing SKUs to avoid local collisions
    print("Fetching existing store SKUs to prevent duplicates...")
    while True:
        try:
            response = session.get(
                f"{STORE_URL}/products", 
                params={"per_page": 100, "page": page, "_fields": "sku"}, 
                timeout=TIMEOUT
            )
            response.raise_for_status()
            products = response.json()
            if not products:
                break
            for p in products:
                if p.get("sku"):
                    existing_skus.add(p["sku"].strip())
            page += 1
        except requests.exceptions.RequestException as e:
            print(f"[Error] Failed fetching existing products: {e}")
            break

    print(f"Loaded {len(existing_skus)} existing SKUs. Beginning scan for empty SKUs...\n")

    # Step 2: Iterate through products to find and assign missing SKUs
    page = 1
    while True:
        try:
            response = session.get(
                f"{STORE_URL}/products", 
                params={"per_page": 50, "page": page}, 
                timeout=TIMEOUT
            )
            response.raise_for_status()
            products = response.json()
        except requests.exceptions.RequestException as e:
            print(f"[Error] Network error on page {page}: {e}")
            break
            
        if not products:
            break  # No more products left to check
            
        for product in products:
            product_id = product["id"]
            name = product["name"]
            current_sku = product.get("sku", "").strip()
            
            # Only update if the SKU field is currently empty
            if not current_sku:
                new_sku = generate_unique_sku(name, existing_skus)
                print(f"Product: '{name}' (ID: {product_id})")
                print(f"    -> Assigning new SKU: {new_sku}")
                
                update_data = {"sku": new_sku}
                try:
                    update_response = session.put(
                        f"{STORE_URL}/products/{product_id}", 
                        json=update_data, 
                        timeout=TIMEOUT
                    )
                    
                    if update_response.status_code == 200:
                        print("    -> Successfully updated!\n")
                        total_updated += 1
                    else:
                        print(f"    -> [Error] Failed to update (Status {update_response.status_code}): {update_response.text}\n")
                except requests.exceptions.RequestException as e:
                    print(f"    -> [Error] Network error updating product {product_id}: {e}\n")
            else:
                print(f"Skipping '{name}' (Already has SKU: {current_sku})")
                
        page += 1

    print(f"Finished! Total products updated with new SKUs: {total_updated}")

if __name__ == "__main__":
    main()