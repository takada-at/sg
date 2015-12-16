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

以下AWS上に保存された設定を「リモート設定」、csvとして保存されている設定を「ローカル設定」と呼びます。

リモート設定を保存するには`fetch`コマンドを利用します。

```
$ sgsg.py fetch
mkdir security_groups
GROUP: group
save to security_groups/group.csv
```

ダウンロードされたcsvファイルにはコメントなどを追加することができます。エクセルなどで編集してください(文字コードはutf-8を想定しています)。

またセキュリティグループの設定を追加・削除し、リモートに反映することができます。


### 差分の表示

ローカルとリモートの差分を表示するには`diff`コマンドを使用します。

`L:`とついているのはローカル設定だけにあるもの、`R:`とついているのはリモート設定だけにあるものです。

```
$ sgsg.py diff
GROUP: somegroup
L:tcp   22      22      192.168.11.1/32
R:tcp   22      22      0.0.0.0/32
```

### ローカルからリモートへの同期

更新を反映するには`commit`コマンドを使用します。

csvに追加、または削除を行なったあと、以下のコマンドを実行します。差分が表示されるので確認後yを選択してください。

```
sgsg.py commit security_groups/somegroup.csv
GROUP: somegroup
post this setting?[y/N]
+tcp    80      80      192.168.0.1
```
