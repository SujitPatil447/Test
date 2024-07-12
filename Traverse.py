import os


class Traverse:

    def __init__(self, path, ignore_folders=None):
        self.path = path
        self.ignore_folders = ignore_folders if ignore_folders else []
        self.default_ignore_files = ['__init__.py']
        self.default_prefix_ignore = 'test_'

    def get_list(self):
        # Specify the root directory using a raw string
        root_directory = self.path

        # Initialize an empty list to store file paths
        file_list = []

        # Traverse through the entire directory while ignoring specified folders and default ignore files
        for root, dirs, files in os.walk(root_directory):
            dirs[:] = [d for d in dirs if d not in self.ignore_folders]  # Ignore specified folders
            for file in files:
                if file.endswith('.py') and file not in self.default_ignore_files and not file.startswith(self.default_prefix_ignore):
                    file_path = os.path.join(root, file)
                    file_list.append((file, file_path))

        # Print the file names and paths
        for file_info in file_list:
            print(file_info)

        return file_list
