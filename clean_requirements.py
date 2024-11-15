import re
import subprocess
from pathlib import Path

def clean_and_update_requirements():
    """Clean and update requirements.txt file."""
    requirements_path = Path('requirements.txt')
    
    # Read and clean the current requirements
    try:
        # Try different encodings
        for encoding in ['utf-8', 'utf-8-sig', 'latin-1']:
            try:
                with open(requirements_path, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # Clean and parse requirements
    clean_requirements = []
    for line in content.split('\n'):
        # Remove any BOM or special characters
        line = line.strip().replace('\ufeff', '')
        # Skip empty lines or comments
        if not line or line.startswith('#'):
            continue
        # Extract package name and version using regex
        match = re.match(r'^([a-zA-Z0-9\-._]+)(?:==|>=|<=|~=|!=|>|<)?([a-zA-Z0-9\-._]+)?', line)
        if match:
            package_name = match.group(1)
            try:
                # Get latest version
                result = subprocess.run(
                    ['pip', 'index', 'versions', package_name],
                    capture_output=True,
                    text=True
                )
                latest_version = result.stdout.split('\n')[0].split(' ')[-1]
                clean_requirements.append(f"{package_name}=={latest_version}")
                print(f"Updated {package_name} to version {latest_version}")
            except Exception as e:
                print(f"Error updating {package_name}: {e}")
                if match.group(2):  # If there was an original version
                    clean_requirements.append(f"{package_name}=={match.group(2)}")
                else:
                    clean_requirements.append(package_name)

    # Write the cleaned and updated requirements
    try:
        with open('requirements.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(clean_requirements))
        print("\nSuccessfully cleaned and updated requirements.txt!")
    except Exception as e:
        print(f"Error writing file: {e}")

if __name__ == '__main__':
    clean_and_update_requirements()