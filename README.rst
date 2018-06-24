============
Defournement
============


| Deploy the application.
| Only Kubernetes is supported right now.

Configuration
=============

Define the **/etc/farine.ini** or override the path using the environment variable **FARINE_INI**:

::

    [DEFAULT]
    amqp_uri=amqp://127.0.0.1:5672/amqp
    db_connector=postgres
    db_name=defournement
    db_user=jambon
    db_password=beurre
    db_host=127.0.0.1

    [defournement]
    enabled=true
    api_host=https://127.0.0.1
    api_ca_file=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    api_key=<key>
    exclude_namespaces=default,kube-system,kube-public,ingress,baguette


Launch
======

::

    farine --start=defournement
