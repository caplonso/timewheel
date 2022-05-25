import pathlib
from setuptools import setup, find_packages

PATH = pathlib.Path(__file__).parent

README = (PATH / "README.md").read_text()


setup(
    name="timewheel-scheduler",
    version="0.3.0",
    description="Async crontab like scheduler",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Fausto Alonso",
    author_email="falonso@gmail.com",
    license="MIT",
    packages=find_packages(include=["timewheel"]),
    include_package_data=True
)