#-*- coding:utf-8 -*-
"""
Test the get rpc method
"""
#pylint:disable=wildcard-import,unused-wildcard-import,redefined-outer-name
import json
from .fixtures import *

def test_detail_default(deploydb1):
    """
    Test the detail method : must succeed.
    """
    entries = defournement.service.Defournement().detail('deploydb1owner', deploydb1)
    assert len(entries['results']) == 2

def test_detail_no_uid(deploydb1):
    """
    Test with a wrong uid : return an empty list.
    """
    entries = defournement.service.Defournement().detail('deploydb1owner', 'toto')
    assert len(entries['results']) == 0

def test_detail_no_owner(deploydb1):
    """
    Test with a wrong owner : return an empty list.
    """
    entries = defournement.service.Defournement().detail('toto', deploydb1)
    assert len(entries['results']) == 0
