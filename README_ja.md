AWSのセキュリティグループを管理するツールです。

## インストール

```
$ python setup.py install
```

## 使い方
適当なディレクトリで初期化コマンドを実行してください。

設定が保存されます。

```
$ cd yourpath
$ sgsg.py init
enter your region[us-east-1]:
us-west-2
save to sg.cfg
enter your aws_access_key_id:
xxx
enter your aws_secret_access_key:
xxx
save to aws_key
```

セキュリティグループの設定を保存します。

```
$ sgsg.py fetch
mkdir security_groups
GROUP: group
save to security_groups/group.csv
```

ダウンロードされたcsvファイルにはコメントなどを追加することができます。

またセキュリティグループの設定を追加することも可能です。

追加した設定を反映するには以下のコマンドを実行してください。

```
$ sgsg.py commit security_groups/some.csv
```
