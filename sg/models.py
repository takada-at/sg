# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
                        print_function)

from collections import namedtuple


class Rule(namedtuple("Rule",
                      [u"ip_protocol", u"from_port",
                       u"to_port", u"cidr_ip", u"group"])):
    def as_dict(self):
        return {f: getattr(self, f)
                for f in self._fields}

    def as_line(self):
        rows = [self.ip_protocol,
                self.from_port,
                self.to_port,
                self.cidr_ip or self.group]
        return "\t".join(map(str, rows))


class Diff(object):
    def __init__(self, local_only, remote_only):
        self.local_only = local_only
        self.remote_only = remote_only


class Grant(object):
    @classmethod
    def from_rule(cls, rule):
        for grant in rule.grants:
            if rule.ip_protocol == "-1":
                continue
            obj = cls(ip_protocol=rule.ip_protocol,
                      from_port=str(rule.from_port),
                      to_port=str(rule.to_port),
                      cidr_ip=grant.cidr_ip,
                      group=grant.name or grant.group_id)
            yield obj

    @classmethod
    def keys(cls):
        return [u"ip_protocol", u"from_port",
                u"to_port", u"cidr_ip", u"group", u"comment"]

    def __init__(self, ip_protocol, from_port, to_port,
                 cidr_ip=None,
                 group=None,
                 comment=None):
        self.ip_protocol = ip_protocol
        self.from_port = from_port
        self.to_port = to_port
        self.cidr_ip = cidr_ip or None
        self.group = group or None
        self.comment = comment
        self.is_cidr_ip = cidr_ip is not None

    @property
    def grant(self):
        return self.cidr_ip or self.group

    @property
    def rule(self):
        return Rule(self.ip_protocol, self.from_port,
                    self.to_port, self.cidr_ip, self.group)

    def as_dict(self):
        return self.rule.as_dict()

    def __str__(self):
        rows = [self.rule.ip_protocol, self.rule.from_port,
                self.rule.to_port, self.grant]
        return "\t".join(rows)
