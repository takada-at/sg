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


def pytest_funcarg__files(request):
    from sg.client import AwsClient
    from sg.service import SgService
    config = pytest_funcarg__config(request)
    pytest_funcarg__mock_groups(request)
    tempdir = config.base_path
    client = AwsClient(config)
    path_list = SgService.save_groups(config, client,
                                      tempdir / 'security_groups',
                                      noconfirm=True)
    return path_list
