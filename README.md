AWSのセキュリティグループを管理するツールです。

セキュリティグループの設定をcsvでダウンロード、コメントをつけてバージョン管理、追加したものをAPI経由で保存という使い方ができます。

## インストール

```
$ pip install sg
```

OR

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

### リモートからローカルへの同期

リモートのセキュリティグループの設定を保存するには`fetch`コマンドを利用します。

```
$ sgsg.py fetch
mkdir security_groups
GROUP: group
save to security_groups/group.csv
```

ダウンロードされたcsvファイルにはコメントなどを追加することができます。エクセルなどで編集してください(文字コードはutf-8を想定しています)。

またセキュリティグループの設定を追加・削除し、リモートに反映することができます。


### ローカルからリモートへの同期

csvに追加、または削除を行なったあと、以下のコマンドを実行します。差分が表示されるので確認後yを選択してください。

```
sgsg.py commit security_groups/somegroup.csv
GROUP: somegroup
post this setting?[y/N]
+tcp    80      80      192.168.0.1
```
