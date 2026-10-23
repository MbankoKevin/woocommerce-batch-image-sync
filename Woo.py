import os
import glob
import mimetypes
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- LOAD ENVIRONMENT VARIABLES ---
load_dotenv()

STORE_URL = os.getenv("STORE_URL")
WP_MEDIA_URL = os.getenv("WP_MEDIA_URL")

WC_CONSUMER_KEY = os.getenv("WC_CONSUMER_KEY")
WC_CONSUMER_SECRET = os.getenv("WC_CONSUMER_SECRET")

WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

IMAGE_FOLDER = os.getenv("IMAGE_FOLDER")

# Request timeout in seconds
TIMEOUT = 30
# Number of concurrent threads (adjust between 3-8 depending on your server hosting capacity)
MAX_WORKERS = 5

def create_session(auth):
    """Creates a requests Session with pre-configured auth for connection pooling."""
    session = requests.Session()
    session.auth = auth
    return session

def get_product_id_by_sku(session, sku):
    """Finds a WooCommerce product ID using its SKU."""
    try:
        response = session.get(
            f"{STORE_URL}/products", 
            params={"sku": sku}, 
            timeout=TIMEOUT
        )
        response.raise_for_status()
        products = response.json()
        if products:
            return products[0]["id"]
    except requests.exceptions.RequestException as e:
        print(f"    [Error] Network error while fetching SKU {sku}: {e}")
    return None

def upload_image_to_media_library(session, image_path, filename):
    """Uploads a local image file to WordPress Media Library using a persistent session."""
    content_type, _ = mimetypes.guess_type(image_path)
    if not content_type:
        content_type = "application/octet-stream"

    headers = {
        "Content-Disposition": f"attachment; filename={filename}",
        "Content-Type": content_type
    }
    
    try:
        with open(image_path, "rb") as img:
            response = session.post(
                WP_MEDIA_URL,
                headers=headers,
                data=img,
                timeout=TIMEOUT
            )
        
        if response.status_code == 201:
            return response.json()["id"]
        print(f"    [Error] Failed to upload {filename} (Status {response.status_code}): {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"    [Error] Network error uploading {filename}: {e}")
    
    return None

def process_sku(sku):
    """Handles the full workflow for a single SKU (thread-safe execution)."""
    # Create thread-specific sessions for connection pooling
    wc_session = create_session(HTTPBasicAuth(WC_CONSUMER_KEY, WC_CONSUMER_SECRET))
    wp_session = create_session(HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD))
    
    print(f"Processing SKU: {sku}...")
    
    product_id = get_product_id_by_sku(wc_session, sku)
    if not product_id:
        print(f"    [Skipped] Product with SKU '{sku}' not found in WooCommerce.")
        return
        
    pattern = os.path.join(IMAGE_FOLDER, f"{sku}*")
    matching_image_paths = [f for f in glob.glob(pattern) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    
    if not matching_image_paths:
        print(f"    [Skipped] No images found for SKU '{sku}'.")
        return
        
    matching_image_paths.sort()
    
    media_ids = []
    for img_path in matching_image_paths:
        filename = os.path.basename(img_path)
        print(f"    Uploading image: {filename}...")
        media_id = upload_image_to_media_library(wp_session, img_path, filename)
        if media_id:
            media_ids.append(media_id)
            
    if not media_ids:
        return
        
    featured_image_id = media_ids[0]
    gallery_image_ids = [{"id": mid} for mid in media_ids[1:]]
    
    update_data = {
        "images": [{"id": featured_image_id}] + gallery_image_ids
    }
    
    try:
        update_response = wc_session.put(
            f"{STORE_URL}/products/{product_id}", 
            json=update_data,
            timeout=TIMEOUT
        )
        
        if update_response.status_code == 200:
            print(f"    Success! Attached {len(media_ids)} image(s) to product {sku}.")
        else:
            print(f"    [Error] Failed to update product {sku} (Status {update_response.status_code}): {update_response.text}")
    except requests.exceptions.RequestException as e:
        print(f"    [Error] Network error updating product {sku}: {e}")

def main():
    if not IMAGE_FOLDER or not os.path.exists(IMAGE_FOLDER):
        print(f"[Error] Image folder path does not exist or is not set: {IMAGE_FOLDER}")
        return

    all_files = os.listdir(IMAGE_FOLDER)
    unique_skus = set()

    for filename in all_files:
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            base_name = os.path.splitext(filename)[0]
            parts = base_name.rsplit('-', 1)
            if len(parts) > 1 and (parts[1].isdigit() or parts[1] in ['front', 'side', 'back', 'interior', 'doors']):
                sku = parts[0]
            else:
                sku = base_name
                
            unique_skus.add(sku)

    print(f"Found {len(unique_skus)} unique SKUs to process. Starting parallel execution (Workers: {MAX_WORKERS})...\n")

    # Run SKUs concurrently using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_sku, sku) for sku in unique_skus]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"[Error] Thread generated an exception: {e}")

    print("\nAll tasks completed!")

if __name__ == "__main__":
    main()