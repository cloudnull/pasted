import setuptools


setuptools.setup(
    name='pasted',
    version='0.0.1',
    long_description=__doc__,
    packages=['pasted'],
    include_package_data=True,
    zip_safe=False,
    test_suite='tests',
    install_requires=[
        'flask',
        'flask-wtf',
        'blinker'
    ]
)
