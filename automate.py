import os
from openai import AzureOpenAI
import re
import argparse


class Automation:

    def __init__(self, main_path: str = None, main_test_path: str = None):
        self.client = AzureOpenAI(
            azure_endpoint="https://corpfunct-hackathon1-openai.openai.azure.com/",
            api_key='84c560949cad47edac056b1564e71b70',
            api_version="2024-02-15-preview"
        )
        if main_path is not None and main_test_path is not None:
            self.src_path = main_path
            self.test_path = main_test_path
            with open(main_path, 'r') as file:
                self.main_content = file.read()

            with open(main_test_path, 'r') as file:
                self.test_main = file.read()
        else:
            self.src_path = None
            self.test_path = None

    def test_case_generation(self, file: str, name: str):
        with open(file, 'r') as file:
            file_content = file.read()

        if self.src_path is not None:

            message_text = [{"role": "system",
                             "content": "You are an AI assistant that helps developer to generate test "
                                        "cases for their code"},
                            {"role": "user",
                             "content": f"Write me test cases for functions presents in the python file "
                                        f"provided below\n"
                                        f"{self.main_content}\nGenerate test cases for the entire code "
                                        f"aiming for 100% coverage"},
                            {"role": "assistant", f"content": f"Sure, here are your test cases \n "
                                                              f"{self.test_main}"},
                            {"role": "user",
                             "content": f"Write me test cases for functions presents in the python file "
                                        f"provided below\n"
                                        f"{file_content}\ninclude Gherkin references inside each test case"}]

        else:
            message_text = [{"role": "system",
                             "content": "You are an AI assistant that helps developer to generate test "
                                        "cases for their code"},
                            {"role": "user",
                             "content": f"Write me test cases for functions presents in the python file "
                                        f"provided\n"
                                        f"{file_content}\ninclude Gherkin references inside each test case, "
                                        f"write class-based test cases and also aim for 100% coverage"}]

        completion = self.client.chat.completions.create(
            model="gpt-35-turbo",  # model = "deployment_name"
            messages=message_text,
            temperature=0.45,
            max_tokens=3500,
            top_p=0.45,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None
        )

        response = completion.choices[0].message.content

        test_cases = re.findall(r'```python(.*?)```', response, re.DOTALL)

        new_directory_path = "tests/"  # Replace with the desired new directory path

        if not os.path.exists(new_directory_path):
            os.makedirs(new_directory_path)

        file_name = os.path.join(new_directory_path, f"test_{name}")
        with open(file_name, 'w') as test_file:
            test_file.write(''.join(test_cases))

        print(f'Test cases extracted from the response have been saved in the file: {name}')


def main():
    parser = argparse.ArgumentParser(description='Automate test case generation for a given function.')
    parser.add_argument('file_path', help='Path of file to be tested from root directory')
    parser.add_argument('file_name', help='Name of the file to be tested')
    parser.add_argument('example_function_path', help='Path to the example function', nargs='?')
    parser.add_argument('test_example_path', help='Path to the test example', nargs='?')
    args = parser.parse_args()

    if args.example_function_path and args.test_example_path:
        automate_test_generation = Automation(args.example_function_path, args.test_example_path)

    else:
        automate_test_generation = Automation()

    automate_test_generation.test_case_generation(args.file_name, args.file)


if __name__ == "__main__":
    main()


