#-*- coding:utf-8 -*-
"""
Kubernetes deployment component :
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

class Deployment(object):

    def __init__(self, definition):
        """
        Initialize the definition.
        """
        self.definition = definition

    def exists(self):
        """
        Check the existence of the deployment.
        :returns: The deploy status.
        :rtype: bool
        """
        v1beta1 = client.ExtensionsV1beta1Api()
        try:
            v1beta1.read_namespaced_deployment(
                self.definition['repo'],
                self.definition['namespace'])
        except:
            LOGGER.exception('Deployment does not exist')
            return False
        return True

    def specifications(self):
        """
        Set the deployment specifications.
        :returns: The deployment specifications.
        :rtype:  client.ExtensionsV1beta1Deployment
        """
        #1. Set the ports
        ports = [client.V1ContainerPort(container_port=port['number'], protocol=port['protocol']) for port in self.definition['ports']]
        #2. Set the resources
        #resources = {'cpu':self.definition['cpu'], 'memory': self.definition['memory']}
        resources = {'cpu':'100m', 'memory': '100Mi'}
        resources = client.V1ResourceRequirements(limits=resources, requests=resources)
        #3. Set healthchecks
        readiness = None
        liveness = None
        for health in self.definition['healthchecks']:
            _exec, tcp_socket, http_get = None, None, None
            if health['command'] == 'COMMAND':
                _exec = client.V1ExecAction(command=health['value'])
            elif health['command'] == 'TCP':
                tcp_socket = client.V1TCPSocketAction(port=health['port'])
            else:
                http_get = client.V1HTTPGetAction(path=health['path'], port=health['port'], scheme=health['command'])

            probe = client.V1Probe(failure_threshold=self.definition['failure_threshold'],
                    initial_delay_seconds=self.definition['initial_delay_seconds'],
                    period_seconds=self.definition['interval_seconds'],
                    success_threshold=self.definition['success_threshold'],
                    timeout_seconds=self.definition['timeout_seconds'],
                    _exec=_exec,
                    tcp_socket=tcp_socket,
                    http_get=http_get
                    )
            if health['type'] == 'readiness':
                readiness = probe
            else:
                liveness = probe
        #4. Security context
        security = client.V1SecurityContext(allow_privilege_escalation=False, run_as_non_root=True)
        #5. Set the container
        container = client.V1Container(
            name=self.definition['repo'],
            image=self.definition['tag'],
            ports=ports,
            resources=resources,
            readiness_probe=readiness,
            liveness_probe=liveness,
            security_context=security,
            env=None)#No need to setup envs : already done in the dockerfile
        #6. The pod template
        template = client.V1PodTemplateSpec(
            client.V1ObjectMeta(labels={"name": self.definition['repo'], "repo": self.definition['repo'], "owner": self.definition['owner'], "branch": self.definition['branch'], "fullname": self.definition['name']}),
            spec=client.V1PodSpec(containers=[container]))
        #7. The rolling update strategy
        strategy = client.ExtensionsV1beta1DeploymentStrategy(
            type='RollingUpdate',
            rolling_update=client.ExtensionsV1beta1RollingUpdateDeployment(
                max_surge=1,
                max_unavailable=1
            )
        )
        #8. The deployment spec
        spec = client.ExtensionsV1beta1DeploymentSpec(
                #replicas=self.definition['instances'],
                replicas=1,
                strategy=strategy,
                template=template)
        #9. The deployment object
        deployment = client.ExtensionsV1beta1Deployment(
                api_version="extensions/v1beta1",
                kind="Deployment",
                metadata=client.V1ObjectMeta(name=self.definition['repo'], labels={"uid": self.definition['uid'], "repo": self.definition['repo'], "owner": self.definition['owner'], "branch": self.definition['branch'], "fullname": self.definition['name'], "name": self.definition['repo']}),
                spec=spec)
        return deployment

    def create(self):
        """
        Create a deployment.
        """
        LOGGER.info('deployment.create()')
        #1. Retrieve the container spec
        deployment = self.specifications()
        #2. Apply
        try:
            v1beta1 = client.ExtensionsV1beta1Api()
            v1beta1.create_namespaced_deployment(body=deployment, namespace=self.definition['namespace'])
        except ApiException as exc:
            LOGGER.error(exc)
            return False
        return True

    def update(self):
        """
        Update a deployment.
        """
        LOGGER.info('deployment.update()')
        #1. Retrieve the container spec
        deployment = self.specifications()
        #2. Patch
        try:
            v1beta1 = client.ExtensionsV1beta1Api()
            v1beta1.patch_namespaced_deployment(name=self.definition['repo'], namespace=self.definition['namespace'], body=deployment)
        except:
            LOGGER.exception('Cannot update the deployment')
            return False
        return True

    def deploy(self):
        """
        Deploy a deployment.
        :returns: The deploy status.
        :rtype: bool
        """
        LOGGER.info('deployment.deploy()')
        if not self.exists():
            return self.create()
        return self.update()

    def delete(self):
        """
        Delete a deployment resource. Idempotent.
        :returns: The deployment deletion status.
        :rtype: bool
        """
        try:
            v1beta1 = client.ExtensionsV1beta1Api()
            v1beta1.delete_namespaced_deployment(
            name=self.definition['name'],
            namespace=self.definition['namespace'],
            body=client.V1DeleteOptions(
                propagation_policy='Foreground',
                grace_period_seconds=5))
        except ApiException as exc:
            if exc.status != 404:
                LOGGER.error(exc)
                return False
        return True
