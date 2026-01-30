import os
from jira import JIRA

ISSUE_TYPE_NAME = "Test case"

def get_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v

def get_jira_client() -> JIRA:
    return JIRA(
        server=get_env("JIRA_URL"),
        basic_auth=(get_env("JIRA_EMAIL"), get_env("JIRA_API_TOKEN")),
    )

def customfield_number(field_id: str) -> str:
    # "customfield_10039" -> "10039"
    prefix = "customfield_"
    if not field_id.startswith(prefix):
        raise ValueError(f"Unexpected custom field id: {field_id}")
    n = field_id[len(prefix):]
    if not n.isdigit():
        raise ValueError(f"Unexpected custom field id: {field_id}")
    return n

def find_existing_by_automation_id(jira: JIRA, project_key: str, field_id: str, automation_id: str) -> str | None:
    # JQL: project=KEY AND cf[10039] ~ "test_001_..."
    cf = customfield_number(field_id)
    jql = f'project = {project_key} AND cf[{cf}] ~ "{automation_id}" ORDER BY created DESC'
    issues = jira.search_issues(jql, maxResults=1)
    return issues[0].key if issues else None

def upsert_test_case(jira: JIRA, project_key: str, field_id: str, tc: dict) -> str:
    fields = {
        "project": {"key": project_key},
        "summary": tc["summary"],
        "description": tc["description"],
        "issuetype": {"name": ISSUE_TYPE_NAME},
        field_id: tc["automation_id"],
    }

    existing_key = find_existing_by_automation_id(jira, project_key, field_id, tc["automation_id"])
    if existing_key:
        issue = jira.issue(existing_key)
        issue.update(fields=fields)
        return existing_key

    issue = jira.create_issue(fields=fields)
    return issue.key

def upload_test_cases(test_cases: list[dict]) -> None:
    jira = get_jira_client()
    project_key = get_env("JIRA_PROJECT_KEY")
    field_id = os.getenv("JIRA_AUTOMATION_FIELD_ID", "customfield_10039")

    for tc in test_cases:
        key = upsert_test_case(jira, project_key, field_id, tc)
        print(f"Upserted {key} ({tc['automation_id']})")

if __name__ == "__main__":
    # Minimal smoke-test example
    sample = [{
        "summary": "Happy Path Login",
        "description": "Steps:\n1. Open login page\n2. Enter valid creds\n3. Click Login\n\nExpected: Dashboard visible",
        "automation_id": "test_001_happy_path",
    }]
    upload_test_cases(sample)
    print("Done.")
