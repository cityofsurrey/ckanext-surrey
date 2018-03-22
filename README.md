![Logo Localidata](https://raw.githubusercontent.com/localidata/ckanext-surrey/master/ckanext/surrey/public/images/logoLocalidata.png)

ckanext-surrey
==============

En Localidata hemos modificado la extensión original del [La Ciudad de Surrey](https://github.com/CityofSurrey/ckanext-surrey) para la plataforma CKAN.

[CKAN](http://ckan.org) es un portal de código abierto, diseñado y desarrolado para que los gobiernos locales y estatales puedan publicar y compartir su datos abiertos fácilmente. 

Esta extensión actualmente sólo tiene la funcionalidad de Federación. 

Ha sido desarrollada para versiones 2.7.3 de CKAN.

#### Descarga y configuración de la extensión

-source /usr/lib/ckan/default/bin/activate
-cd /usr/lib/ckan/default/src		
-pip install -e git+git://github.com/localidata/ckanext-surrey.git#egg=ckanext-surrey
-plugins: ... surrey surreyfacet surreyextrapages


#### Eliminar
-pip uninstall ckanext-surrey