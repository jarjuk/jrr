import pytest
import os
import re

from urllib.parse import urlparse, urlencode, parse_qs, urlunparse


def test_framework():
    assert 1 == 1


def test_str_class():
    cl = str
    assert cl.__name__ == str.__name__


def test_str_none_equal():
    assert not (None == "hello")
    assert not ("hello" == None)
    assert "hello" != None


def test_round():
    val = 11
    def next_8(val): return (int(val / 8) + (val % 8 > 0))*8
    assert next_8(7) == 8
    assert next_8(8) == 8
    assert next_8(11) == 16
    assert next_8(9) == 16
    assert next_8(127) == 128
    assert next_8(128) == 128
    assert next_8(129) == 136


def test_str_class_D():
    class D:
        pass
    cl = D
    print(f"{type(str)=}, {cl=}, {cl.__class__=}, {str.__class__}=")
    assert cl.__name__ == D.__name__
    assert cl.__name__ != str.__name__


# ------------------------------------------------------------------
# slice test

def test_str_slice():
    buf = "123"
    assert buf[0:] == "123"
    assert buf[1:] == "23"
    assert buf[:1] == "1"
    assert buf[:2] == "12"
    assert buf[1:2] == "2"

# ------------------------------------------------------------------
# urllib3.parse

def test_urlparse1():
    o = urlparse("file://dir1/dir2/koe.yaml")
    assert o.path == "/dir2/koe.yaml"
    assert o.netloc == "dir1"

    o = urlparse("file:///home/pi/dir/koe.yaml")
    assert o.netloc == ""
    assert o.path == "/home/pi/dir/koe.yaml"

    url = "http://google.com/pi/dir/koe.yaml"
    o = urlparse(url)
    assert o.netloc == "google.com"
    assert o.path == "/pi/dir/koe.yaml"
    assert os.path.dirname(o.path) == "/pi/dir"
    assert o.geturl() == url



def test_url_unparseparse1():

    url = "http://google.com/pi/dir/koe.yaml"
    o = urlparse(url)
    assert o.netloc == "google.com"
    assert o.path == "/pi/dir/koe.yaml"
    assert os.path.dirname(o.path) == "/pi/dir"
    assert o.geturl() == url

    new_path = os.path.dirname(o.path) + "/image.png"
    url2 = urlunparse(o._replace(path=new_path))
    assert url2 == "http://google.com/pi/dir/image.png"
    

# ------------------------------------------------------------------
# regexp

def test_rex1():
    line = "May 16 15:12:56 jrr5 jrr.sh[1715]: 2025-05-16:15:12:56,087 WARNING  [jrr_radio.py:1755] system_shutdown: starting"
    

