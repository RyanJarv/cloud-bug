"""Main module."""
import http.client
from string import Template
import json
import os
import shutil
import subprocess
import tempfile
from random import randrange
from typing import Optional, List
import urllib.request
import platform
import zipfile

import botocore
from mypy_boto3_ecs.type_defs import NetworkConfigurationTypeDef

import boto3

DEFAULT_IMAGE = 'aaaguirrep/offensive-docker'
DOWNLOAD_BASE_URL = 'https://cloud-debug.amazonwebservices.com/release/metadata'  # 'darwin_amd64/1/latest-version'
DEBUG_TASK_ROLE_NAME = 'cloud-bug-ecs-sidecar-task'


class CloudDebug:
    def __init__(self, aws_session: boto3.session.Session):
        self.session = aws_session
        self.base_dir = os.path.expanduser("~/.cloud-bug")
        self.cloud_debug_path = os.path.join(self.base_dir, 'bin', 'cloud-debug')
        self.debug_role_arn: Optional[str] = None

    def setup(self, update=False) -> 'CloudDebug':
        fetch_executable(self.cloud_debug_path, update)
        self.debug_role_arn = task_role_arn(self.session, DEBUG_TASK_ROLE_NAME)
        return self

    def run(self, *args) -> subprocess.CompletedProcess:
        run_args = [self.cloud_debug_path] + args
        print("[DEBUG] Running cloud-debug with '{}'".format(run_args))
        result = subprocess.run(run_args)
        print("[INFO] cloud-debug exited with code {}".format(result.returncode))
        return result


def default_subnet_ids(sess: boto3.session.Session, vpc_id: str):
    ec2 = sess.client('ec2')
    resp = ec2.describe_subnets(Filters=[
        {
            'Name': 'isDefault',
            'Values': [True]
        },
        {
            'Name': 'vpc-id',
            'Values': [vpc_id]
        }
    ])
    return [subnet['SubnetId'] for subnet in resp['Subnets']]


# If default subnets can only exist in a default vpc this function probably isn't needed
def get_default_vpc_id(sess: boto3.session.Session) -> str:
    ec2 = sess.client('ec2')
    resp = ec2.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': [True]}])
    if len(resp['Vpcs']) == 0:
        raise UserWarning('Could not find default vpc, try rerunning using the --subnet option')
    return resp['Vpcs'][0]['VpcId']


def default_security_groups(sess: boto3.session.Session, vpc_id: str) -> List[str]:
    ec2 = sess.client('ec2')

    resp = ec2.describe_security_groups(Filters=[
        {'Name': 'group-name', 'Values': ['default']},
        {'Name': 'vpc-id', 'Values': [vpc_id]},
    ])
    if len(resp['SecurityGroups']) == 0:
        raise UserWarning('Could not find default security group')

    return [group['GroupId'] for group in resp['SecurityGroups']]


def task_role_arn(session: boto3.session.Session) -> [str, bool]:
    """This is used for both the original deployed service and the copy that cloud-debug creates."""
    iam = session.client("iam")

    try:
        resp = iam.get_role(DEBUG_TASK_ROLE_NAME)
        role_arn = resp['Role']['Arn']
        print("[INFO] Found existing cloud-debug role {}".format(role_arn))
        return role_arn, False
    except botocore.errorfactory.NoSuchEntityException:
        pass

    policy_doc = '''
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
'''

    #TODO: if this fails look for a role that has the right permissions that we can reuse
    resp = iam.create_role(RoleName=DEBUG_TASK_ROLE_NAME, AssumeRolePolicyDocument=policy_doc)
    iam.attach_role_policy(RoleName=DEBUG_TASK_ROLE_NAME, PolicyArn='arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore')
    return resp['Role']['Arn'], True

class EcsEnv:
    def __init__(
        self,
        aws_session: boto3.session.Session,
        cluster: Optional[str] = None,
        task_definition: Optional[str] = None,
        task_role: Optional[str] = None,
        security_groups: Optional[List[str]] = None,
        subnets: Optional[List[str]] = None,
    ):
        self.session = aws_session

        self.security_groups = security_groups
        self._created_task_role = False
        self.task_role = task_role
        self.cluster = cluster
        self.subnets = subnets

    def create(self):
        """Get's defaults or creates resources that where not set explicitly"""
        s = self.session

        self.security_groups = self.security_groups or default_security_groups(s)
        self.task_role, self._created_task_role = self.task_role or task_role_arn(s)
        #self.cluster = self.cluster or default_cluster(s)
        self.subnets = self.subnets or default_subnet_ids(s, get_default_vpc_id(s))
        self.account_id = sts.get_caller_identity()['Account']

    def destroy(self):
        """Cleans up anything we created"""

        if self._created_task_role:
            iam = self.session.client('iam')
            try:
                iam.delete_role(RoleName=DEBUG_TASK_ROLE_NAME)
            except iam.exceptions.NoSuchEntityException:
                print("[INFO] role {} doesn't exist".format(DEBUG_TASK_ROLE_NAME))
            except iam.exceptions.DeleteConflictException:
                print("[WARN] could not delete the {} role, may need to delete this manually".format(DEBUG_TASK_ROLE_NAME))




class EcsService:
    def __init__(
        self,
        ecs_env: EcsEnv,
        service_name: Optional[str] = None,
        image: Optional[str] = None,
    ):
        self.env = ecs_env
        self.image = image or DEFAULT_IMAGE
        self.service_name = service_name or "cloud-bug-{}".format(randrange(100, 999))
        self.task_definition = self.task_definition()
        self.service = None

    def create(self):
        ecs = self.env.session.client('ecs')
        resp = ecs.create_service(
            cluster=self.env.cluster,
            serviceName=self.service_name,
            taskDefinition=self.task_definition,
            desiredCount=1,
            launchType='FARGATE',
            platformVersion='1.4.0',
            networkConfiguration={
                'awsvpcConfiguration': { 'subnets': self.env.subnets },
                'securityGroups': self.env.subnets,
                'assignPublicIp': 'ENABLED'
            },
            schedulingStrategy='REPLICA',
        )
        self.service = resp['service']

    def destroy(self):
        raise NotImplementedError("resources must be cleaned up manually for now")

    def task_definition(self) -> str:
        task_template = Template("""
            {
                "taskRoleArn": "${task_role_arn}",
                "containerDefinitions": [
                    {
                        "image": "${image}",
                        "interactive": true,
                        "essential": true,
                        "pseudoTerminal": true,
                        "name": "${task_name}"
                    }
                ],
                "family": "${task_name}",
                "requiresCompatibilities": [
                    "FARGATE"
                ],
                "networkMode": "awsvpc",
                "memory": "512",
                "cpu": "256",
            }
        """)
        return task_template.substitute(mapping={
            'task_role_arn': self.env.task_role,
            'image': self.image,
            'task_name': self.service_name
        })

# def default_cluster(sess: boto3.session.Session) -> str:
#     ecs = sess.client('ecs')
#     resp = ecs.describe_clusters(clusters=['default'])
#     if len(resp['failures']) != 0:
#         for failure in resp['failures']:
#             raise UserWarning(json.dumps(failure))
#
#     if len(resp['clusters']) != 1:
#         raise UserWarning('''
# Could not find the default ECS cluster, try specifying one with --cluster or create it with:
#     aws ecs create-cluster --name default
# ''')
#
#     return resp['clusters'][0]['clusterArn']










def fetch_executable(download_path, update=False) -> str:
    if not update or os.path.exists(download_path):
        print("[INFO] Skipping cloud-debug download, use --update to force re-downloading")
        return
    else:
        path = latest_version_path()
        print("[INFO] Fetching cloud-debug from {}".format(path))

        zip_path: str
        with urllib.request.urlopen(path) as resp:
            tmp_dir = tempfile.TemporaryDirectory()

            with tempfile.NamedTemporaryFile() as f:
                zip_path = f.name
                f.write(resp.read())

                zipfile.ZipFile(zip_path).extractall(tmp_dir.name)

        src = os.path.join(tmp_dir.name, 'cloud-debug')
        os.makedirs(os.path.dirname(download_path), exist_ok=True)
        shutil.copy(src, download_path)
        os.chmod(path=download_path, mode=0o755)
        print("[INFO] cloud-debug downloaded and extracted to {}.".format(self.cloud_debug_path))

        return download_path

def _get_sys_url_part() -> str:
    sys = platform.system()
    sys_url_part: str
    if sys == 'Darwin':
        sys_url_part = 'darwin_amd64'
    elif sys == 'Linux':
        raise NotImplemented
    elif sys == 'Windows':
        raise NotImplemented
    else:
        raise UserWarning("Unknown system type: {}".format(sys))
    return sys_url_part

def latest_version_path() -> str:
    sys_url_part = _get_sys_url_part()
    # TODO: Don't hardcode minor version, can get this at '/1/latest-version'
    path = '{}/{}/1/1.0/latest-version'.format(DOWNLOAD_BASE_URL, sys_url_part)

    version: str
    with urllib.request.urlopen(path) as f:
        version = f.read().decode('utf-8')

    metadata_path = '{}/{}/1/1.0/{}/release-metadata.json'.format(DOWNLOAD_BASE_URL, sys_url_part, version)

    metadata: dict  # { "location":"...", "checksum":"...", ... }
    print('[INFO] Fetching metadata from {}'.format(metadata_path))
    with urllib.request.urlopen(metadata_path) as f:
        metadata = json.loads(f.read().decode('utf-8'))

    return metadata["location"]
