AWS Security Group Management Tool.

## Install

```
$ python setup.py install
```

## Usage


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

```
$ sgsg.py fetch
mkdir security_groups
GROUP: group
save to security_groups/group.csv
```

download your 


# edit your csv

$ sgsg.py commit security_groups/some.csv
```