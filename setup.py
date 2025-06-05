from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="certbot-dns-csc",
    version="1.0.0",
    author="Engin Eken",
    author_email="e.eken@outlook.com",
    description="CSC Global Domain Manager DNS Authenticator plugin for Certbot",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/EnginEken/certbot-dns-csc",
    project_urls={
        "Bug Tracker": "https://github.com/EnginEken/certbot-dns-csc/issues",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Plugins",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Security",
        "Topic :: System :: Installation/Setup",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=[
        "acme>=0.31.0",
        "certbot>=0.31.0",
        "requests>=2.20.0",
        "setuptools",
        "zope.interface",
    ],
    extras_require={
        "dev": [
            "pytest>=3.0.0",
            "pytest-cov",
            "responses>=0.9.0",
        ],
    },
    entry_points={
        "certbot.plugins": [
            "dns-csc = certbot_dns_csc.dns_csc:Authenticator",
        ],
    },
    include_package_data=True,
)
