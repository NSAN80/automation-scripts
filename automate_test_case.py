from playwright.sync_api import sync_playwright
from datetime import datetime
import os
import requests

# ================== CONFIGURATION ==================
LOCAL_URL = "http://192.168.1.99:8000/index.html"

# Give the test a real name (this WILL show in Jira list / Work column)
TEST_NAME = "Static Page Smoke Test - Index Loads"

# Put your test steps here (these WILL show in the Jira description)
TEST_STEPS = [
    f"Navigate to {LOCAL_URL}",
    "Verify the page loads successfully",
    "Verify an H1 heading is present",
    "Capture a screenshot for evidence",
]

EXPECTED_RESULT = "Page loads and an H1 is present."

JIRA_URL = "https://nsan80.atlassian.net"
EMAIL = "ai@nsan80.com"
PROJECT_KEY = "AQLDM"
ISSUE_TYPE_NAME = "Test Case"

AUTOMATION_FIELD_ID = "customfield_10039"  # your Automation ID custom field
PRIORITY_NAME = "Medium"
# ===================================================


def adf_text(text: str) -> dict:
    return {"type": "text", "text": text}


def adf_paragraph(text: str) -> dict:
    return {"type": "paragraph", "content": [adf_text(text)]}


def adf_bullet_list(items: list[str]) -> dict:
    return {
        "type": "bulletList",
        "content": [
            {
                "type": "listItem",
                "content": [{"type": "paragraph", "content": [adf_text(item)]}],
            }
            for item in items
        ],
    }


def build_adf_description(test_name: str, steps: list[str], expected: str, actual_h1: str, result: str, screenshot: str) -> dict:
    content = [
        adf_paragraph(f"Test Name: {test_name}"),
        adf_paragraph("Preconditions: Web server is running and accessible."),
        adf_paragraph("Test Steps:"),
        adf_bullet_list(steps),
        adf_paragraph(f"Expected Result: {expected}"),
        adf_paragraph(f"Observed H1: {actual_h1}"),
        adf_paragraph(f"Execution Result: {result}"),
        adf_paragraph(f"Evidence: {screenshot} (attached)"),
    ]
    return {"type": "doc", "version": 1, "content": content}


def run_playwright_test():
    print("Starting Playwright test...")
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()

        print(f"Going to {LOCAL_URL} ...")
        page.goto(LOCAL_URL)

        heading = page.query_selector("h1")
        if heading:
            heading_text = heading.inner_text().strip()
            print(f"Found heading: {heading_text}")
            result = "PASS"
        else:
            heading_text = "(no h1 found)"
            print("Heading not found")
            result = "FAIL"

        screenshot_file = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        page.screenshot(path=screenshot_file)
        print(f"Screenshot saved: {screenshot_file}")

        browser.close()
        return result, heading_text, screenshot_file


def create_jira_test_case(result: str, heading_text: str, screenshot_file: str):
    jira_token = os.environ.get("JIRA_API_TOKEN")
    if not jira_token:
        raise SystemExit(
            "JIRA_API_TOKEN is not set. Run:\n"
            "  export JIRA_API_TOKEN=\"PASTE_YOUR_TOKEN_HERE\""
        )

    auth = (EMAIL, jira_token)

    # ✅ Summary = what you see in Jira list (“Work” column)
    summary = f"{TEST_NAME} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    # ✅ Automation value can include test name + timestamp
    automation_value = f"AUTO-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # ✅ Description with real steps (ADF)
    adf_description = build_adf_description(
        test_name=TEST_NAME,
        steps=TEST_STEPS,
        expected=EXPECTED_RESULT,
        actual_h1=heading_text,
        result=result,
        screenshot=screenshot_file,
    )

    payload = {
        "fields": {
            "project": {"key": PROJECT_KEY},
            "summary": summary,
            "description": adf_description,
            "issuetype": {"name": ISSUE_TYPE_NAME},
            "priority": {"name": PRIORITY_NAME},
            AUTOMATION_FIELD_ID: automation_value,
        }
    }

    print("Creating test case in Jira...")
    resp = requests.post(
        f"{JIRA_URL}/rest/api/3/issue",
        auth=auth,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )

    if resp.status_code != 201:
        raise SystemExit(f"Failed to create Jira issue: {resp.status_code} {resp.text}")

    issue_key = resp.json()["key"]
    print(f"Test case created: {issue_key}")

    # Attach screenshot
    attach_url = f"{JIRA_URL}/rest/api/3/issue/{issue_key}/attachments"
    with open(screenshot_file, "rb") as f:
        files = {"file": (screenshot_file, f)}
        attach_resp = requests.post(
            attach_url,
            auth=auth,
            headers={"X-Atlassian-Token": "no-check"},
            files=files,
            timeout=60,
        )

    if attach_resp.status_code in (200, 201):
        print("Screenshot attached successfully")
    else:
        print(f"Screenshot attach failed: {attach_resp.status_code} {attach_resp.text}")

    return issue_key


if __name__ == "__main__":
    result, heading_text, screenshot_file = run_playwright_test()
    issue_key = create_jira_test_case(result, heading_text, screenshot_file)
    print(f"Finished. Jira Test Case: {issue_key}, Result: {result}")
