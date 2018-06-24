#-*- coding:utf-8 -*-
"""
Kubernetes service component :
- create()
- delete()
- deploy()
- exists()
- update()
"""
import logging
from kubernetes import client
from kubernetes.client.rest import ApiException

LOGGER = logging.getLogger(__name__)

class Service(object):

    def __init__(self, definition):
        """
        Initialize the definition.
        """
        self.definition = definition

    def exists(self):
        """
        Check if a service already exists.
        :rtype: bool
        """
        v1api = client.CoreV1Api()
        try:
            v1api.read_namespaced_service(
                name=self.definition['repo'],
                namespace=self.definition['namespace'])
        except:
            LOGGER.exception('Namespace does not exist')
            return False
        return True

    def specifications(self):
        """
        Create the service specifications.
        :returns: The service specifications.
        :rtype: client.V1Service
        """
        #1. Port
        ports = [
            client.V1ServicePort(port=port['number'], target_port=port['number'], protocol=port['protocol'])
            for port in self.definition['ports']
        ]
        #2. Spec
        spec = client.V1ServiceSpec(
            type='ClusterIP',
            ports=ports,
            selector={"name": self.definition['repo']}
        )
        #3. Service
        return client.V1Service(
                metadata=client.V1ObjectMeta(name=self.definition['repo']),
                spec=spec
        )

    def create(self):
        """
        Create a service resource.
        :returns: The service creation status.
        :rtype: bool
        """
        #1. Retrieve the spec
        service = self.specifications()
        #2. Apply
        try:
            v1api = client.CoreV1Api()
            v1api.create_namespaced_service(self.definition['namespace'], body=service)
        except:
            LOGGER.exception('Cannot create the service')
            return False
        return True

    def update(self):
        """
        Update a service resource.
        :returns: The service creation status.
        :rtype: bool
        """
        #1. Retrieve the spec
        service = self.specifications()
        #2. Apply
        try:
            v1api = client.CoreV1Api()
            v1api.patch_namespaced_service(
                name=self.definition['repo'],
                namespace=self.definition['namespace'],
                body=service
            )
        except:
            LOGGER.exception('Cannot update the service')
            return False
        return True

    def deploy(self):
        """
        Deploy a service.
        :returns: The deploy status.
        :rtype: bool
        """
        if not self.exists():
            return self.create()
        return self.update()

    def delete(self):
        """
        Delete a service.
        """
