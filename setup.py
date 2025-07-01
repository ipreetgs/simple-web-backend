from setuptools import setup, find_packages

setup(
    name="myapp",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Flask",
        "Flask-Cors",
        "Flask-SQLAlchemy",
        "Flask-JWT-Extended",
        "python-dotenv",
        "Werkzeug",
    ],
    entry_points={
        "console_scripts": [
            # No CLI entry, but you can add one if needed
        ],
    },
) 