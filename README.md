# Automation Scripts

Python automation framework for Jira testing.

This project:
- Creates test cases
- Uploads them to Jira
- Executes tests
- Marks pass/fail
- Creates bugs automatically for failures

---

## Files

01_create_testcases.py  → generate test cases  
02_run_testcases.py     → execute test cases  
jira_upload.py          → upload tests to Jira  
upload_testcases.py     → send data to Jira  
run_tests.py            → main runner  
utils.py                → helpers  

---

## Setup

Create virtual environment:

python -m venv venv
source venv/bin/activate

Install dependencies:

pip install -r requirements.txt

---

## Run

python run_tests.py

---

## Notes

Automation scripts for personal testing workflow.
