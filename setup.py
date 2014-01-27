from setuptools import setup, find_packages
import sys, os

version = '0.9'

setup(
	name='ckanext-surrey',
	version=version,
	description="Custom behaviour for the City of Surrey Ckan instance",
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author='City of Surrey',
	author_email='opendata@surrey.ca',
	url='https://github.com/opennorth/ckanext-surrey',
	license='',
	packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
	namespace_packages=['ckanext', 'ckanext.surrey'],
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		# -*- Extra requirements: -*-
	],
	entry_points=\
	"""
        [ckan.plugins]
	# Add plugins here, eg
	surrey=ckanext.surrey.plugin:SurreyTemplatePlugin
        surreyfacet=ckanext.surrey.plugin:SurreyFacetPlugin
	""",
)
