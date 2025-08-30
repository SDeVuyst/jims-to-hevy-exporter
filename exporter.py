### CHANGE THIS ###
JIMS_USERNAME = "your_username"
JIMS_PASSWORD = "your_password"
HEVY_API_KEY = "api_key"

### DO NOT CHANGE BELOW THIS LINE ###

import base64
import requests
from datetime import datetime, timedelta
from dateutil import parser
from pprint import pprint


LOGIN_URL = "https://myjims.jimsfitness.com/login"
CHECKIN_URL = "https://myjims.jimsfitness.com/selfservice/check-in-history"
BASE_URL = "https://api.hevyapp.com/v1/workouts"

def login_session():
    session = requests.Session()

    # Encode credentials as base64
    creds = f"{JIMS_USERNAME}:{JIMS_PASSWORD}"
    b64_creds = base64.b64encode(creds.encode()).decode()

    headers = {
        "Authorization": f"Basic {b64_creds}",
        "Content-Type": "application/json",
        "Origin": "https://myjims.jimsfitness.com",
        "User-Agent": "Mozilla/5.0",
        "x-tenant": "jimsfitness",
        "x-nox-client-type": "WEB",
        "x-public-facility-group": "JIMS-4428297DBB8242B1854D542AEE224B7F",
    }

    payload = {
        "username": JIMS_USERNAME,
        "password": JIMS_PASSWORD
    }

    res = session.post(LOGIN_URL, json=payload, headers=headers)
    if res.status_code != 200:
        raise Exception(f"Login failed: {res.status_code} - {res.text}")

    print("Login successful")
    return session


def fetch_checkins():
    session = login_session()
    today = datetime.today()
    last_year = today - timedelta(days=365)
    checkin_url = (
        f"https://myjims.jimsfitness.com/nox/v1/studios/checkin/history/report"
        f"?from={last_year.strftime('%Y-%m-%d')}&to={today.strftime('%Y-%m-%d')}"
    )

    checkin_headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "x-tenant": "jimsfitness",
        "x-nox-client-type": "WEB",
        "x-public-facility-group": "JIMS-4428297DBB8242B1854D542AEE224B7F",
    }

    resp = session.get(checkin_url, headers=checkin_headers)

    if resp.ok:
        checkins = resp.json()
        return checkins
    else:
        raise Exception(f"Failed to fetch check-ins: {resp.status_code} - {resp.text}")


def normalize_time(timestr):
    # strip the [Europe/Brussels] part and parse
    clean_str = timestr.split("[")[0]
    dt = parser.isoparse(clean_str)
    # return proper UTC ISO 8601 format
    return dt.astimezone(tz=None).isoformat()


if __name__ == "__main__":

    assert JIMS_USERNAME != "your_username", "Please set your JIMS_USERNAME"
    assert JIMS_PASSWORD != "your_password", "Please set your JIMS_PASSWORD"
    assert HEVY_API_KEY != "api_key", "Please set your Hevy API_KEY"

    jims_workouts = fetch_checkins()
    pprint(f"Fetched {len(jims_workouts)} check-ins")

    headers = {
        "accept": "application/json",
        "api-key": HEVY_API_KEY,
        "Content-Type": "application/json"
    }

    for workout in jims_workouts:
        payload = {
            "workout": {
                "title": f"Workout at {workout['studioName']}",
                "description": f"Auto-imported from Jims on {workout['date']}",
                "start_time": normalize_time(workout["checkinTime"]),
                "end_time": normalize_time(workout["checkoutTime"]),
                "is_private": False,
                "exercises": [
                    {
                        "exercise_template_id": "527DA061",
                        "superset_id": None,
                        "notes": "Auto-imported session",
                        "sets": [
                            {
                                "type": "normal",
                            }
                        ]
                    },
                ],
            }
        }

        response = requests.post(BASE_URL, headers=headers, json=payload)

        if response.status_code == 201:
            print("Workout created:", response.json())
        else:
            print("Error:", response.status_code, response.text)
