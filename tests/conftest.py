# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
                        print_function)

import boto
import os
from pathlib import Path
import moto
import shutil
import tempfile
from sg.client import Config


def pytest_funcarg__tempdir(request):
    def final():
        shutil.rmtree(tempdir)

    tempdir = tempfile.mkdtemp()
    request.addfinalizer(final)
    os.chdir(tempdir)
    return Path(tempdir)


def pytest_funcarg__config(request):
    tempdir = pytest_funcarg__tempdir(request)
    with (tempdir / "aws_key").open("w") as fio:
        fio.write(u'dummy:dummy')
    config = Config("sge.cfg")
    config.region = None
    return config


def pytest_funcarg__mock_groups(request):
    def end():
        mock.stop()

    mock = moto.mock_ec2()
    mock.start()
    con = boto.connect_ec2()
    group = con.create_security_group("mock-group", "hoge")
    group2 = con.create_security_group("mock-group2", "description")
    group.authorize(ip_protocol="tcp", from_port=22, to_port=22,
                    cidr_ip="192.168.1.0/32")
    group.authorize(ip_protocol="tcp", from_port=22, to_port=22,
                    src_group=group2)
    request.addfinalizer(end)
    return [group, group2]
