import requests
import json
from base64 import b64encode

# -------------------------
# Step 2a: Jira Credentials
# -------------------------
JIRA_URL = "https://nsan80.atlassian.net"
EMAIL = "ai@nsan80.com"
API_TOKEN = "ATATT3xFfGF0tXVMg0FKD4JZIRV3XlS9FZ2ua4yewEOb4eQnGdgllrezcKtFS6KLLNMXBgAsluN918JrnmjjmUZ8rq89hUAHqFr6dBx5KKrmx0jXPMJ22zcbNWrkTJvFv__8kFbGztYGdaAdzVsU7lmO26e1TyUAXmOKHm8xMvgVQHUo02gk2k8=0392489C"   # Replace this with your actual API token
PROJECT_KEY = "AQLDM"
AUTOMATION_FIELD = "customfield_10039"  # Your Automation ID

# -------------------------
# Step 2b: Headers for Jira API
# -------------------------
auth = b64encode(f"{EMAIL}:{API_TOKEN}".encode()).decode()
headers = {
    "Authorization": f"Basic {auth}",
    "Content-Type": "application/json"
}

# -------------------------
# Step 2c: The test case in Jira ADF format
# -------------------------
test_case = {
    "fields": {
        "project": {"key": PROJECT_KEY},
        "summary": "Sample Test Case",  # This is the title of your test case
        "description": {                # ✅ This is the Atlassian Document Format (ADF)
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Step-by-step instructions for this test case go here."}
                    ]
                }
            ]
        },
        "issuetype": {"name": "Test Case"},  # Use the exact Jira issue type
        "priority": {"name": "Medium"},      # Can be changed to High/Low/etc
        AUTOMATION_FIELD: "AUTOMATION-001"   # Your automation ID
    }
}

# -------------------------
# Step 2d: Upload test case to Jira
# -------------------------
response = requests.post(
    f"{JIRA_URL}/rest/api/3/issue",
    headers=headers,
    data=json.dumps(test_case)
)

print("HTTP status code:", response.status_code)
print("Response:", response.text)
