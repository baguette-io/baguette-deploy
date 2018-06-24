#-*-coding:utf-8 -*-
#pylint:disable=line-too-long,no-self-use
"""
Entrypoint for the deployment:
- list()
- detail()
- create_deployment()
- create_ingress()
- create_service()
- delete()
- watch()
"""
import logging
from farine.connectors.sql import fn
import farine.amqp
import farine.execute
import farine.rpc
from defournement.models import Deployment as Model
from defournement.models import Status
import defournement.components as cmpt
import defournement.utils

LOGGER = logging.getLogger(__name__)

class Defournement(object):
    """
    Deployment management:
    - Call the orchestration to start the deployment.
    - Listen to update its state.
    """

    def __init__(self):
        defournement.utils.k8s_config()
        self.exclude_namespaces= farine.settings.defournement['exclude_namespaces'].split(',')

    @farine.rpc.method()
    def list(self, owner, offset=0, limit=10):
        """
        Get the last deployment records given an owner.
        :param owner: The owner to retrieve the deployments.
        :type owner: str
        :param offset: The offset to start retrieving deployments. Default to 0.
        :type limit: int
        :param limit: The number of deployments to retrieve. Default to 10.
        :type limit: int
        :returns: The owner deployments.
        :type: dict
        """
        output = {'count':0, 'next':None, 'previous':None, 'results':[]}
        output['count'] = Model.select(fn.count(Model.uid)).where(Model.owner == owner).scalar()
        deployments = Model.select().where(Model.owner == owner).order_by(Model.date_created.desc()).offset(offset).limit(limit)
        for deployment in deployments:
            query = Status.select().where(Status.uid == deployment.uid).order_by(Status.date_created.desc()).get()
            output['results'].append(deployment.to_json(extras={'status':query.status}))
        return output

    @farine.rpc.method()
    def detail(self, owner, uid):
        """
        Given an owner and an uid, retrieve the details.
        :param owner: The owner to retrieve the deployment details.
        :type owner: str
        :param uid: The deployment uid.
        :type uid: str
        :returns: The deployment details.
        :type: list
        """
        output = {'count':0, 'next':None, 'previous':None, 'results':[]}
        #1. Check permission
        exist = Model.select().where(Model.owner == owner, Model.uid == uid).scalar()
        if not exist:
            return output
        # 2. Retrieve all the status
        output['count'] = Status.select().where(Status.uid == uid).count()
        query = Status.select().where(Status.uid == uid).order_by(Status.date_created.desc())
        output['results'] = [q.to_json() for q in query]
        return output

    @farine.amqp.consume(exchange='deployment', routing_key='create')
    def create(self, body, message):
        """
        Deploy an application.
        :param body: The application definition.
        :type body: dict
        :param message: Message class.
        :type message: kombu.message.Message
        """
        message.ack()
        LOGGER.info(body)
        definition = body['definition']
        #1. Create the Deployment model
        Model.create(uid=definition['uid'], owner=definition['owner'], name=definition['name'], namespace=definition['namespace'])
        Status.create(uid_id=definition['uid'], status='deploying')
        #2. Namespace
        component = cmpt.Namespace(definition['namespace'])
        result = component.deploy()
        if not result:
            Status.create(uid=definition['uid'], status='error:namespace')
        #3. Service
        component = cmpt.Service(definition)
        result = component.deploy()
        if not result:
            Status.create(uid=definition['uid'], status='error:service')
        #4. Ingress
        component = cmpt.Ingress(definition)
        result = component.deploy()
        if not result:
            Status.create(uid=definition['uid'], status='error:ingress')
        #5. Deployment
        component = cmpt.Deployment(definition)
        result = component.deploy()
        if not result:
            Status.create(uid=definition['uid'], status='error:deployment')
        return result

    @farine.rpc.method()
    def delete(self, owner, uid):
        """
        Delete a deployment.
        :param body: The application definition.
        :type body: dict
        :param message: Message class.
        :type message: kombu.message.Message
        """
        try:
            current = Model.select().where(Model.owner == owner, Model.uid == uid).get()
        except Model.DoesNotExist:
            return True
        Status.create(uid=uid, status='terminating')
        component = cmpt.Deployment({'uid': uid, 'name': current.name, 'owner': owner, 'namespace': current.namespace})
        ##
        if not component.exists():
            Status.create(uid=uid, status='terminated')
            return True
        result = component.delete()
        return result

    @farine.execute.method()
    def watch(self):
        """
        Listen for deployments events.
        """
        from kubernetes import client, watch
        from defournement.models import Status, IntegrityError
        v1ext = client.ExtensionsV1beta1Api()
        w = watch.Watch()
        last_seen_version = 0
        for event in w.stream(v1ext.list_deployment_for_all_namespaces, resource_version=last_seen_version, timeout_seconds=0):
            if not event:
                continue
            if event['object'].metadata.namespace in self.exclude_namespaces:
                continue
            if event['type'] == 'ADDED':
                continue
            LOGGER.info("%s %s [%s] %s", event['type'], event['object'].kind, event['object'].metadata.namespace, event['object'].metadata.name)
            last_seen_version = event['object'].metadata.resource_version
            # Retrieve uid
            uid = event['object'].metadata.labels['uid']
            try:
                if event['type'] == 'DELETED':
                    Status.create(uid=uid, status='terminated')
                elif event['object'].status.unavailable_replicas in (None, 0):
                    Status.create(uid=uid, status='running')
                else:
                    Status.create(uid=uid, status='unhealthy')
            except IntegrityError:
                LOGGER.exception('Unknown deployment uid')
