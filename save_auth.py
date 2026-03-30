"""
Run this ONCE on your PC to save your Google login session.
It opens Edge — log in with your Google account, then press Enter.
"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    )
    context = browser.new_context()
    page = context.new_page()

    page.goto("https://accounts.google.com")
    print("Log in with your Google account in the Edge window.")
    print("After logging in successfully, press Enter here to save the session...")
    input()

    context.storage_state(path="auth.json")
    browser.close()
    print("Session saved to auth.json")
