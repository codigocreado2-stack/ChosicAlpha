"""Setup configuration for ChosicAlpha package (Python 3.12+)."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file if exists
this_directory = Path(__file__).parent
long_description = ""
readme_file = this_directory / "README.md"
if readme_file.exists():
    long_description = readme_file.read_text(encoding="utf-8")

setup(
    name="ChosicAlpha",
    version="0.0.1",
    author="codigocreado2-stack",
    description="Cliente y utilidades para la API de Chosic (Spotify Playlist Generator)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/codigocreado2-stack/ChosicAlpha",
    packages=find_packages(exclude=['test', 'test.*']),
    classifiers=[
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: GNU General Public License v2 (GPLv2)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.12",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-mock>=3.10.0",
            "pytest-cov>=4.0.0",
            "black>=21.0",
            "ruff>=0.1.0",
            "mypy>=1.5",
        ],
    },
    entry_points={
        "console_scripts": [
            "chosic-search=ChosicAlpha.Busqueda:main",
            "chosic-download=ChosicAlpha.Downloader:main",
        ],
    },
)
