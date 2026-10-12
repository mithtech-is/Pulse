from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = [line for line in f.read().splitlines() if line.strip()]

setup(
    name="pulse",
    version="0.1.0",
    description="Enterprise Project Management Platform",
    author="MithTech",
    author_email="info@mith.tech",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
