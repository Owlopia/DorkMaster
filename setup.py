import os
import sys
from setuptools import setup, find_packages

# Read README.md for long description if available
long_description = ""
if os.path.exists("README.md"):
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()

dorks_file = "data/dorks.json" if os.path.exists("data/dorks.json") else "dorkmaster/data/dorks.json"

icon_file = "assets/DorkMaster.png" if os.path.exists("assets/DorkMaster.png") else "assets/dorkmaster.png"

setup(
    name="dorkmaster",
    version="0.1.0",
    author="infinitydecoder",
    maintainer="Owlopia",
    author_email="contact@owlopia.dev",
    description="Automated Google Dorking and OSINT Reconnaissance Tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Owlopia/DorkMaster",
    packages=find_packages(),
    package_data={
        "dorkmaster": ["assets/*.png", "data/*.json"],
    },
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "beautifulsoup4>=4.11.0",
        "tabulate>=0.8.10",
        "googlesearch-python>=1.2.3",
    ],
    entry_points={
        'console_scripts': [
            'dorkmaster=dorkmaster.cli:main',
        ],
    },
    data_files=[
        ("share/applications", ["dorkmaster.desktop"]),
        ("share/icons/hicolor/128x128/apps", [icon_file]),
        ("share/dorkmaster", [dorks_file]),
    ],
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Topic :: Security",
    ],
)
