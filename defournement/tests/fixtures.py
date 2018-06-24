#-*- coding:utf-8 -*-
import json
import datetime
import mock
import multiprocessing
import os
import random
import shutil
import string
import time
import uuid
import pytest
import defournement
import defournement.service
import farine.exceptions
import farine.rpc
import farine.settings
from pytest_rabbitmq.factories.client import clear_rabbitmq
from farine.tests.fixtures import *
from kubernetes.client.rest import ApiException
from pytest_postgresql import factories

postgresql_proc = factories.postgresql_proc()
postgres = factories.postgresql('postgresql_proc')

def gen_str(length=15):
    """
    Generate a string of `length`.
    """
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in xrange(length))

@pytest.fixture(autouse=True)
def init(postgres, tmpdir):
    """
    auto load the settings and init the db.
    """
    farine.settings.load()
    farine.settings.defournement['ca_file'] = str(tmpdir)
    farine.settings.defournement['cert_file'] = str(tmpdir)
    farine.settings.defournement['key_file'] = str(tmpdir)
    db = farine.connectors.sql.setup(farine.settings.defournement)
    db.execute_sql('CREATE TABLE "deployment" ("uid" VARCHAR(255) NOT NULL PRIMARY KEY, "namespace" VARCHAR(255) NOT NULL, "name" VARCHAR(255) NOT NULL, "owner" VARCHAR(255) NOT NULL, "date_created" TIMESTAMP DEFAULT NOW())')
    db.execute_sql('CREATE TABLE "status" ("id" SERIAL NOT NULL PRIMARY KEY, "uid_id" VARCHAR(255) NOT NULL, "status" VARCHAR(255) NOT NULL, "date_created" TIMESTAMP DEFAULT NOW(), FOREIGN KEY(uid_id) REFERENCES deployment(uid))')
    db.close()
    farine.connectors.sql.init('defournement', db)


@pytest.fixture()
def definition_factory():
    """
    Definition factory, used by the deploy module.
    """
    def factory(instances=1, cpu=1, memory=1024, ports=None, private=True, health=None, domain=None):
        definition = {'uid':uuid.uuid4().hex , 'instances':instances, 'owner' : gen_str(), 'branch': gen_str(), 'repo': gen_str(), 'namespace': gen_str()}
        definition['ports'] = []
        ports = ports or []
        for port in ports:
            definition['ports'].append({'number':port, 'protocol':'tcp', 'name':'http'})
        definition['cpu'] = cpu
        definition['memory'] = memory
        definition['name'] = '{0}-{1}-{2}'.format(definition['owner'], definition['repo'], definition['branch']).lower()
        definition['tag'] = os.path.join('docker://', '{0}-{1}-{2}:{3}'.format(definition['owner'], definition['repo'], definition['branch'], definition['uid']).lower())
        definition['private'] = private
        definition['healthchecks'] = health or []
        definition['domain_name'] = domain
        return {'definition': definition}
    return factory

@pytest.fixture()
def definition1(definition_factory):
    return definition_factory(ports=[80], private=True)

@pytest.fixture()
def definition2(definition_factory):
    return definition_factory(ports=[1,8000], private=False, health=[{'interval_seconds': 10,
                      'initial_delay_seconds': 3,
                      'failure_threshold': 5,
                      'success_threshold': 5,
                      'path': '/',
                      'port': 8000,
                      'protocol': 'HTTP',
                      'type': 'readiness',
                      'timeout_seconds': 10},
                     {'initial_delay_seconds': 3,
                      'interval_seconds': 10,
                      'failure_threshold': 5,
                      'success_threshold': 5,
                      'protocol': 'COMMAND',
                      'timeout_seconds': 10,
                      'type': 'liveness',
                      'value': '/usr/bin/ls'}], domain='mybranch.myrepo.owner.projects.baguette.io')

def _rpc_server(callback_name):
    server = defournement.service.Defournement()
    farine.settings.load()
    farine.rpc.Server(service='defournement', callback_name=callback_name, callback=getattr(server, callback_name), name='defournement').start()

@pytest.fixture()
def rpc_server_factory(request, rabbitmq_proc, rabbitmq):
    def factory(callback_name):
        process = multiprocessing.Process(
            target=lambda:_rpc_server(callback_name),
        )
        def cleanup():
            process.terminate()
            clear_rabbitmq(rabbitmq_proc, rabbitmq)
        request.addfinalizer(cleanup)
        process.start()
        time.sleep(5)
        return process
    return factory


@pytest.fixture
def db_factory():
    def factory(owner, repo, branch, fail=False, date_created=None):
        from defournement.models import Deployment, Status
        uid = uuid.uuid4().hex
        name = '{}-{}-{}'.format(owner, repo, branch)
        namespace = 'default'
        Deployment.create(owner=owner, uid=uid, name=name, namespace=namespace, date_created=date_created)
        status = ['deploying', 'aborted'] if fail else ['deploying', 'running']
        for state in status:
            Status.create(uid=uid, status=state, date_created=date_created)
        return uid
    return factory

@pytest.fixture
def deploydb1(db_factory):
    u1 = db_factory('deploydb1owner', 'deploydb1repo', 'deploydb1branch', fail=False, date_created=datetime.datetime(2000,1,1,0,0))
    return u1

@pytest.fixture
def deploydb1bis(db_factory):
    u1bis = db_factory('deploydb1owner', 'deploydb1repobis', 'deploydb1branchbis', fail=True, date_created=datetime.datetime.now())
    return u1bis

@pytest.fixture
def deploydb2(db_factory):
    return db_factory('deploydb2owner', 'deploydb2repo', 'deploydb2branch', fail=False, date_created=datetime.datetime.now())

@pytest.fixture()
def request_factory():
    def factory(status, data, reason=''):
        import kubernetes.client.rest
        resp = mock.Mock()
        resp.status = status
        resp.data = json.dumps(data)
        resp.reason = reason
        return kubernetes.client.rest.RESTResponse(resp)
    return factory

@pytest.fixture()
def defour():
    return defournement.service.Defournement()
