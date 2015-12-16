# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
                        print_function)

import mock
from pathlib import Path
from sg.client import Config, AwsClient
from sg.models import Rule, Grant
from sg.service import SgService, FileService


def test_save_config(tempdir):
    """SgService.save_config

    :param tempdir:
    :return:
    """
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


def test_diff_list(config, mock_groups):
    tempdir = config.base_path
    client = AwsClient(config)
    SgService.save_groups(config, client,
                          tempdir / 'security_groups',
                          noconfirm=True)
    file_path = tempdir / 'security_groups/mock-group.csv'
    assert file_path.exists()
    group = client.get('mock-group')
    group.revoke(ip_protocol="tcp", from_port=22, to_port=22,
                 cidr_ip="192.168.1.0/32")
    group.authorize(ip_protocol="tcp", from_port=22, to_port=22,
                    cidr_ip="192.168.1.10/32")
    group.authorize(ip_protocol="tcp", from_port=22, to_port=22,
                    cidr_ip="192.168.1.20/32")
    group2 = client.get('mock-group2')
    group2.authorize(ip_protocol="tcp", from_port=22, to_port=22,
                     cidr_ip="192.168.1.10/32")
    diff_list = SgService.diff_list(config, AwsClient(config), [])
    dic = dict(diff_list)
    diff0 = dic['mock-group']
    assert 2 == len(diff0.remote_only)
    assert 1 == len(diff0.local_only)
    # remoteで削除したもの
    assert diff0.local_only == {Rule("tcp", "22", "22",
                                     cidr_ip="192.168.1.0/32",
                                     group=None)}
    # remoteに追加したもの
    assert diff0.remote_only == {Rule("tcp", "22", "22",
                                      cidr_ip="192.168.1.10/32",
                                      group=None),
                                 Rule("tcp", "22", "22",
                                      cidr_ip="192.168.1.20/32",
                                      group=None),
                                 }
    diff1 = dic['mock-group2']
    assert diff1.local_only == set()
    # remoteに追加したもの
    assert diff1.remote_only == {Rule("tcp", "22", "22",
                                      cidr_ip="192.168.1.10/32", group=None)}


def test_commit(config, mock_groups):
    """SgService.commitのテスト.

    :param config:
    :param mock_groups:
    :return:
    """
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


def test_list_files_local(config, files):
    """SgService.list_files_localのテスト.

    :param config:
    :param files:
    :return:
    """
    get_files = SgService.list_files_local(config)
    assert set(files) == set(get_files)


def test_commit_list(config, files):
    tempdir = config.base_path
    base = tempdir / 'security_groups'
    client = AwsClient(config)
    group = client.get('mock-group')
    group2 = client.get('mock-group2')
    group.revoke(ip_protocol="tcp", from_port=22, to_port=22,
                 cidr_ip="192.168.1.0/32")
    group.revoke(ip_protocol="tcp", from_port=22, to_port=22,
                 src_group=group2)
    gr0 = Grant(ip_protocol="tcp", from_port="22", to_port="22",
                cidr_ip="192.168.10.0/32")
    gr1 = Grant(ip_protocol="tcp", from_port="33", to_port="44",
                group="mock-group2")
    gr2 = Grant(ip_protocol="tcp", from_port="22", to_port="22",
                cidr_ip="192.168.20.0/32")
    FileService.write_csv(base / "mock-group.csv",
                          [
                              gr0,
                              gr1,
                              ])
    FileService.write_csv(base / "mock-group2.csv",
                          [
                              gr2,
                              ])
    diff_list = dict(SgService.diff_list(config, AwsClient(config), []))
    diff0 = diff_list['mock-group']
    assert diff0.local_only == {gr0.rule, gr1.rule}
    assert diff_list['mock-group2'].local_only == {gr2.rule}
    SgService.commit_list(config=config, client=AwsClient(config),
                          file_path_list=[],
                          noconfirm=True)
    diff_list = dict(SgService.diff_list(config, AwsClient(config), []))
    assert "mock-group" not in diff_list
    assert "mock-group2" not in diff_list
