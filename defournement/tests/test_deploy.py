#-*- coding:utf-8 -*-
"""
Test the deployment process.
"""
#pylint:disable=wildcard-import,unused-wildcard-import,redefined-outer-name
from .fixtures import *

def test_create_ok(definition1, request_factory):
    """
    Deploy a recipe that does work.
    """
    request = request_factory(200, {})
    with mock.patch('kubernetes.client.rest.RESTClientObject.request', mock.Mock(return_value=request)):
        service = defournement.service.Defournement()
        assert service.create(definition1, mock.Mock())

def test_create_ko_400(definition1, request_factory):
    """
    Deploy a recipe that does not work: raises http code 400.
    """
    request = request_factory(400, {})
    with mock.patch('kubernetes.client.rest.RESTClientObject.request', mock.Mock(return_value=request)) as deployment:
        deployment.side_effect = ApiException(400)
        service = defournement.service.Defournement()
        assert not service.create(definition1, mock.Mock())

def test_create_ko_404(definition1, request_factory):
    """
    Deploy a recipe that does not work: raises http code 404.
    """
    request = request_factory(404, {})
    with mock.patch('kubernetes.client.rest.RESTClientObject.request', mock.Mock(return_value=request)) as deployment:
        deployment.side_effect = ApiException(404)
        service = defournement.service.Defournement()
        assert not service.create(definition1, mock.Mock())

def test_create_ko_409(definition1, request_factory):
    """
    Deploy a recipe that does not work: raises http code 409.
    """
    request = request_factory(409, {})
    with mock.patch('kubernetes.client.rest.RESTClientObject.request', mock.Mock(return_value=request)) as deployment:
        deployment.side_effect = ApiException(409)
        service = defournement.service.Defournement()
        assert not service.create(definition1, mock.Mock())


def test_delete_ok(deploydb1, request_factory):
    """
    Stop an existing deployment : must return True.
    """
    request = request_factory(200, {})
    with mock.patch('kubernetes.client.rest.RESTClientObject.request', mock.Mock(return_value=request)) as deployment:
        service = defournement.service.Defournement()
        assert service.delete('deploydb1owner', deploydb1)

def test_delete_non_exist(deploydb1, request_factory):
    """
    Stop a non existing deployment : must return True.
    """
    request = request_factory(404, {})
    with mock.patch('kubernetes.client.rest.RESTClientObject.request', mock.Mock(return_value=request)) as deployment:
        deployment.side_effect = ApiException(404)
        service = defournement.service.Defournement()
        assert service.delete('deploydb1owner', deploydb1)

def test_delete_non_exist_2(deploydb1, request_factory):
    """
    Stop a non existing deployment that we cannot retrieve from db : must return True.
    """
    service = defournement.service.Defournement()
    assert service.delete('deploydb1owner', 'xxx')

def test_delete_ko(deploydb1, request_factory):
    """
    Stop an existing deployment which returns an unexpected error : must return False.
    """
    request = request_factory(409, {})
    with mock.patch('kubernetes.client.rest.RESTClientObject.request', mock.Mock(return_value=request)) as deployment:
        with mock.patch('defournement.components.deployment.exists', mock.Mock(return_value=True)):
            deployment.side_effect = ApiException(409)
            service = defournement.service.Defournement()
            assert not service.delete('deploydb1owner', deploydb1)
