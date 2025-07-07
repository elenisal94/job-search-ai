import os
import requests
from dotenv import load_dotenv

# Load env variables
load_dotenv()
APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

def test_adzuna():
    country = "gb"  # Use 'gb' for the UK
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    
    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "what": "python developer",
        "where": "London",
        "results_per_page": 10,
        "content-type": "application/json"
    }

    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Jobs found: {data.get('count')}")
        for job in data.get("results", []):
            print(job["title"], "-", job.get("company", {}).get("display_name"))
    else:
        print("Error:", response.status_code, response.text)

test_adzuna()
