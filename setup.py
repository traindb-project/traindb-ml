# -*- coding: utf-8 -*-

import os

from setuptools import find_packages, setup

with open('README.rst') as f:
    readme = f.read()


# with open('LICENSE.txt') as f:
#     licenses = f.read()


setup(
    name='etrimlclient',
    version='1.0',
    description='Model-based Approximate Query Processing (AQP) engine.',
    # classifiers=[
    #     'Development Status :: 1.0',
    #     'License :: OSI Approved :: MIT License',
    #     'Programming Language :: Python :: 3.8',
    #     'Topic :: Approximate Query Processing :: AQP :: Data Warehouse',
    # ],
    # classifiers=wtforms.fields.SelectMultipleField(
    #     description="Classifier",
    # ),
keywords='Approximate Query Processing AQP',
    url='https://github.com/traindb-project/etrimlclient',
    author='ETRI',
    author_email='sungsoo@etri.re.kr',
    long_description=readme,
    # license=licenses,
    # packages=['etrimlclient'],
    packages=find_packages(exclude=('experiments', 'tests', 'docs')),
    entry_points={
        'console_scripts': ['etrimlclient=etrimlclient.main:main', 'etrimlslave=etrimlclient.main:slave', 'etrimlmaster=etrimlclient.main:master'],
    },
    zip_safe=False,
    install_requires=[
        'numpy', 'sqlparse', 'pandas', 'scikit-learn', 'qregpy', 'scipy', 'dill', 'matplotlib', 'torch', 'category_encoders', 'tox', 'sphinx', 'gensim',
    ],
    test_suite='nose.collector',
    tests_require=['nose'],
)
