import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()
REED_API_KEY = os.getenv("REED_API_KEY")

def test_reed_api():
    url = "https://www.reed.co.uk/api/1.0/search"
    params = {
        "keywords": "python developer",
        "locationName": "London",
        "distanceFromLocation": 10,
        "resultsToTake": 10,
        "resultsToSkip": 0
    }


    response = requests.get(url, params=params, auth=HTTPBasicAuth(REED_API_KEY, ''))
    
    if response.status_code == 200:
        data = response.json()
        print("Jobs found:", len(data.get("results", [])))
        for job in data.get("results", []):
            print(job["jobTitle"])
    else:
        print("Error:", response.status_code, response.text)

test_reed_api()
