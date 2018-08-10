import setuptools

from soup.__version__ import VERSION_STRING


setuptools.setup(
    name="soup_dumpling",
    version=VERSION_STRING,
    author="Doktor",
    author_email="doktorthehusky@gmail.com",

    packages=setuptools.find_packages(),
    python_requires='>=3',

    entry_points={
        'console_scripts': [
            'soup = soup.main:main',
        ]
    }
)
