#-*- coding:utf-8 -*-
"""
Kubernetes namespace component :
- create()
- delete()
- deploy()
- exists()
"""
import logging
from kubernetes import client
from kubernetes.client.rest import ApiException

LOGGER = logging.getLogger(__name__)

class Namespace(object):

    def __init__(self, name):
        """
        Initialize the definition.
        """
        self.name = name

    def exists(self):
        """
        Check if a namespace already exists.
        :rtype: bool
        """
        v1api = client.CoreV1Api()
        try:
            v1api.read_namespace(name=self.name)
        except:
            LOGGER.exception('Namespace does not exist')
            return False
        return True

    def create(self):
        """
        Create the namespace.
        :returns: Creation status.
        :rtype: bool
        """
        v1api = client.CoreV1Api()
        try:
            v1api.create_namespace(body=client.V1Namespace(metadata=client.V1ObjectMeta(name=self.name)))
        except:
            LOGGER.exception('Cannot create namespace')
            return False
        return True

    def deploy(self):
        """
        Deploy a namespace.
        :returns: The deploy status.
        :rtype: bool
        """
        if not self.exists():
            self.create()
        return True

    def delete(self):
        """
        Delete a namespace.
        """
