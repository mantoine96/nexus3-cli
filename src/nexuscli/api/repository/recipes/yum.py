from typing import Optional

from nexuscli import exception, nexus_util
from nexuscli.api.repository.base_models import Repository
from nexuscli.api.repository.base_models import HostedRepository
from nexuscli.api.repository.base_models import ProxyRepository
from nexuscli.api.repository.base_models import GroupRepository

__all__ = ['YumGroupRepository', 'YumHostedRepository', 'YumProxyRepository']


class _YumRepository(Repository):
    """
    A `Yum <https://help.sonatype.com/repomanager3/formats/yum-repositories>`_
    base Nexus repository.

    :param name: name of the repository.
    :type name: str
    :param depth: The Yum ``repodata`` depth. Usually 1.
    :type depth: int
    :param kwargs: see :class:`Repository`
    """
    RECIPE_NAME = 'yum'

    def __init__(self, *args, **kwargs):
        self.depth: int = kwargs.get('depth', 1)

        super().__init__(*args, **kwargs)

    @property
    def configuration(self):
        """
        As per :py:obj:`Repository.configuration` but specific to this
        repository recipe and type.

        :rtype: str
        """
        repo_config = super().configuration
        repo_config['attributes']['yum'] = {
            'repodataDepth': self.depth
        }
        return repo_config


class YumHostedRepository(HostedRepository, _YumRepository):
    """
    A `Yum <https://help.sonatype.com/repomanager3/formats/yum-repositories>`_
    hosted Nexus repository.

    See :class:`HostedRepository` and :class:`YumRepository`
    """
    def upload_file(self, source, destination):
        dst_path, dst_file = nexus_util.get_dst_path_and_file(source, destination)

        repository_path = nexus_util.REMOTE_PATH_SEPARATOR.join(
            ['repository', self.name, dst_path, dst_file])

        with open(source, 'rb') as fh:
            response = self._client.put(
                repository_path, data=fh, stream=True, service_url=self._client.config.url)

        if response.status_code != 200:
            raise exception.NexusClientAPIError(
                f'Uploading to {repository_path}. Reason: {response.reason} '
                f'Status code: {response.status_code} Text: {response.text}')


class YumProxyRepository(ProxyRepository, _YumRepository):
    """
    A `Yum <https://help.sonatype.com/repomanager3/formats/yum-repositories>`_
    proxy Nexus repository.

    See :class:`ProxyRepository` and :class:`YumRepository`
    """
    pass


class YumGroupRepository(GroupRepository, _YumRepository):
    def __init__(self, *args, **kwargs):
        self.gpg_keypair: Optional[str] = kwargs.get('gpg_keypair')
        self.passphrase: Optional[str] = kwargs.get('passphrase')
        super().__init__(*args, **kwargs)

    @property
    def configuration(self):
        """
        As per :py:obj:`Repository.configuration` but specific to this
        repository recipe and type.

        :rtype: str
        """
        repo_config = super().configuration
        repo_config['attributes'].update({
            'yumSigning': {
                'keypair': self.gpg_keypair,
                'passphrase': self.passphrase
            }
        })
        return repo_config
