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
    # Fallback when /search (JQL) returns 410
    # This uses issue picker which is often allowed even when JQL search is restricted.
    query = "Automated test"  # change this if your test case summaries use a different prefix

    r = requests.get(
        f"{JIRA_URL}/rest/api/3/issue/picker",
        headers=jira_headers(EMAIL, token),
        params={
            "query": query,
            "currentProjectId": "",   # leave blank
            "currentJQL": f'project="{PROJECT_KEY}"'
        },
        timeout=30
    )
    r.raise_for_status()

    data = r.json()
    issues = data.get("sections", [])
    results = []

    for section in issues:
        for issue in section.get("issues", []):
            # issue picker returns key + summary
            if issue.get("key") and issue.get("summary"):
                results.append({"key": issue["key"], "fields": {"summary": issue["summary"]}})

    return results

    return r.json()["issues"]


def add_comment(token, key, text):
    requests.post(
        f"{JIRA_URL}/rest/api/3/issue/{key}/comment",
        headers=jira_headers(EMAIL, token),
        json={"body": adf(text)},
        timeout=30
    )


def attach_file(token, key, filename):
    with open(filename, "rb") as f:
        requests.post(
            f"{JIRA_URL}/rest/api/3/issue/{key}/attachments",
            headers={
                "Authorization": jira_headers(EMAIL, token)["Authorization"],
                "X-Atlassian-Token": "no-check"
            },
            files={"file": (filename, f)},
            timeout=60
        )


def create_bug(token, test_key, summary, evidence):
    payload = {
        "fields": {
            "project": {"key": PROJECT_KEY},
            "summary": f"[AUTO FAIL] {summary}",
            "description": adf(f"Automated test failed.\n\nEvidence:\n{evidence}"),
            "issuetype": {"name": BUG_ISSUETYPE},
        }
    }

    r = requests.post(
        f"{JIRA_URL}/rest/api/3/issue",
        headers=jira_headers(EMAIL, token),
        json=payload,
        timeout=30
    )

    r.raise_for_status()
    bug_key = r.json()["key"]

    # link bug <-> test case
    link = {
        "type": {"name": "Relates"},
        "inwardIssue": {"key": bug_key},
        "outwardIssue": {"key": test_key},
    }

    requests.post(
        f"{JIRA_URL}/rest/api/3/issueLink",
        headers=jira_headers(EMAIL, token),
        json=link,
        timeout=30
    )

    return bug_key


# ---------- Main ----------

if __name__ == "__main__":

    token = os.environ.get("JIRA_API_TOKEN")
    if not token:
        raise SystemExit('Run first: export JIRA_API_TOKEN="YOUR_TOKEN"')

    tests = search_testcases(token)

    if not tests:
        print("No auto-generated test cases found.")
        exit()

    print(f"Found {len(tests)} test cases.\n")

    for issue in tests:
        key = issue["key"]
        summary = issue["fields"]["summary"]

        print(f"Executing {key} | {summary}")

        result, evidence, screenshot = run_static_test()

        add_comment(token, key, f"Automated Result: {result}\n{evidence}")
        attach_file(token, key, screenshot)

        if result == "PASS":
            print(f"{key} PASS\n")
        else:
            bug_key = create_bug(token, key, summary, evidence)
            add_comment(token, key, f"Bug created automatically: {bug_key}")
            print(f"{key} FAIL -> Bug {bug_key}\n")

    print("Done.")
