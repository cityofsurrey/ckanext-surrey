from setuptools import setup, find_packages
import sys, os

version = '1.0'

setup(
    name='ckanext-surrey',
    version=version,
    description="CKAN extension for the city of surrey",
    long_description="""\
        """,
    classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='City of Surrey',
    author_email='opendata@surrey.ca',
    url='https://github.com/CityofSurrey/ckanext-surrey/',
    license='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.surrey'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points= \
        """
        [ckan.plugins]
        # Add plugins here, eg
        surrey=ckanext.surrey.plugin:SurreyTemplatePlugin
        surreyfacet=ckanext.surrey.plugin:SurreyFacetPlugin
        surreyextrapages=ckanext.surrey.plugin:SurreyExtraPagesPlugin
        itranslation=ckanext.itranslation.plugin:ExampleITranslationPlugin
        [babel.extractors]
        ckan = ckan.lib.extract:extract_ckan
        """,
    message_extractors={
        'ckanext': [
            ('**.py', 'python', None),
            ('**.js', 'javascript', None),
            ('**/templates/**.html', 'ckan', None),
        ],
    },
)