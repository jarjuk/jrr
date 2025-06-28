import pytest

import datetime


def test_framework():
    assert 1 == 1


def test_delta_0():
    dt1  = datetime.datetime(year=2002, month=12, day=1, hour=1, minute=1, second=0, microsecond=0 )
    dt2  = dt1
    diff = dt2 - dt1

    assert diff.total_seconds() == 0

def test_delta_1s():
    dt1  = datetime.datetime(year=2002, month=12, day=1, hour=1, minute=1, second=0, microsecond=0 )
    dt2  = datetime.datetime(year=2002, month=12, day=1, hour=1, minute=1, second=1, microsecond=0 )
    diff = dt2 - dt1

    assert diff.total_seconds() == 1.0
    assert diff.total_seconds()*1000 == 1000    
    
def test_delta_1us():
    dt1  = datetime.datetime(year=2002, month=12, day=1, hour=1, minute=1, second=0, microsecond=0 )
    dt2  = datetime.datetime(year=2002, month=12, day=1, hour=1, minute=1, second=0, microsecond=1 )
    diff = dt2 - dt1

    assert diff.total_seconds() == 1.0/10**6
    assert diff.microseconds == 1.0

def test_delta_2us():
    max_us = 1000000
    expect_ms = 2/1000
    dt1  = datetime.datetime(year=2002, month=12, day=1, hour=1, minute=1, second=0, microsecond=max_us-1 )
    dt2  = datetime.datetime(year=2002, month=12, day=1, hour=1, minute=1, second=1, microsecond=1 )
    diff = dt2 - dt1

    assert diff.total_seconds() == 2.0/10**6
    assert diff.microseconds == 2.0
    
    
def test_delta_2s2us():
    max_us = 1000000
    expect_ms = 2/1000
    dt1  = datetime.datetime(year=2002, month=12, day=1, hour=1, minute=1, second=0, microsecond=max_us-1 )
    dt2  = datetime.datetime(year=2002, month=12, day=1, hour=1, minute=1, second=2, microsecond=1 )
    diff = dt2 - dt1

    assert diff.total_seconds() == (1.0+ 2.0/10**6)
    assert diff.microseconds == 2.0
    

def test_delta_2ms():
    max_us = 1000000
    expect_ms = 2
    dt1  = datetime.datetime(year=2002, month=12, day=1, hour=1, minute=1, second=0, microsecond=0 )
    dt2  = datetime.datetime(year=2002, month=12, day=1, hour=1, minute=1, second=0, microsecond=2000 )
    diff = dt2 - dt1

    assert diff.total_seconds() == 0.002
    assert diff.total_seconds() == expect_ms/1000
    
    
    
