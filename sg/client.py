# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
                        print_function)

import boto
import boto.ec2
import boto.vpc

import io
from pathlib import Path
from six import moves

from .models import Grant


DEFAULT_CONFIG = u"""[security_group]
region = {region}
path = ./security_groups
key_file = ./aws_key
"""


class Config(object):
    CONFIG_PATH = './sg.cfg'

    def __init__(self, config_path=None, region=None,
                 base_path='.'):
        config_parser = moves.configparser.SafeConfigParser()
        config_parser.readfp(io.StringIO(DEFAULT_CONFIG))
        config_parser.read([config_path])
        self.base_path = Path(base_path)
        self.config_path = config_path
        self.config = dict(config_parser.items('security_group'))
        self.region = region or self.config.get("region")
        self.key_file = self.config.get("key_file")

    def get_connection(self):
        if self.key_file:
            with Path(self.key_file).open() as fp:
                key, secretkey = fp.read().rstrip().split(':')
                args = dict(aws_access_key_id=key,
                            aws_secret_access_key=secretkey)
        else:
            args = dict()
        if self.region:
            return boto.ec2.connect_to_region(self.region, **args)
        else:
            return boto.connect_ec2(**args)

    def group_data_path(self):
        return Path(self.config['path']) / '.group.json'


class SgException(Exception):
    pass


class AwsClient(object):
    def __init__(self, context):
        self.context = context
        self.connection = context.get_connection()
        if not self.connection:
            raise SgException('cannot connect')

        self._groups = None

    @property
    def groups(self):
        if not self._groups:
            self._groups = self.connection.get_all_security_groups()
            return self._groups
        return self._groups

    def authorize(self, target_group, rule):
        group_data = self.get(group=target_group)
        if rule.cidr_ip:
            group_data.authorize(ip_protocol=rule.ip_protocol,
                                 from_port=rule.from_port,
                                 to_port=rule.to_port,
                                 cidr_ip=rule.cidr_ip,
                                 src_group=None)
        else:
            src_group = self.get(rule.group)
            group_data.authorize(ip_protocol=rule.ip_protocol,
                                 from_port=rule.from_port,
                                 to_port=rule.to_port,
                                 src_group=src_group)

    def remove_rule(self, target_group, rule):
        group_data = self.get(group=target_group)
        if rule.cidr_ip:
            group_data.revoke(ip_protocol=rule.ip_protocol,
                              from_port=rule.from_port,
                              to_port=rule.to_port,
                              cidr_ip=rule.cidr_ip,
                              src_group=None)
        else:
            src_group = self.get(rule.group)
            group_data.revoke(ip_protocol=rule.ip_protocol,
                              from_port=rule.from_port,
                              to_port=rule.to_port,
                              src_group=src_group)

    def get_list(self, group=None):
        for sg in self.groups:
            if group and sg.name != group:
                continue
            for rule in sg.rules:
                for grant in Grant.from_rule(rule):
                    yield grant

    def get(self, group):
        for sg in self.groups:
            if sg.name == group:
                return sg
        return None
