import os
import time
import requests
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import Json
from datetime import datetime

load_dotenv()

# Database connection settings
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "parking_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")

# Warsaw Open Data API configuration
API_URL = os.getenv(
    "WARSAW_API_URL", 
    "https://dane.um.warszawa.pl/api/action/get_m_parkingi_wolne_miejsca"
)
API_TOKEN = (os.getenv("WARSAW_API_TOKEN") or os.getenv("WARSAW_API_KEY") or os.getenv("API_TOKEN") or "").strip(' "\'')

def get_db_connection():
    """Establish and maintain a resilient database connection with auto-retry."""
    while True:
        try:
            return psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                port=DB_PORT
            )
        except psycopg2.OperationalError as e:
            print(f"[{datetime.now()}] Database connection error, retrying in 3 seconds: {e}")
            time.sleep(3)

def fetch_parking_data():
    """Fetch live parking occupancy data from the Warsaw Open Data API."""
    headers = {}
    if API_TOKEN:
        headers["Authorization"] = API_TOKEN
    try:
        response = requests.post(API_URL, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"[{datetime.now()}] Error fetching parking data: {e}")
        return None

def save_data(data):
    """Parse API response and persist parking registry and occupancy logs into PostgreSQL."""
    if not data:
        print(f"[{datetime.now()}] No data to save.")
        return

    # 1. Check known primary keys
    parkings_list = data.get("Parkings") or data.get("carParks")

    # 2. Dynamic fallback: extract the first non-empty list found in the payload
    if not parkings_list and isinstance(data, dict):
        for val in data.values():
            if isinstance(val, list) and len(val) > 0:
                parkings_list = val
                break

    # 3. Abort gracefully if no list structure matches
    if not parkings_list:
        print(f"[{datetime.now()}] No parking list found in response.")
        return

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        for item in parkings_list:
            name = item.get("name")
            if not name:
                continue

            # Parse coordinates and descriptive metadata
            lat = float(item.get("latitude")) if item.get("latitude") else None
            lon = float(item.get("longitude")) if item.get("longitude") else None
            address = item.get("adress", "")
            manager = item.get("manager", "")
            category = item.get("parkingCategory", "")

            # Calculate total parking capacity across all levels
            total_spots = 0
            for lvl in item.get("total_places", []):
                total_spots += lvl.get("standard", 0) + lvl.get("disabled", 0) + lvl.get("electric", 0)

            # Insert or update static parking facility record
            cur.execute("""
                INSERT INTO parkings (name, latitude, longitude, address, manager, category, total_spots)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (name) DO UPDATE 
                SET total_spots = EXCLUDED.total_spots,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude;
            """, (name, lat, lon, address, manager, category, total_spots))

            # Parse available spot metrics with safe fallback to zero
            free_info = item.get("free_places_total", {})
            free_public = free_info.get("public", 0) or 0
            free_disabled = free_info.get("disabled", 0) or 0
            free_electric = free_info.get("electric", 0) or 0
            total_free = free_public + free_disabled + free_electric

            # Append time-series occupancy measurement
            cur.execute("""
                INSERT INTO parking_occupancy_logs 
                (parking_name, free_public, free_disabled, free_electric, total_free, raw_payload)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (name, free_public, free_disabled, free_electric, total_free, Json(item)))

        conn.commit()
        print(f"[{datetime.now()}] Saved {len(parkings_list)} parking entries to the database.")
    except Exception as e:
        conn.rollback()
        print(f"[{datetime.now()}] Error saving data to the database: {e}")
    finally:
        cur.close()
        conn.close()

def fetch_and_save():
    """Single fetch and storage cycle."""
    payload = fetch_parking_data()
    if payload:
        save_data(payload)

def main():
    """Main execution loop polling the API every 5 minutes."""
    print(f"[{datetime.now()}] Starting parking data fetcher...")
    while True:
        fetch_and_save()
        time.sleep(300)

if __name__ == "__main__":
    main()