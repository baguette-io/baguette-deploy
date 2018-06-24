import json
from .fixtures import *

def test_watch_ok(defour, caplog):
    """
    Watch deployments: must succeed anyway.
    """
    import logging
    obj = mock.Mock()
    obj.kind = 'deployment'
    obj.metadata = mock.Mock()
    obj.metadata.namespace = 'toto-default'
    obj.metadata.name = 'toto'
    obj.metadata.labels = {'owner':'owner', 'branch': 'branch', 'repo': 'repo', 'uid':'uid'}
    events = [{'type':'MODIFIED', 'object':obj}]
    with mock.patch('kubernetes.watch.Watch.stream', mock.Mock(return_value=events)) as stream:
        defour.watch()
        assert caplog.record_tuples == [('defournement.service', logging.INFO, 'MODIFIED deployment [toto-default] toto'),
                                         ('defournement.service', logging.ERROR, 'Unknown deployment uid')]

def test_watch_exclude(defour, caplog):
    """
    Watch deployment in an exluded namespace: must skip it.
    """
    obj = mock.Mock()
    obj.kind = 'deployment'
    obj.metadata = mock.Mock()
    obj.metadata.namespace = 'kube-system'
    obj.metadata.name = 'toto'
    obj.metadata.labels = {'owner':'owner', 'branch': 'branch', 'repo': 'repo', 'uid':'uid'}
    events = [{'type':'MODIFIED', 'object':obj}]
    with mock.patch('kubernetes.watch.Watch.stream', mock.Mock(return_value=events)) as stream:
        defour.watch()
        assert caplog.record_tuples == []
