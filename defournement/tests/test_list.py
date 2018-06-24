#-*- coding:utf-8 -*-
"""
Test the get rpc method
"""
#pylint:disable=wildcard-import,unused-wildcard-import,redefined-outer-name
import json
from .fixtures import *

def test_get_default_limit(deploydb1, deploydb1bis, deploydb2):
    """
    Test the get method with the default limit: must succeed.
    """
    entries = defournement.service.Defournement().list('deploydb1owner')
    assert entries['count'] == 2
    assert len(entries['results']) == 2
    assert json.loads(entries['results'][0])['uid'] == deploydb1bis
    assert json.loads(entries['results'][1])['uid'] == deploydb1

def test_get_specific_limit(deploydb1, deploydb1bis, deploydb2):
    """
    Test the get method with a limit set to 1 : must succeed.
    """
    entries = defournement.service.Defournement().list('deploydb1owner', 0, 1)
    assert entries['count'] == 2
    assert len(entries['results']) == 1
    ##
    entry = json.loads(entries['results'][0])
    assert entry.has_key('uid')
    assert entry.has_key('status')
    assert entry['uid'] == deploydb1bis

def test_get_specific_offset(deploydb1, deploydb1bis, deploydb2):
    """
    Test the get method with an offset set to 1 : must succeed.
    """
    entries = defournement.service.Defournement().list('deploydb1owner', 1)
    assert entries['count'] == 2
    assert len(entries['results']) == 1
    ##
    entry = json.loads(entries['results'][0])
    assert entry['uid'] == deploydb1
