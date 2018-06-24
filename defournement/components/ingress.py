#-*- coding:utf-8 -*-
"""
Kubernetes ingress component :
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

class Ingress(object):

    def __init__(self, definition):
        """
        Initialize the definition.
        """
        self.definition = definition

    def exists(self):
        """
        Check if an ingress rule already exists.
        :rtype: bool
        """
        v1beta1 = client.ExtensionsV1beta1Api()
        try:
            v1beta1.read_namespaced_ingress(
                name=self.definition['repo'],
                namespace=self.definition['namespace'])
        except:
            LOGGER.exception('Ingress rule does not exist')
            return False
        return True

    def specifications(self):
        """
        Create the ingress specifications.
        :returns: The ingress specifications.
        :rtype: client.V1beta1IngressSpec
        """
        spec = client.V1beta1IngressSpec(
                    rules=[client.V1beta1IngressRule(
                        host=self.definition['domain_name'],
                        http=client.V1beta1HTTPIngressRuleValue(
                            paths=[client.V1beta1HTTPIngressPath(
                                path='/',
                                backend=client.V1beta1IngressBackend(service_name=self.definition['repo'], service_port=port['number']))
                                for port in self.definition['ports']
                            ]
                        )
                    )]
                )
        return client.V1beta1Ingress(
            metadata=client.V1ObjectMeta(name=self.definition['repo']),
            spec=spec
        )

    def create(self):
        """
        Create an ingress rule.
        """
        #1. Retrieve the spec
        ingress = self.specifications()
        #2. Apply
        try:
            v1beta1 = client.ExtensionsV1beta1Api()
            v1beta1.create_namespaced_ingress(self.definition['namespace'], body=ingress)
        except ApiException as exc:
            if exc.status != 404:
                LOGGER.error(exc)
            return False
        return True

    def update(self):
        """
        Update an ingress rule.
        """
        #1. Retrieve the spec
        ingress = self.specifications()
        #2. Apply
        try:
            v1beta1 = client.ExtensionsV1beta1Api()
            v1beta1.patch_namespaced_ingress(
                name=self.definition['repo'],
                namespace=self.definition['namespace'],
                body=ingress
            )
        except:
            LOGGER.exception('Cannot update the ingress rule')
            return False
        return True

    def deploy(self):
        """
        Deploy an ingress rule.
        :returns: The deploy status.
        :rtype: bool
        """
        if not self.exists():
            return self.create()
        return self.update()
    
    def delete(self):
        """
        Delete an ingress rule.
        """
