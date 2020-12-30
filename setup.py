from pathlib import Path

from setuptools import find_packages
from setuptools import setup

__version__ = "1.0.0"
ROOT_DIR = Path(".")

with open(str(ROOT_DIR / "README.md")) as readme:
    long_description = readme.read()

setup(
    name="SimpleCrawler",
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    author="jackwardell",
    author_email="jack@wardell.xyz",
    url="https://github.com/jackwardell",
    description="Enter something here",
    long_description=long_description,
    long_description_content_type="text/markdown",
    test_suite="tests",
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Natural Language :: English",
        "Intended Audience :: Developers",
    ],
    entry_points={
        "console_scripts": ["crawl=simple_crawler.cli:crawl"],
    },
    keywords="python",
    python_requires=">=3.6",
    install_requires=["requests", "click"],
)
