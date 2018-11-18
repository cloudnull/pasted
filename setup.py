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
        'diskcache',
        'flask',
        'flask-wtf',
        'blinker',
        'openstacksdk'
    ],
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Topic :: Utilities',
        'Topic :: Software Development :: Libraries :: Python Modules'
      ],
    entry_points = {
        "console_scripts": [
            "pasted-debug = pasted.entry:start_app_debug",
            "pasted-prod = pasted.entry:start_app_prod"
        ]
    }
)
