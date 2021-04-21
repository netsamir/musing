from setuptools import find_packages, setup


def readme():
    with open('README.rst') as f:
        return f.read()


setup(
    name='crypto_bot',
    version='1.0',
    description='A Bots to trades crypto currency',
    author='Samir and Charlie',
    author_email='netsamir@gmail.com',
    package_dir={"": "src"},
    packages=find_packages("src"),
    include_package_data=True,
    tests_require=['nose2'],
    test_suite='nose2.collector.collector',
    entry_points={
        "console_scripts": [
           "cbot=crypto_bot.bot:main",
        ],
    },
    zip_safe=False
)
