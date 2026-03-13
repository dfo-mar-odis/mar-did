import os


def validate(file):
    return True

def validate2(file):
    return False

expected_biochem_files = {
    'salinity': {
        'filetypes': ['.csv'],
        'validators': [validate]
    },
    'oxygen': {
        'filetypes': ['.dat', '.xls'],
        'validators': [validate, validate2]
    },
    'chlorophyll': {
        'filetypes': ['.xls'],
        'validators': [validate]
    },
}

def validate_files(dir_path, expected):
    print('validating files')
    for file in os.listdir(dir_path):
        file_path = os.path.join(dir_path, file)
        if os.path.isfile(file_path):
            _, ext = os.path.splitext(file)
            if ext in expected['filetypes']:
                for validator in expected['validators']:
                    if not validator(file_path):
                        print(f"Validation failed for {file_path}")
                    else:
                        print(f"Validation passed for {file_path}")

            else:
                print(f"Unexpected file type: {file_path}")


# Scan a directory for recognizable subdirectories and files
def scan_mission_directory(mission_path):
    sub_dirs = [d for d in os.listdir(mission_path) if os.path.isdir(os.path.join(mission_path, d))]

    print(sub_dirs)

    for dir in sub_dirs:
        sub_dir = os.path.join(mission_path, dir)
        if dir.lower() in expected_biochem_files:
            validate_files(sub_dir, expected_biochem_files[dir.lower()])
        else:
            scan_mission_directory(sub_dir)


# these are directories expected in the root mission directory and the functions to run when they're encountered
expected_mission_directories = {
    'biochem': {
        'scanners': [scan_mission_directory]
    },
    'metadata': {
        'validators': [scan_mission_directory]
    },
}

def scan_dir(mission_path):
    sub_dirs = [d for d in os.listdir(mission_path) if os.path.isdir(os.path.join(mission_path, d))]

    print(sub_dirs)

    for dir in sub_dirs:
        if dir.lower() in expected_mission_directories:
            for scanner in expected_mission_directories[dir.lower()]['scanners']:
                scanner(os.path.join(mission_path, dir))
        else:
            print(f"Unexpected directory: {dir}")


if __name__ == "__main__":
    root_dir = '/home/colepram/Storage/projects/test_data/'
    mission = 'TEST2026666'

    scan_dir(os.path.join(root_dir, mission))
