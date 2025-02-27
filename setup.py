from setuptools import setup, find_namespace_packages

setup(
    name="ultravox-cli",
    version="0.1.0",
    packages=find_namespace_packages(),
    package_dir={"": "."},
    install_requires=[
        line.strip()
        for line in open("requirements.txt")
        if line.strip() and not line.startswith("#")
    ],
    python_requires=">=3.8",
)
