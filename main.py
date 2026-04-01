import os
import json
import base64
from datetime import datetime, timezone
from dotenv import load_dotenv
from groq import Groq
from playwright.sync_api import sync_playwright
from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSc8RRUAG8n8nPB9dm21m_MxwHQ-JuDnEj7GnvwEkWXykkKFuQ/viewform"
CALENDAR_ID = "akhil.k@kalvium.community"

def get_attendance_status():
    """Check Google Calendar for today's events to determine attendance status."""
    try:
        sa_json = os.getenv("GOOGLE_SERVICE_ACCOUNT")
        if not sa_json:
            print("No service account found, defaulting to present.")
            return "It was a working day, and I was present"

        sa_info = json.loads(sa_json)
        creds = service_account.Credentials.from_service_account_info(
            sa_info,
            scopes=["https://www.googleapis.com/auth/calendar.readonly"]
        )
        service = build("calendar", "v3", credentials=creds)

        today = datetime.now(timezone.utc).date()
        time_min = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc).isoformat()
        time_max = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc).isoformat()

        events = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True
        ).execute().get("items", [])

        for event in events:
            title = event.get("summary", "").lower()
            if "holiday" in title or "campus holiday" in title:
                print(f"Found holiday event: {event.get('summary')}")
                return "It was a campus holiday"
            if "leave" in title or "absent" in title:
                print(f"Found leave event: {event.get('summary')}")
                return "It was a working day, but I was on leave or absent"

        return "It was a working day, and I was present"

    except Exception as e:
        print(f"Calendar check failed: {e}, defaulting to present.")
        return "It was a working day, and I was present"

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSc8RRUAG8n8nPB9dm21m_MxwHQ-JuDnEj7GnvwEkWXykkKFuQ/viewform"

def get_auth_state():
    # In GitHub Actions, auth is passed as base64 env var
    auth_b64 = os.getenv("GOOGLE_AUTH_STATE")
    if auth_b64:
        auth_data = json.loads(base64.b64decode(auth_b64).decode("utf-8"))
        with open("auth.json", "w") as f:
            json.dump(auth_data, f)
    return "auth.json"

def generate_answers():
    prompt = """You are filling a daily work journal. Generate realistic, concise answers for the following 4 questions:
1. What were your key tasks for the day?
2. What challenges/problems did you solve today?
3. What challenges/problems were you NOT able to solve today?
4. What is your plan for the next day?

Reply with exactly 4 lines, one answer per line, no numbering or labels."""

    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    lines = [l for l in res.choices[0].message.content.strip().split("\n") if l.strip()]
    return lines

def submit_form(answers):
    auth_path = get_auth_state()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=auth_path)
        page = context.new_page()

        page.goto(FORM_URL)
        page.wait_for_load_state("networkidle")

        # Check if authenticated
        if "sign" in page.title().lower():
            print("Not authenticated — auth session may have expired.")
            browser.close()
            return

        # Check the "Record email" checkbox if unchecked
        try:
            checkbox = page.locator('[role="checkbox"]').first
            if checkbox.get_attribute("aria-checked") == "false":
                checkbox.click()
                page.wait_for_timeout(1000)
        except Exception:
            pass

        # Radio: select based on calendar status
        attendance = get_attendance_status()
        print(f"Attendance status: {attendance}")
        page.locator(f'[data-value="{attendance}"]').click()
        page.wait_for_timeout(1500)

        # Click Next
        page.get_by_role("button", name="Next").click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        # Fill text fields
        textareas = page.locator("textarea").all()
        for i, textarea in enumerate(textareas[:4]):
            textarea.click()
            textarea.fill(answers[i])
            page.wait_for_timeout(300)

        # Handle multi-page: keep clicking Next until Submit appears
        for _ in range(3):
            if page.get_by_role("button", name="Submit").count() > 0:
                break
            if page.get_by_role("button", name="Next").count() > 0:
                page.get_by_role("button", name="Next").click()
                page.wait_for_timeout(2000)

        page.get_by_role("button", name="Submit").click()
        page.wait_for_timeout(3000)

        print("Form submitted successfully!")
        browser.close()

if __name__ == "__main__":
    answers = generate_answers()
    print("Generated answers:")
    for a in answers:
        print(" -", a)
    submit_form(answers)