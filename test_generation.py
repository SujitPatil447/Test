from automate import Automation
from Traverse import Traverse


class TestGeneration:
    sample_function = 'main.py'
    sample_test_function = 'test_main.py'

    def __init__(self, repo_address, ignored_folder: list = None):
        if ignored_folder is None:
            self.ignored_folder = []
        self.ignored_folder = ignored_folder
        self.repo_address = repo_address

    def automate_gen(self, sample_function: str = None, sample_test_function: str = None ):
        # creating instance of traverse class
        traverse_instance = Traverse(self.repo_address, self.ignored_folder)

        # calling get_list function to get list of function to be tested
        function_list = traverse_instance.get_list()

        # Creating Automation class instance to generate test cases
        automation_instance = Automation(sample_function, sample_test_function)

        for function in function_list:
            with open(function[1], 'r') as file:
                content = file.read()
            automation_instance.test_case_generation(content, function[0])
