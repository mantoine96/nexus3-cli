import json
import logging
import os
import pathlib
import warnings
from typing import Dict, Iterator, Optional

import semver
from click import progressbar

from nexuscli.api.repository.base_models import base_repository, util
from nexuscli import exception, nexus_util

# https://issues.sonatype.org/browse/NEXUS-19525
# https://github.com/thiagofigueiro/nexus3-cli/issues/77
CLEANUP_SET_MIN_VERSION = semver.VersionInfo(3, 19, 0)


LOG = logging.getLogger(__name__)


class Repository(base_repository.BaseRepository):
    """
    Representation of the simplest Nexus repositories.

    Nexus 3 repository recipes (formats) supported by this class:

        - `bower
          <https://help.sonatype.com/repomanager3/formats/bower-repositories>`_
        - `npm
          <https://help.sonatype.com/repomanager3/formats/npm-registry>`_
        - `nuget
          <https://help.sonatype.com/repomanager3/formats/nuget-repositories>`_
        - `pypi
          <https://help.sonatype.com/repomanager3/formats/pypi-repositories>`_
        - `raw
          <https://help.sonatype.com/repomanager3/formats/raw-repositories>`_
        - `rubygems
          <https://help.sonatype.com/repomanager3/formats/rubygems-repositories>`_
        - `docker
          <https://help.sonatype.com/repomanager3/formats/docker-registry>`_
        - `apt
          <https://help.sonatype.com/repomanager3/formats/apt-repositories>`_

    :param name: name of the repository.
    :param nexus_client: the :class:`~nexuscli.nexus_client.NexusClient`
        instance that will be used to perform operations against the Nexus 3
        service. You must provide this at instantiation or set it before
        calling any methods that require connectivity to Nexus.
    :param recipe: format (recipe) of the new repository. Must be one of
        :py:attr:`RECIPES`. See Nexus documentation for details.
    :param blob_store_name: name of an existing blob store; 'default'
        should work on most installations.
    :param strict_content_type_validation: Whether to validate file
        extension against its content type.
    :param cleanup_policy: name of an existing repository clean-up policy.
    """
    TYPE = None

    def __init__(self, *args, **kwargs):
        self._cleanup_policy: Optional[str] = kwargs.get('cleanup_policy')

        super().__init__(*args, **kwargs)

    @property
    def _nexus_recipe_name(self):
        """
        The Nexus 3 name for this repository's recipe (format). Used with the Groovy API.
        """
        return f'{self.recipe_name}-{self.TYPE}'

    def _cleanup_uses_set(self):
        # In case Sonatype changes the version string format, default to the
        # new behaviour as there should be more people using newer versions
        if self._client is None or self._client.server_version is None:
            return True

        # When the breaking API change was introduced
        if self._client.server_version >= CLEANUP_SET_MIN_VERSION:
            return True

        return False

    @property
    def cleanup_policy(self):
        """
        Groovy-formatted value for the cleanup/policy attribute.
        """
        if self._cleanup_uses_set():
            if isinstance(self._cleanup_policy, list):
                return self._cleanup_policy  # when loaded from nexus, it already comes as a list
            return [self._cleanup_policy]
        else:
            return self._cleanup_policy

    @property
    def configuration(self) -> Dict:
        """
        Repository configuration represented as a python dict. The dict
        returned by this property can be converted to JSON for use with the
        ``nexus3-cli-repository-create``
        groovy script created by the
        :py:meth:`~nexuscli.api.repository.collection.RepositoryCollection.create`
        method.

        Example structure and attributes common to all repositories:

        >>> common_configuration = {
        >>>     'name': 'my-repository',
        >>>     'online': True,
        >>>     'recipeName': 'raw',
        >>>     '_state': 'present',
        >>>     'attributes': {
        >>>         'storage': {
        >>>             'blobStoreName': 'default',
        >>>         },
        >>>         'cleanup': {
        >>>             'policyName': None,
        >>>         }
        >>>     }
        >>> }

        Depending on the repository type and format (recipe), other attributes
        will be present.

        :return: repository configuration
        :rtype: dict
        """
        repo_config = {
            'name': self.name,
            'online': True,
            'recipeName': self._nexus_recipe_name,
            '_state': 'present',
            'attributes': {
                'storage': {
                    'blobStoreName': self.blob_store_name,
                    'strictContentTypeValidation': self.strict_content,
                },
            }
        }

        # we want 'x' or ['x'] but not None or [None]
        if self.cleanup_policy and any(self.cleanup_policy):
            repo_config['attributes']['cleanup'] = {
                'policyName': self.cleanup_policy}

        return repo_config

    def list(self, repository_path: str) -> Iterator[Optional[str]]:
        """
        List all the artefacts, recursively, in a given ``repository_path``.

        :param repository_path: location on the repository service.
        :return: artefacts under ``repository_path``.
        """
        for artefact in self.list_raw(repository_path):
            yield artefact.get('path')

    def list_raw(self, repository_path: str) -> Iterator[Dict]:
        """
        As per :meth:`list` but yields raw Nexus artefacts as dicts.

        :param repository_path: location on the repository service.
        """
        # FIXME: path handling :(
        repository_path = f'{self.name}{nexus_util.REMOTE_PATH_SEPARATOR}{repository_path}'
        repo, directory, filename = nexus_util.split_component_path(repository_path)
        path_filter = ''  # matches everything

        if directory is not None:
            path_filter = directory
            # Not all repos require a directory as part of the artefact path.
            if not (path_filter == '' or
                    path_filter.endswith(nexus_util.REMOTE_PATH_SEPARATOR)):
                path_filter += nexus_util.REMOTE_PATH_SEPARATOR

        if filename is not None:
            # The artefact path is always relative to the given repo.
            path_filter += filename

        list_gen = self._list_raw_search(path_filter)

        for artefact in list_gen:
            yield artefact

    def _list_raw_search(self, path_filter: str) -> Iterator[Dict]:
        # TODO: use `group` attribute in raw repositories to speed-up queries
        query = {
            'repository': self.name,
        }

        if path_filter:
            query['keyword'] = f'"{path_filter}"'  # hacky as fuck :(

        return self._get_paginated('search/assets', params=query)

    def _get_paginated(self, endpoint: str, **request_kwargs) -> Iterator[Dict]:
        """
        Performs a GET request using the given args and kwargs. If the response
        is paginated, the method will repeat the request, manipulating the
        `params` keyword argument each time in order to receive all pages of
        the response.

        Items in the responses are sent in "batches": when all elements of a
        response have been yielded, a new request is made and the process
        repeated.

        :param request_kwargs: passed verbatim to the _request() method, except
            for the argument needed to paginate requests.
        :return: a generator that yields on response item at a time.
        """
        response = self._client.request('get', endpoint, **request_kwargs)
        if response.status_code == 404:
            raise exception.NexusClientAPIError(response.reason)

        try:
            content = response.json()
        except json.decoder.JSONDecodeError:
            raise exception.NexusClientAPIError(response.content)

        while True:
            for item in content.get('items'):
                yield item

            continuation_token = content.get('continuationToken')
            if continuation_token is None:
                break

            request_kwargs['params'].update(
                {'continuationToken': continuation_token})
            response = self._client.request('get', endpoint, **request_kwargs)

            try:
                content = response.json()
            except json.decoder.JSONDecodeError:
                raise exception.NexusClientAPIError(response.content)

    def delete(self, repository_path):
        """
        Delete artefacts, recursively if ``repository_path`` is a directory.

        :param repository_path: location on the repository service.
        :type repository_path: str
        :return: number of deleted files. Negative number for errors.
        :rtype: int
        """

        delete_count = 0
        death_row = self.list_raw(repository_path)

        with progressbar([a for a in death_row], label='Deleting') as death_row:
            for artefact in death_row:
                id_ = artefact['id']
                artefact_path = artefact['path']

                response = self._client.delete(f'assets/{id_}')
                LOG.info('Deleted: %s (%s)', artefact_path, id_)
                delete_count += 1
                if response.status_code == 404:
                    LOG.warning('File disappeared while deleting')
                    LOG.debug(response.reason)
                elif response.status_code != 204:
                    LOG.error(response.reason)
                    return -1

        return delete_count

    @staticmethod
    def _should_skip_download(download_url, download_path, artefact, nocache):
        """False when nocache is set or local file is out-of-date"""
        if nocache:
            try:
                LOG.debug('Removing %s because nocache is set', download_path)
                os.remove(download_path)
            except FileNotFoundError:
                pass
            return False

        if nexus_util.has_same_hash(artefact, download_path):
            LOG.debug(
                'Skipping %s because local copy %s is up-to-date', download_url, download_path)
            return True

        return False

    def download_file(self, download_url, destination):
        """Download an asset from Nexus artefact repository to local
        file system.

        :param download_url: fully-qualified URL to asset being downloaded.
        :type download_url: str
        :param destination: file or directory location to save downloaded
            asset. Must be an existing directory; any exiting file in this
            location will be overwritten.
        :type destination: str
        :return:
        """
        response = self._client.get(download_url)

        if response.status_code != 200:
            raise exception.DownloadError(
                f'Downloading from {download_url}. Reason: {response.reason}')

        with open(destination, 'wb') as fd:
            LOG.debug('Writing %s to %s', download_url, destination)
            for chunk in response.iter_content(chunk_size=8192):
                fd.write(chunk)

    def download(self, source, destination, flatten=False, nocache=False):
        """Download artefacts. The source must be a valid Nexus 3
        repository path, including the repository name as the first component
        of the path.

        The destination must be a local file name or directory.

        If a file name is given as destination, the asset may be renamed. The
        final destination will depend on ``flatten``.

        :param source: location of artefact or directory on the repository
            service.
        :type source: str
        :param destination: path to the local file or directory.
        :type destination: str
        :param flatten: if True, the remote path isn't reproduced locally.
        :type flatten: bool
        :param nocache: if True, force download of a directory or artefact,
                        ignoring an existing local copy. If false, it will not
                        re-download an existing copy if its checksum matches
                        the one in Nexus (as determined by
                        :meth:`nexuscli.nexus_util.has_same_hash`).
        :type nocache: bool
        :return: number of downloaded files.
        :rtype: int
        """
        download_count = 0
        if source.endswith(nexus_util.REMOTE_PATH_SEPARATOR) and \
                not (destination.endswith('.') or destination.endswith('..')):
            destination += os.sep

        artefacts = self.list_raw(source)

        with progressbar([a for a in artefacts], label='Downloading') as artefacts:
            for artefact in artefacts:
                download_url = artefact['downloadUrl']
                artefact_path = artefact['path']
                LOG.debug('Downloading [%s] to [%s] from [%s], flatten=%s',
                          artefact_path, destination, download_url, flatten)
                download_path = nexus_util.remote_path_to_local(
                    artefact_path, destination, flatten
                )

                if self._should_skip_download(
                        download_url, download_path, artefact, nocache):
                    download_count += 1
                    continue

                try:
                    self.download_file(download_url, download_path)
                    download_count += 1
                except exception.DownloadError:
                    LOG.warning('Error downloading %s', download_url)
                    continue

        return download_count

    def upload(self, source, destination, recurse=True, flatten=False):
        """
        Upload artefacts. The source must be either a local file name or
        directory. The flatten and recurse options are honoured for
        directory uploads.

        The destination must be a valid Nexus 3 repository path, including the
        repository name as the first component of the path.

        :param source: location of file or directory to be uploaded.
        :type source: str
        :param destination: destination path in Nexus, including repository
            name and, if required, directory name (e.g. raw repos require a
            directory).
        :type destination: str
        :param recurse: do not process sub directories for uploads to remote
        :type recurse: bool
        :param flatten: Flatten directory structure by not reproducing local
                        directory structure remotely
        :type flatten: bool
        :return: number of files uploaded.
        """
        if os.path.isdir(source):
            return self.upload_directory(source, destination, recurse=recurse, flatten=flatten)

        self.upload_file(source, destination)
        return 1

    def upload_file(self, source, destination):
        raise NotImplementedError

    @staticmethod
    def _upload_dst_path(
            source: pathlib.Path,
            source_file: pathlib.Path,
            destination: pathlib.Path,
            flatten: bool):
        if flatten:
            return destination.joinpath(source_file.name)
        else:
            return destination.joinpath(source_file.relative_to(source))

    def upload_directory(self, source, destination, recurse=True, flatten=False):
        """
        Uploads all files in a directory to the specified destination directory
        in this repository, honouring options flatten and recurse.

        :param source: path to local directory to be uploaded
        :param destination: destination directory
        :param recurse: when True, upload directory recursively.
        :type recurse: bool
        :param flatten: when True, the source directory tree isn't replicated
            on the destination.
        :return: number of files uploaded
        :rtype: int
        """
        destination = pathlib.Path(destination)
        file_set = util.get_files(source, recurse)
        expected_upload_count = len(file_set)
        upload_count = 0
        with progressbar(file_set, length=expected_upload_count) as file_set:
            for source_file in file_set:
                dst_path = self._upload_dst_path(source, source_file, destination, flatten)
                LOG.debug('Uploading [%s] to [%s] in repository=%s, flatten=%s',
                          source_file, dst_path, self.name, flatten)
                self.upload_file(source_file, dst_path)
                upload_count += 1

        if expected_upload_count != upload_count:
            warnings.warn(f'expected {expected_upload_count} to upload but got {upload_count}')

        return upload_count
