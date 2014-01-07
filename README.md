#City of Surrey CKAN extension

*CKAN extension development for the implementation of the [City of Surrey](https://www.surrey.ca/)*

The extension contains the following features:

- Add a custom CSS file
- Add public file (images)
- Add custom licence
- Add predefined extra fields at the dataset level
- Support custom templates
- Remove the 'organization' from the facet list

More documentation available in [ckanext/surrey/docs/customization.md](ckanext/surrey/docs/customization.md)

## Installation

Activate your pyenv and go to the CKAN root, for example:
```
 cd /usr/lib/ckan/default/
 source bin/activate
 cd src/ckan
```

Install the extension from GitHub:

```
pip install -e git+git://github.com/opennorth/ckanext-surrey.git#egg=ckanext-surrey
```

Add the extension in the configuration file. `surrey` does most of the work, `surreyfacet` mainly removes the organization from the facet menu
```
ckan.plugins =  ... surrey surreyfacet
``` 

Add the custom licence file in the configuration file.

```
licenses_group_url = file:///path/to/extension/ckanext-surrey/ckanext/surrey/licences.json
```
