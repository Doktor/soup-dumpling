import setuptools

setuptools.setup(
    name="soup_dumpling",
    version='3.0.0',
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
