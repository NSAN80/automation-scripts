# 02_run_testcases.py

import os
import re
import requests
from base64 import b64encode
from datetime import datetime
from playwright.sync_api import sync_playwright

# ================== CONFIG ==================
JIRA_URL = "https://nsan80.atlassian.net"
EMAIL = "ai@nsan80.com"
PROJECT_KEY = "AQLDM"

TEST_ISSUETYPE = "Test Case"
BUG_ISSUETYPE = "Bug"

AUTO_LABEL = "auto-generated"   # must match script 1

LOCAL_URL = "http://192.168.1.99:8000/index.html"
# ============================================


# ---------- Jira helpers ----------

def jira_headers(email, token):
    auth = b64encode(f"{email}:{token}".encode()).decode()
    return {
        "Authorization": f"Basic {auth}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def adf(text):
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {"type": "paragraph",
             "content": [{"type": "text", "text": text}]}
        ],
    }


# ---------- Playwright test ----------

def run_static_test():
    print("Running Playwright test (headless Firefox)...")

    with sync_playwright() as p:
        # IMPORTANT: headless=True prevents freezing
        browser = p.firefox.launch(headless=True)

        page = browser.new_page()
        page.goto(LOCAL_URL)

        heading = page.query_selector("h1")

        if heading:
            result = "PASS"
            heading_text = heading.inner_text()
        else:
            result = "FAIL"
            heading_text = "(no h1 found)"

        screenshot = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        page.screenshot(path=screenshot)

        browser.close()

    evidence = f"URL={LOCAL_URL} | H1={heading_text} | screenshot={screenshot}"
    return result, evidence, screenshot


# ---------- Jira operations ----------

def search_testcases(token):
    jql = f'project={PROJECT_KEY} AND issuetype="{TEST_ISSUETYPE}" AND labels="{AUTO_LABEL}" ORDER BY created DESC'

    r = requests.get(
        f"{JIRA_URL}/rest/api/3/search",
        headers=jira_headers(EMAIL, token),
        params={"jql": jql, "fields": "summary"},
        timeout=30
    )

    r.raise_for_status()
    return r.json()["issues"]


def add_comment(token, key, text):
    requests.post(
        f"{JIRA_URL}/rest/api/3/issue/{key}/c_
