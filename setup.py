from setuptools import find_packages, setup

def readme():
    with open('README.rst') as f:
        return f.read()


setup(
    name='BTCBot',
    version='1.0',
    description='Python Distribution Utilities',
    author='Samir and Charlie',
    author_email='netsamir@gmail.com',
    package_dir={"": "src"},
    packages=find_packages("src"),
    include_package_data=True,
    tests_require=['nose2'],
    test_suite='nose2.collector.collector',
     entry_points={
        "console_scripts": [
           "startbot=btcbot.simple_bot:main",
        ],
    },
    zip_safe=False
)
