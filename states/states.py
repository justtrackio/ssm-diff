from __future__ import print_function
from botocore.exceptions import ClientError, NoCredentialsError
from .helpers import flatten, merge, add, search
import sys
import os
import yaml
import boto3
import termcolor


def str_presenter(dumper, data):
    if len(data.splitlines()) == 1 and data[-1] == '\n':
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='>')
    if len(data.splitlines()) > 1:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data.strip())


yaml.SafeDumper.add_representer(str, str_presenter)


class SecureTag(yaml.YAMLObject):
    yaml_tag = u'!secure'

    def __init__(self, secure):
        self.secure = secure

    def __repr__(self):
        return self.secure

    def __str__(self):
        return termcolor.colored(self.secure, 'magenta')

    def __eq__(self, other):
        return isinstance(other, SecureTag) and self.secure == other.secure

    def __hash__(self):
        return hash(self.secure)

    def __ne__(self, other):
        return not self.__eq__(other)

    @classmethod
    def from_yaml(cls, loader, node):
        return cls(node.value)

    @classmethod
    def to_yaml(cls, dumper, data):
        style = '|' if len(data.secure.splitlines()) > 1 else None
        return dumper.represent_scalar(cls.yaml_tag, data.secure, style=style)


yaml.SafeLoader.add_constructor('!secure', SecureTag.from_yaml)
yaml.SafeDumper.add_multi_representer(SecureTag, SecureTag.to_yaml)


class StateBase:
    def get(self, paths, flat=True):
        raise NotImplementedError

    def save(self, state):
        raise NotImplementedError


class LocalState(StateBase):
    def __init__(self, filename):
        self.filename = filename

    def get(self, paths, flat=True):
        try:
            with open(self.filename, 'rb') as f:
                data = yaml.safe_load(f.read())
            output = {}
            for path in paths:
                if path.strip('/'):
                    output = merge(output, search(data, path))
                else:
                    return flatten(data) if flat else data
            return flatten(output) if flat else output
        except IOError as e:
            print(e, file=sys.stderr)
            if e.errno == 2:
                print("Please, run init before doing plan!")
            sys.exit(1)
        except TypeError as e:
            if 'object is not iterable' in e.args[0]:
                return {}
            raise

    def save(self, state):
        try:
            with open(self.filename, 'wb') as f:
                content = yaml.safe_dump(state, default_flow_style=False)
                f.write(content.encode('utf-8'))
        except Exception as e:
            print(e, file=sys.stderr)
            sys.exit(1)


class S3State(StateBase):
    def __init__(self, bucket, key, profile, filename):
        self.s3 = boto3.client('s3', profile_name=profile) if profile else boto3.client('s3')
        self.bucket = bucket
        self.key = key
        self.filename = filename

    def save(self):
        kms_key_id = os.environ.get('KMS_KEY_ID')
        if not kms_key_id:
            print("Please set KMS_KEY_ID environment variable to encrypt the state file!")
            sys.exit(1)
        try:
            with open(self.filename, 'rb') as f:
                state = yaml.safe_load(f.read())
            self.s3.put_object(
                Bucket=self.bucket,
                Key=f"{self.key}/{self.filename}",
                Body=yaml.safe_dump(state),
                ServerSideEncryption='aws:kms',
                SSEKMSKeyId=kms_key_id
            )
            print(f"State saved to S3 bucket: {self.bucket}/{self.key}/{self.filename}")
        except ClientError as e:
            print("Failed to save parameters to S3!", e, file=sys.stderr)
            sys.exit(1)


class RemoteState(StateBase):
    def __init__(self, profile):
        self.ssm = boto3.client('ssm', profile_name=profile) if profile else boto3.client('ssm')

    def get(self, paths=['/', ], flat=True):
        paginator = self.ssm.get_paginator('get_parameters_by_path')
        output = {}
        for path in paths:
            try:
                for page in paginator.paginate(Path=path, Recursive=True, WithDecryption=True):
                    for param in page['Parameters']:
                        add(obj=output,
                            path=param['Name'],
                            value=self._read_param(param['Value'], param['Type']))
            except (ClientError, NoCredentialsError) as e:
                print("Failed to fetch parameters from SSM!", e, file=sys.stderr)

        return flatten(output) if flat else output

    def _read_param(self, value, ssm_type='String'):
        return SecureTag(value) if ssm_type == 'SecureString' else str(value)

    def apply(self, diff):
        for k in diff.added():
            ssm_type = 'StringList' if isinstance(diff.target[k], list) else 'SecureString' if isinstance(diff.target[k], SecureTag) else 'String'
            value = repr(diff.target[k]) if isinstance(diff.target[k], SecureTag) else str(diff.target[k])
            self.ssm.put_parameter(Name=k, Value=value, Type=ssm_type)

        for k in diff.removed():
            self.ssm.delete_parameter(Name=k)

        for k in diff.changed():
            ssm_type = 'SecureString' if isinstance(diff.target[k], SecureTag) else 'String'
            value = repr(diff.target[k]) if isinstance(diff.target[k], SecureTag) else str(diff.target[k])
            self.ssm.put_parameter(Name=k, Value=value, Overwrite=True, Type=ssm_type)
