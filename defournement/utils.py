#-*- coding:utf-8 -*-
"""
Utils:
- k8s_config()
"""
import farine.settings
from kubernetes import client

def k8s_config():
    """
    Setup the kubernetes config.
    """
    configuration = client.Configuration()
    configuration.host = farine.settings.defournement['api_host']
    configuration.ssl_ca_cert = farine.settings.defournement['api_ca_file']
    configuration.api_key['authorization'] = farine.settings.defournement['api_key']
    configuration.api_key_prefix['authorization'] = 'Bearer'
    client.Configuration.set_default(configuration)

