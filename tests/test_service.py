# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
                        print_function)

import mock
from pathlib import Path
from sg.client import Config, AwsClient
from sg.models import Rule
from sg.service import SgService


def test_save_config(tempdir):
    config = Config("sge.cfg")
    with mock.patch("sg.service._confirm") as dummy:
        dummy.return_value = True
        with mock.patch("six.moves.input") as dum2:
            dum2.return_value = "dummy"
            SgService.save_config(config)
            assert (tempdir / 'sge.cfg').exists()
            assert (tempdir / 'aws_key').exists()


def test_save(config, mock_groups):
    with mock.patch("sg.service._confirm") as dummy:
        dummy.return_value = True
        client = AwsClient(config)
        SgService.save_groups(config, client,
                              config.base_path / 'security_groups')
        assert Path(config.base_path / 'security_groups/mock-group.csv').exists()


def test_diff(config, mock_groups):
    tempdir = config.base_path
    with mock.patch("sg.service._confirm") as dummy:
        dummy.return_value = True
        client = AwsClient(config)
        SgService.save_groups(config, client,
                              tempdir / 'security_groups')
        file_path = tempdir / 'security_groups/mock-group.csv'
        assert file_path.exists()
        group = client.get('mock-group')
        group.revoke(ip_protocol="tcp", from_port=22, to_port=22,
                     cidr_ip="192.168.1.0/32")
        group.authorize(ip_protocol="tcp", from_port=22, to_port=22,
                        cidr_ip="192.168.1.10/32")
        group.authorize(ip_protocol="tcp", from_port=22, to_port=22,
                        cidr_ip="192.168.1.20/32")
        diff = SgService.diff(AwsClient(config), 'mock-group', file_path)
        assert 2 == len(diff.remote_only)
        assert 1 == len(diff.local_only)
        # remoteで削除したもの
        assert diff.local_only == {Rule("tcp", "22", "22",
                                        cidr_ip="192.168.1.0/32",
                                        group=None)}
        # remoteに追加したもの
        assert diff.remote_only == {Rule("tcp", "22", "22",
                                         cidr_ip="192.168.1.10/32",
                                         group=None),
                                    Rule("tcp", "22", "22",
                                         cidr_ip="192.168.1.20/32",
                                         group=None),
                                    }


def test_commit(config, mock_groups):
    tempdir = config.base_path
    with mock.patch("sg.service._confirm") as dummy:
        dummy.return_value = True
        client = AwsClient(config)
        SgService.save_groups(config, client,
                              tempdir / 'security_groups')
        file_path = tempdir / 'security_groups/mock-group.csv'
        assert file_path.exists()
        group = client.get('mock-group')
        group.revoke(ip_protocol="tcp", from_port=22, to_port=22,
                     cidr_ip="192.168.1.0/32")
        group.authorize(ip_protocol="tcp", from_port=22, to_port=22,
                        cidr_ip="192.168.1.10/32")
        group.authorize(ip_protocol="tcp", from_port=22, to_port=22,
                        cidr_ip="192.168.1.20/32")
        diff = SgService.diff(AwsClient(config), 'mock-group', file_path)
        SgService.commit(client, diff, group.name)
        client = AwsClient(config)
        # remoteに反映されることを確認
        grants = list(client.get_list("mock-group"))
        rules = [grant.rule for grant in grants]
        # さっきrevokeしたものが復活している
        assert Rule(ip_protocol="tcp", from_port="22", to_port="22",
                    cidr_ip="192.168.1.0/32", group=None) in rules
        assert Rule(ip_protocol="tcp", from_port="22", to_port="22",
                    cidr_ip="192.168.1.10/32", group=None) not in rules
