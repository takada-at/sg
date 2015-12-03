# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
                        print_function)

import csv
import json
from pathlib import Path
from six import moves
import sys

from .client import DEFAULT_CONFIG
from .models import Grant, Diff


def _confirm(message, more=None):
    print("%s[y/N]" % message)
    if more:
        print(more)
    yes = {'yes', 'y'}
    no = {'no', 'n', ''}
    choice = moves.input().lower()
    if choice in yes:
        return True
    elif choice in no:
        return False
    else:
        sys.stdout.write("Please respond with 'yes' or 'no'")


class SgService(object):
    @staticmethod
    def save_config(config):
        config_path = Path(config.config_path)
        if not config_path.exists():
            allow = True
        else:
            allow = _confirm("overwrite %s \nOK?" % str(config_path))
        if allow:
            print("enter your region[us-east-1]:")
            region = moves.input() or "us-east-1"
            with config_path.open("w") as fp:
                print("save to %s" % str(config_path))
                fp.write(DEFAULT_CONFIG.format(region=region))

        key_file = Path(config.config.get('key_file'))
        if key_file.exists():
            allow = _confirm("overwrite %s \nOK?" % str(key_file))
        else:
            allow = True
        if allow:
            print("enter your aws_access_key_id:")
            key_id = moves.input()
            print("enter your aws_secret_access_key:")
            secret_key = moves.input()
            if key_id and secret_key:
                print("save to %s" % key_file)
                with key_file.open("w") as fp:
                    fp.write(u"%s:%s" % (key_id, secret_key))

    @staticmethod
    def read(target_file):
        if not target_file.exists():
            raise StopIteration()
        with target_file.open('r') as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                grant = Grant(**row)
                yield grant

    @staticmethod
    def save_groups(config, client, path):
        if not path.exists():
            path.mkdir()
        group_settings = []
        for gr in client.groups:
            savepath = SgService.save(client=client, base_path=path,
                                      group=gr)
            if not savepath:
                continue
            group_settings.append(dict(path=str(savepath.name),
                                       group=gr.name,
                                       id=gr.id))

        group_path = config.group_data_path()
        if not group_path.exists():
            with group_path.open('wb') as fp:
                json.dump(group_settings, fp=fp)

    @staticmethod
    def save(client, base_path, group):
        file_path = base_path / ("%s.csv" % group.name)
        print("GROUP: %s" % group.name)
        diff = SgService.diff(client=client,
                              group=group.name,
                              target_file=file_path)
        more = ["+" + rule.as_line() for rule in diff.remote_only]
        more += ["-" + rule.as_line() for rule in diff.local_only]
        if not diff.remote_only and not diff.local_only:
            print("nothing changed")
            return
        if not file_path.exists():
            allow = True
        else:
            allow = _confirm("save this setting?",
                             more="\n".join(more))
        if not allow:
            return
        grants = []
        if file_path.exists():
            for grant in SgService.read(file_path):
                if grant.rule not in diff.local_only:
                    grants.append(grant)
        for grant in client.get_list():
            if grant.rule in diff.remote_only:
                grants.append(grant)
        grants.sort(key=lambda x: x.grant)
        with file_path.open("wb") as fp:
            print("save to %s" % file_path)
            writer = csv.DictWriter(fp, fieldnames=Grant.keys())
            writer.writeheader()
            for grant in grants:
                writer.writerow(grant.as_dict())
        return file_path

    @staticmethod
    def diff(client, group, target_file):
        file_contents = set()
        for grant in SgService.read(target_file):
            file_contents.add(grant.rule)
        current_rules = {grant.rule for grant in client.get_list(group)}
        return Diff(local_only=file_contents-current_rules,
                    remote_only=current_rules-file_contents)

    @staticmethod
    def file_setting(config, target_file):
        group_setting = config.group_data_path()
        with group_setting.open() as fp:
            data = json.load(fp)
            for setting in data:
                if setting['path'] == target_file.name:
                    return setting['group']

    @staticmethod
    def commit(client, diff, target_group):
        more = ["+" + rule.as_line() for rule in diff.local_only]
        more += ["-" + rule.as_line() for rule in diff.remote_only]
        if _confirm("post this setting?",
                    more="\n".join(more)):
            for rule in diff.local_only:
                client.authorize(target_group=target_group,
                                 rule=rule)
                print("Add %s" % rule.as_line())
            for rule in diff.remote_only:
                client.remove_rule(target_group=target_group,
                                   rule=rule)
                print("Delete %s" % rule.as_line())
