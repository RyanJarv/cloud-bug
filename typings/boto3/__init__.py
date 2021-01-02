import importlib.util
import logging
import sys
from typing import Any, Optional, Union, overload

import boto3.session
from boto3.session import Session
from botocore.config import Config
from mypy_boto3_ec2.client import EC2Client
from mypy_boto3_ec2.service_resource import EC2ServiceResource
from mypy_boto3_ecs.client import ECSClient
from mypy_boto3_iam.client import IAMClient
from mypy_boto3_iam.service_resource import IAMServiceResource
from mypy_boto3_sts.client import STSClient

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal
__author__: str
__version__: str

DEFAULT_SESSION: Optional[Session] = None


def setup_default_session(
    aws_access_key_id: str = None,
    aws_secret_access_key: str = None,
    aws_session_token: str = None,
    region_name: str = None,
    botocore_session: str = None,
    profile_name: str = None,
) -> Session:
    ...


def set_stream_logger(
    name: str = "boto3", level: int = logging.DEBUG, format_string: Optional[str] = None
) -> None:
    ...


def _get_default_session() -> Session:
    ...


class NullHandler(logging.Handler):
    def emit(self, record: Any) -> Any:
        ...


@overload
def client(
    service_name: Literal["iam"],
    region_name: Optional[str] = None,
    api_version: Optional[str] = None,
    use_ssl: Optional[bool] = None,
    verify: Union[bool, str, None] = None,
    endpoint_url: Optional[str] = None,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_session_token: Optional[str] = None,
    config: Optional[Config] = None,
) -> IAMClient:
    ...


@overload
def client(
    service_name: Literal["ec2"],
    region_name: Optional[str] = None,
    api_version: Optional[str] = None,
    use_ssl: Optional[bool] = None,
    verify: Union[bool, str, None] = None,
    endpoint_url: Optional[str] = None,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_session_token: Optional[str] = None,
    config: Optional[Config] = None,
) -> EC2Client:
    ...


@overload
def client(
    service_name: Literal["ecs"],
    region_name: Optional[str] = None,
    api_version: Optional[str] = None,
    use_ssl: Optional[bool] = None,
    verify: Union[bool, str, None] = None,
    endpoint_url: Optional[str] = None,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_session_token: Optional[str] = None,
    config: Optional[Config] = None,
) -> ECSClient:
    ...


@overload
def client(
    service_name: Literal["sts"],
    region_name: Optional[str] = None,
    api_version: Optional[str] = None,
    use_ssl: Optional[bool] = None,
    verify: Union[bool, str, None] = None,
    endpoint_url: Optional[str] = None,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_session_token: Optional[str] = None,
    config: Optional[Config] = None,
) -> STSClient:
    ...


@overload
def resource(
    service_name: Literal["iam"],
    region_name: Optional[str] = None,
    api_version: Optional[str] = None,
    use_ssl: Optional[bool] = None,
    verify: Union[bool, str, None] = None,
    endpoint_url: Optional[str] = None,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_session_token: Optional[str] = None,
    config: Optional[Config] = None,
) -> IAMServiceResource:
    ...


@overload
def resource(
    service_name: Literal["ec2"],
    region_name: Optional[str] = None,
    api_version: Optional[str] = None,
    use_ssl: Optional[bool] = None,
    verify: Union[bool, str, None] = None,
    endpoint_url: Optional[str] = None,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_session_token: Optional[str] = None,
    config: Optional[Config] = None,
) -> EC2ServiceResource:
    ...
