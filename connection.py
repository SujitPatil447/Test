import os
import requests
import base64
import re

# Configuration
GPT4V_KEY = "6acbefb394cf438f80dfa4f92444a3ba"
headers = {
    "Content-Type": "application/json",
    "api-key": GPT4V_KEY,
}
main_path = r"C:\Intern\test-gpt\test_gpt\main.py"

with open(main_path, 'r') as file:
    main_content = file.read()
# Payload for the request
payload = {
    "messages": [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": "You are an AI assistant that helps developer to generate test "
                            "cases for their code"
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Write complete pytest testcases for the code provided below, "
                            "also add gherkin reference for all test cases in string doc format "
                            f"inside each testcase for \n  {main_content}"
                }
            ]
        }
    ],
    "temperature": 0.45,
    "top_p": 0.45,
    "max_tokens": 3500
}

GPT4V_ENDPOINT = "https://dpe-openai.openai.azure.com/openai/deployments/dpe-4o/chat/completions?api-version=2024-02-15-preview"

# Send request
try:
    response = requests.post(GPT4V_ENDPOINT, headers=headers, json=payload)
    response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
except requests.RequestException as e:
    raise SystemExit(f"Failed to make the request. Error: {e}")

# Handle the response as needed (e.g., print or process)
res = response.json()

response_content = res['choices'][0]['message']['content']
test_cases = re.findall(r'```python(.*?)```', response_content, re.DOTALL)

print(test_cases[0])
