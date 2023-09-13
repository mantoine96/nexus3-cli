import json
from click import ClickException
from enum import Enum


class CliReturnCode(Enum):
    """Error codes returned by :py:mod:`nexuscli.cli`"""
    SUCCESS = 0
    NO_FILES = 1
    API_ERROR = 2
    CONNECTION_ERROR = 3
    DOWNLOAD_ERROR = 4
    INVALID_CREDENTIALS = 5
    CAPABILITY_NOT_AVAILABLE = 6
    NOT_IMPLEMENTED = 7
    INVALID_SUBCOMMAND = 10
    SUBCOMMAND_ERROR = 11
    NOT_FOUND = 12
    TASK_DISABLED = 13
    POLICY_NOT_FOUND = 20
    REPOSITORY_NOT_FOUND = 30
    CONFIG_ERROR = 40
    UNKNOWN_ERROR = 99


API_ERROR_MAP = {
    'Creating and updating scripts is disabled': {
        'class': 'ConfigError',
        'msg': (
            'Please enable scripting in your Nexus instance; see https://support.sonatype.com/hc'
            '/en-us/articles/360045220393-Scripting-Nexus-Repository-Manager-3#how-to-enable')
    },
    '"EULA is not accepted"': {
        'class': 'ConfigError',
        'msg': (
            'Please accept the Health Check EULA using your Nexus instance UI; once this is done '
            'for at least one repository, the API call will work for other repositories')
    },
}
"""Map from Nexus API response to an exception class and user-friendly error"""


def _lookup_and_raise(nexus_message):
    if nexus_message in API_ERROR_MAP.keys():
        friendly_message = API_ERROR_MAP[nexus_message]['msg']
        exception_class = API_ERROR_MAP[nexus_message]['class']
        raise globals()[exception_class](friendly_message) from None


def _raise_if_error_is_mapped(nexus_message_bytes):
    # error could be a plain string
    if isinstance(nexus_message_bytes, str):
        _lookup_and_raise(nexus_message_bytes)

    # or it could be a byte-encoded string
    if isinstance(nexus_message_bytes, bytes):
        try:
            result = nexus_message_bytes.decode('utf-8')
            _lookup_and_raise(result)
        except UnicodeDecodeError:
            pass

    # maybe it's a JSON object
    try:
        nexus_response = json.loads(nexus_message_bytes)
    except (TypeError, json.JSONDecodeError):
        return

    if not isinstance(nexus_response, dict):
        return

    try:
        result = nexus_response['message']
    except KeyError:
        raise TypeError(f'Unrecognised Nexus error response: {nexus_response}') from None

    _lookup_and_raise(result)


class NexusClientBaseError(ClickException):
    exit_code = CliReturnCode.UNKNOWN_ERROR.value


class NexusClientAPIError(NexusClientBaseError):
    """Unexpected response from Nexus service."""
    exit_code = CliReturnCode.API_ERROR.value

    def __init__(self, message_bytes=None):
        super().__init__(message_bytes)
        _raise_if_error_is_mapped(message_bytes)


class NexusClientConnectionError(NexusClientBaseError):
    """Generic network connector error."""
    exit_code = CliReturnCode.CONNECTION_ERROR.value


class NexusClientInvalidCredentials(NexusClientBaseError):
    """
    Login credentials not accepted by Nexus service. Usually the result of a
    HTTP 401 response.
    """
    exit_code = CliReturnCode.INVALID_CREDENTIALS.value


class NexusClientInvalidRepositoryPath(NexusClientBaseError):
    """
    Used when an operation against the Nexus service uses an invalid or
    non-existent path.
    """
    pass


class NexusClientInvalidRepository(NexusClientBaseError):
    """The given repository does not exist in Nexus."""
    exit_code = CliReturnCode.REPOSITORY_NOT_FOUND.value


class NexusClientInvalidCleanupPolicy(NexusClientBaseError):
    """The given cleanup policy does not exist in Nexus."""
    exit_code = CliReturnCode.SUBCOMMAND_ERROR.value


class NexusClientCreateRepositoryError(NexusClientBaseError):
    """Used when a repository creation operation in Nexus fails."""
    exit_code = CliReturnCode.SUBCOMMAND_ERROR.value


class NexusClientCreateCleanupPolicyError(NexusClientBaseError):
    """Used when a cleanup policy creation operation in Nexus fails."""
    exit_code = CliReturnCode.SUBCOMMAND_ERROR.value


class NexusClientCapabilityUnsupported(NexusClientBaseError):
    """Client tried to use a capability that doesn't exist in this Nexus 3 server version"""
    exit_code = CliReturnCode.CAPABILITY_NOT_AVAILABLE.value


class DownloadError(NexusClientBaseError):
    """Error retrieving artefact from Nexus service."""
    exit_code = CliReturnCode.DOWNLOAD_ERROR.value


class ConfigError(NexusClientBaseError):
    """Configuration error."""
    exit_code = CliReturnCode.CONFIG_ERROR.value


class NotFound(NexusClientBaseError):
    """The requested object/item was not found on the server"""
    exit_code = CliReturnCode.NOT_FOUND.value

    def __init__(self, message):
        super().__init__(f'{message} was not found on the server')


class TaskDisabled(NexusClientBaseError):
    """The requested task is disabled"""
    exit_code = CliReturnCode.TASK_DISABLED.value

    def __init__(self, message):
        super().__init__(f'{message} is disabled')


class FeatureNotImplemented(NexusClientBaseError):
    """The requested feature hasn't been implemented in this client"""
    exit_code = CliReturnCode.NOT_IMPLEMENTED.value

    def __init__(self, message=None):
        message = message or 'this feature is not yet implemented on nexus3-cli'
        super().__init__(message)
