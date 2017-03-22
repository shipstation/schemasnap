from setuptools import setup, find_packages

setup(
    name='schemasnap',
    version='0.1',
    description='Document schemas with reflection, human editability, and doc rendering capabilities',
    url='https://github.com/shipstation/schemasnap',
    author='ShipStation Data Platform Team',
    author_email='dataplatform@shipstation.com',
    license='MIT',
    packages=find_packages(exclude=['tests']),
    package_data={'schemasnap': ['default_logging_config.yaml']},
    scripts=[
        'bin/db2yaml',
        'bin/excel2yaml',
    ],
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
    install_requires=[
        'colorlog',     # For prettier console logs (see logging.yaml)
        'ruamel.yaml',  # For maintaining YAML files with comments & dict key order
        'sqlalchemy',   # For dialect agnostic SQL reflection
        'xlrd',         # For excel sourced updates
    ],
)
