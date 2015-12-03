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


@group.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.pass_context
def commit(ctx, file_path):
    """アカウントにCSVの内容変更を反映。
    """
    sg = AwsClient(ctx.obj['config'])
    file_path = Path(file_path)
    target_group = SgService.file_setting(ctx.obj['config'], file_path)
    print("GROUP: %s" % target_group)
    if not target_group:
        return
    diff = SgService.diff(client=sg,
                          group=target_group,
                          target_file=file_path)
    if not diff.local_only and not diff.remote_only:
        print("nothing changed")
        return

    SgService.commit(client=sg, target_group=target_group,
                     diff=diff)
