from setuptools import find_packages, setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="bones",
    version="0.0.10",
    description="A bare-bones configuration managment tool.",
    package_dir={"": "bones"},
    packages=find_packages(where="bones"),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sizemore0125/bones",
    author="Logan Sizemore",
    author_email="sizemore0125@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
    extras_require={
        "dev": ["twine>=4.0.2"],
    },
    python_requires=">=3.7",
)