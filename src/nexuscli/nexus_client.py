import logging

from typing import List, Optional

from nexuscli.nexus_config import NexusConfig
from nexuscli.nexus_http import NexusHttp
from nexuscli.api.blobstore import BlobstoreCollection
from nexuscli.api.cleanup_policy import CleanupPolicyCollection
from nexuscli.api.repository import RepositoryCollection
from nexuscli.api.security.realms import RealmCollection
from nexuscli.api.script import ScriptCollection
from nexuscli.api.task import TaskCollection

LOG = logging.getLogger(__name__)


class NexusClient:
    """
    A class to interact with Nexus 3's API.

    Unless all keyword arguments ``url``, ``user`` and ``password`` are
    supplied, the class will attempt to read the configuration file and,
    if unsuccessful, use defaults.

    Args:
        config: instance containing the configuration for the
            Nexus service used by this instance.
    """
    def __init__(self, config: NexusConfig = None):
        self.http: NexusHttp = NexusHttp(config)
        # Collections
        self._blobstores: Optional[BlobstoreCollection] = None
        self._cleanup_policies: Optional[RealmCollection] = None
        self._repositories: Optional[RepositoryCollection] = None
        self._scripts: Optional[ScriptCollection] = None
        self._security_realms: Optional[RealmCollection] = None
        self._tasks: Optional[TaskCollection] = None

    def create_scripts(self, scripts: List[str]) -> None:
        if self.http.config.groovy_enabled:
            for script_name in scripts:
                self.scripts.create_if_missing(script_name)

    @property
    def blobstores(self) -> BlobstoreCollection:
        """Instance of :class:`~nexuscli.api.repository.collection.BlobstoreCollection`"""
        if self._blobstores is None:
            self._blobstores = BlobstoreCollection(nexus_http=self.http)
            self.create_scripts(self._blobstores.script_dependencies())
        return self._blobstores

    @property
    def repositories(self) -> RepositoryCollection:
        """
        Instance of
        :class:`~nexuscli.api.repository.collection.RepositoryCollection`. This
        will automatically use the existing instance of :class:`NexusClient` to
        communicate with the Nexus service.
        """
        if self._repositories is None:
            self._repositories = RepositoryCollection(nexus_http=self.http)
            self.create_scripts(self._repositories.script_dependencies())
        return self._repositories

    @property
    def security_realms(self) -> RealmCollection:
        """
        This instance uses the existing instance of :class:`NexusClient` to communicate with the
        Nexus service.
        """
        if self._security_realms is None:
            self._security_realms = RealmCollection(nexus_http=self.http)
        return self._security_realms

    @property
    def tasks(self) -> TaskCollection:
        """
        Instance of
        :class:`~nexuscli.api.task.collection.RepositoryCollection`. This
        will automatically use the existing instance of :class:`NexusClient` to
        communicate with the Nexus service.
        """
        if self._tasks is None:
            self._tasks = TaskCollection(nexus_http=self.http)
        return self._tasks

    @property
    def cleanup_policies(self) -> CleanupPolicyCollection:
        """
        Instance of
        :class:`~nexuscli.api.cleanup_policy.collection.CleanupPolicyCollection`
        . This will automatically use the existing instance of
        :class:`NexusClient` to communicate with the Nexus service.
        """
        if self._cleanup_policies is None:
            self._cleanup_policies = CleanupPolicyCollection(nexus_http=self.http)
            self.create_scripts(self._cleanup_policies.script_dependencies())
        return self._cleanup_policies

    @property
    def scripts(self) -> ScriptCollection:
        """
        Instance of
        :class:`~nexuscli.api.script.model.ScriptCollection`. This will
        automatically use the existing instance of :class:`NexusClient` to
        communicate with the Nexus service.
        """
        if self._scripts is None:
            self._scripts = ScriptCollection(nexus_http=self.http)
            self.create_scripts(self._scripts.script_dependencies())
        return self._scripts
