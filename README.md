#City of Surrey CKAN extension

*CKAN extension development for the implementation of the [City of Surrey](https://www.surrey.ca/)*

The extension contains the following features:

- Add a custom CSS file
- Add custom pages (contact & suggest dataset forms + follow page) with implementation of iRoutes
- Add public file (images)
- Add custom licence
- Add predefined extra fields at the dataset level
- Support custom templates
- Remove 'organization' from the facet list and various other places

More documentation available in  [ckanext/surrey/docs/customization.md](ckanext/surrey/docs/customization.md)

## Prerequisite

This extension needs the stats extension to be activated with the tracking options

```
ckan.plugins =  ... stats ...
ckan.tracking_enabled = true 
```

In order to refresh the most popular dataset values, make sure to set up the cron jobs (see below).

The extension has been developed and tested to run with CKAN 2.2.

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
ckan.plugins =  ... surrey surreyfacet surreyextrapages
``` 

Add the custom licence file in the configuration file. 

```
licenses_group_url = file:///path/to/extension/ckanext-surrey/ckanext/surrey/licences.json
```


## Set up jobs

Some cron jobs have to be set up in order to have the extension working as expected.

In order to update the recent visits, the tracker and the index has to be rebuilt. The following command will do this using `cron -e` (make sure that the path to `paster` and the .ini file correspond to your installation):
```
@hourly /usr/lib/ckan/default/bin/paster --plugin=ckan tracking update -c /etc/ckan/default/production.ini > /dev/null
hourly /usr/lib/ckan/default/bin/paster --plugin=ckan search-index rebuild -r -c /etc/ckan/default/production.ini > /dev/null
```

In order to receive mail notification (either for the admin and for the users who are registering) add the following comming in the cron jobs:
```
@daily echo '{}' | /usr/lib/ckan/default/bin/paster --plugin=ckan post -c /etc/ckan/default/production.ini /api/action_notifications > /dev/null
```