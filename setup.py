from setuptools import setup, find_packages

setup(
    name="hackerone_research",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",
        "colorama>=0.4.6",
        "fake-useragent>=1.4.0",
    ],
    python_requires=">=3.8",
)