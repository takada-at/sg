# -*- coding: utf-8 -*-
"""
EC2のセキュリティグループを取得したり、TSVからセキュリティグループを追加するよ
"""
from __future__ import (absolute_import, division,
                        print_function)

import click
from pathlib import Path

from .client import Config, AwsClient
from .service import SgService


@click.group()
@click.option('--config', type=click.Path(), default=Config.CONFIG_PATH)
@click.option('--region')
@click.pass_context
def group(ctx, config, region=None):
    myctx = Config(config_path=config, region=region)
    ctx.obj['config'] = myctx


@group.command()
@click.pass_context
def init(ctx):
    """初期化。
    """
    SgService.save_config(ctx.obj['config'])


@group.command()
@click.pass_context
def fetch(ctx):
    """セキュリティグループの設定をcsvに保存。
    """
    pathobj = Path(ctx.obj['config'].config.get("path"))
    if not pathobj.exists():
        print("mkdir %s" % pathobj)
        pathobj.mkdir(parents=True)
    sg = AwsClient(ctx.obj['config'])
    SgService.save_groups(config=ctx.obj['config'], client=sg, path=pathobj)


@group.command("diff")
@click.argument('file_path_list', type=click.Path(exists=True),
                nargs=-1)
@click.pass_context
def diff_(ctx, file_path_list):
    """差分表示
    """
    client = AwsClient(ctx.obj['config'])
    config = ctx.obj['config']
    diffs = SgService.diff_list(config=config, client=client,
                                file_path_list=file_path_list)
    for group_name, diff in diffs:
        print("GROUP: %s" % group_name)
        more = ["L:" + rule.as_line() for rule in diff.local_only]
        more += ["R:" + rule.as_line() for rule in diff.remote_only]
        print("\n".join(more))


@group.command()
@click.argument('file_path_list', type=click.Path(exists=True),
                nargs=-1)
@click.pass_context
def commit(ctx, file_path_list):
    """アカウントにCSVの内容変更を反映。
    """
    client = AwsClient(ctx.obj['config'])
    config = ctx.obj['config']
    SgService.commit_list(config=config,
                          client=client,
                          file_path_list=file_path_list)
