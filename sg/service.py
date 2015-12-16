# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
                        print_function)

import csv
import json
from collections import OrderedDict
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
        sys.stdout.write_csv("Please respond with 'yes' or 'no'")


def to_str(obj):
    if isinstance(obj, dict):
        return {to_str(key): to_str(val)
                for key, val in obj.items()}
    elif obj is None:
        return obj
    else:
        return str(obj)


class FileService(object):
    @staticmethod
    def write_json(file_path, obj):
        with open(str(file_path), 'w') as fp:
            json.dump(obj, fp)

    @staticmethod
    def read_csv(file_path):
        with open(str(file_path), 'r') as fio:
            reader = csv.DictReader(fio)
            for row in reader:
                yield Grant(**to_str(row))

    @staticmethod
    def write_csv(file_path, data):
        print("save", file_path)
        with open(str(file_path), 'w') as fio:
            keys = Grant.keys()
            writer = csv.writer(fio)
            writer.writerow([to_str(val) for val in keys])
            for grant in data:
                vals = []
                row = grant.as_dict()
                for key in Grant.keys():
                    vals.append(to_str(row.get(key, '')))
                writer.writerow(vals)


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
        for grant in FileService.read_csv(target_file):
            yield grant

    @staticmethod
    def save_groups(config, client, path,
                    noconfirm=False):
        """グループ設定をまとめて保存.

        :param config:
        :param client:
        :param path:
        :param noconfirm:
        :return:
        """
        if not path.exists():
            path.mkdir()
        group_settings = []
        save_path_list = []
        for gr in client.groups:
            savepath = SgService.save(client=client, base_path=path,
                                      group=gr,
                                      noconfirm=noconfirm)
            if not savepath:
                continue
            save_path_list.append(savepath)
            group_settings.append(
                OrderedDict([('path', str(savepath.name)),
                             ('group', gr.name),
                             ('id', gr.id)]))
        group_path = config.group_data_path()
        FileService.write_json(group_path, group_settings)
        return save_path_list

    @staticmethod
    def save(client, base_path, group,
             noconfirm=False):
        """セキュリティグループ設定をcsvに保存.

        :param client: AwsClient
        :param base_path: 保存ディレクトリ
        :param group: グループ名
        :param noconfirm:
        :return:
        """
        file_path = base_path / ("%s.csv" % group.name)
        print("GROUP: %s" % group.name)
        diff = SgService.diff(client=client,
                              group=group.name,
                              target_file=file_path)
        more = ["+" + rule.as_line() for rule in diff.remote_only]
        more += ["-" + rule.as_line() for rule in diff.local_only]
        # 空でもファイルはつくっておく
        if not file_path.exists():
            FileService.write_csv(file_path, [])
        if not diff.remote_only and not diff.local_only:
            print("nothing changed")
            return file_path
        if not file_path.exists() or noconfirm:
            allow = True
        else:
            allow = _confirm("save this setting?",
                             more="\n".join(more))
        if not allow:
            return file_path
        grants = []
        if file_path.exists():
            for grant in SgService.read(file_path):
                if grant.rule not in diff.local_only:
                    grants.append(grant)
        for grant in client.get_list():
            if grant.rule in diff.remote_only:
                grants.append(grant)
        grants.sort(key=lambda x: x.grant)
        FileService.write_csv(file_path, grants)
        return file_path

    @staticmethod
    def diff(client, group, target_file):
        """差分取得.

        :param client:
        :param group:
        :param target_file:
        :return:
        """
        file_contents = set()
        groups = client.groups
        groups = {gr.id: gr for gr in groups}
        for grant in SgService.read(target_file):
            if grant.group in groups:
                # セキュリティグループIDを名前に変換.
                group_data = groups[grant.group]
                grant.group = group_data.name or group_data.id
            file_contents.add(grant.rule)
        current_rules = {grant.rule for grant in client.get_list(group)}
        return Diff(local_only=file_contents-current_rules,
                    remote_only=current_rules-file_contents)

    @staticmethod
    def diff_list(config, client, file_path_list):
        """複数ファイルの差分.

        :param config:
        :param client:
        :param file_path_list:
        :return:
        """
        if not file_path_list:
            file_path_list = SgService.list_files(config)
        diffs = []
        for file_path in file_path_list:
            file_path = Path(file_path)
            target_group = SgService.file_setting(config, file_path)
            diff = SgService.diff(client=client,
                                  group=target_group,
                                  target_file=file_path)
            if not diff.local_only and not diff.remote_only:
                continue
            diffs.append((target_group, diff))
        return diffs


    @staticmethod
    def list_files(config):
        """csvをリストアップ.

        :param config:
        :return:
        """
        pathobj = Path(config.config.get("path"))
        file_list = []
        for subpath in pathobj.glob("*.csv"):
            setting = SgService.file_setting(config, subpath)
            if not setting:
                continue
            file_list.append(subpath)
        return file_list

    @staticmethod
    def file_setting(config, target_file):
        """グループ設定を取得.

        :param config:
        :param target_file:
        :return:
        """
        group_setting = config.group_data_path()
        with group_setting.open() as fp:
            data = json.load(fp, object_pairs_hook=OrderedDict)
            for setting in data:
                if setting['path'] == target_file.name:
                    return setting['group']

    @staticmethod
    def commit(client, diff, target_group,
               noconfirm=False):
        """リモートに保存.

        :param client:
        :param diff:
        :param target_group:
        :return:
        """
        more = ["+" + rule.as_line() for rule in diff.local_only]
        more += ["-" + rule.as_line() for rule in diff.remote_only]
        if not more:
            return
        if noconfirm:
            allow = True
        else:
            allow = _confirm("post this setting?",
                             more="\n".join(more))
        if allow:
            for rule in diff.local_only:
                client.authorize(target_group=target_group,
                                 rule=rule)
                print("Add %s" % rule.as_line())
            for rule in diff.remote_only:
                client.remove_rule(target_group=target_group,
                                   rule=rule)
                print("Delete %s" % rule.as_line())


    @staticmethod
    def commit_list(config, client, file_path_list,
                    noconfirm=False):
        """まとめてリモート保存.

        :param config:
        :param client:
        :param file_path_list:
        :param noconfirm:
        :return:
        """
        if not file_path_list:
            file_path_list = SgService.list_files(config)
        for file_path in file_path_list:
            group = SgService.file_setting(config, file_path)
            if not group:
                continue
            diff = SgService.diff(client=client,
                                  group=group,
                                  target_file=file_path)
            SgService.commit(client=client,
                             diff=diff,
                             target_group=group,
                             noconfirm=noconfirm)
