import os
import requests
import re
import argparse
from test_gpt.config.credentials import API_KEY, API_ENDPOINT


TEST_DIRECTORY = "tests/"


class TestGenerationAutomation:
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "api-key": API_KEY,
        }

    def test_case_generation(self, file: str, name: str):
        with open(file, 'r') as file:
            file_content = file.read()

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
                                    f"inside each testcase for \n  {file_content}"
                        }
                    ]
                }
        ],
            "temperature": 0.45,
            "top_p": 0.45,
            "max_tokens": 3500
        }

        try:
            response = requests.post(API_ENDPOINT, headers=self.headers, json=payload)
            response.raise_for_status()
        except requests.RequestException as e:
            raise SystemExit(f"Failed to make the request. Error: {e}")

        res = response.json()

        response_content = res['choices'][0]['message']['content']
        test_cases = re.findall(r'```python(.*?)```', response_content, re.DOTALL)

        if not os.path.exists(TEST_DIRECTORY):
            os.makedirs(TEST_DIRECTORY)

        file_name = os.path.join(TEST_DIRECTORY, f"test_{name}")
        with open(file_name, 'w') as test_file:
            test_file.write(''.join(test_cases[0]))

        print(f'Test cases extracted from the response have been saved in the file: test_{name}')


def main():
    parser = argparse.ArgumentParser(description='Automate test case generation for a given function.')
    parser.add_argument('file_path', help='Absolute Path of file to be tested')
    parser.add_argument('file_name', help='Name of the file to be tested with .py extension')
    args = parser.parse_args()

    automate_test_generation = TestGenerationAutomation()

    automate_test_generation.test_case_generation(args.file_path, args.file_name)


if __name__ == "__main__":
    main()

