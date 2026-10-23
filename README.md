# WooCommerce Batch Image Sync

A high-performance Python script designed to automatically match local image files with WooCommerce products by SKU, upload them to the WordPress Media Library, and attach them to products concurrently.

---

## Features

- **Concurrent Uploads:** Leverages Python's `ThreadPoolExecutor` for parallel image uploads and API updates.
- **Persistent HTTP Connections:** Uses `requests.Session` for efficient connection pooling.
- **Smart SKU Matching:** Parses image filenames automatically to group gallery images by product SKU.
- **Environment Variable Configuration:** Secures sensitive API credentials outside of the codebase using `.env`.
- **Robust Error Handling:** Features configurable request timeouts and comprehensive exception catching for server stability.

---

## Prerequisites

Before running the script, ensure you have:

- **Python 3.8+** installed on your system.
- Access to your WordPress / WooCommerce site with:
  - WooCommerce REST API credentials (**Consumer Key** & **Consumer Secret**).
  - WordPress Application Password (**Username** & **App Password**).

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/MbankoKevin/woocommerce-batch-image-sync
   cd woocommerce-batch-image-sync
   ```

2. **Create a virtual environment (Optional but recommended):**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Configuration

1. Copy or rename `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Open `.env` and fill in your site details and API keys:

   ```env
   STORE_URL=https://your-domain.com/wp-json/wc/v3
   WP_MEDIA_URL=https://your-domain.com/wp-json/wp/v2/media

   WC_CONSUMER_KEY=ck_your_consumer_key_here
   WC_CONSUMER_SECRET=cs_your_consumer_secret_here

   WP_USERNAME=your_wp_username_or_email
   WP_APP_PASSWORD=xxxx xxxx xxxx xxxx

   IMAGE_FOLDER=C:\path\to\your\images
   ```

---

## Usage

1. **Organize your images:**  
   Place your images in the folder specified by `IMAGE_FOLDER`. Name them using your product SKU as the prefix:
   - `SKU123-front.jpg`
   - `SKU123-side.png`
   - `SKU123-1.webp`

2. **Run the script:**
   ```bash
   python main.py
   ```

---

## Project Structure

```text
├── .env.example        # Example environment variables template
├── .gitignore          # Rules for files Git should ignore (e.g., .env)
├── README.md           # Project documentation
├── requirements.txt    # Python dependencies list
└── main.py             # Main upload script
```

---

## License

Distributed under the MIT License. See `LICENSE` for more information.