import pytest
from nexuscli.api.repository.model import YumGroupRepository, YumHostedRepository, YumProxyRepository


def test_upload_error(upload_file_ensure_raises_api_error):
    """Ensure the method raises an exception when the API response is wrong"""
    upload_file_ensure_raises_api_error(YumHostedRepository)


@pytest.mark.parametrize('class_', [YumHostedRepository, YumProxyRepository])
def test_configuration(class_, faker):
    x_depth = faker.pyint()

    # This will break once YumHosted starts validating unknown kwargs (remote_url is Proxy only)
    repo = class_(name='dummy', depth=x_depth, remote_url='http://dummy')

    assert repo.configuration['attributes']['yum']['repodataDepth'] == x_depth


@pytest.mark.integration
@pytest.mark.incremental
class TestYumHostedRepository:
    def test_create(self, nexus_client, repository_factory):
        repository = repository_factory(YumHostedRepository)
        nexus_client.repositories.create(repository)

    def test_upload(self, repository_factory):
        repository = repository_factory(YumHostedRepository)
        repository.upload_file('tests/fixtures/yum/example-0-0-0.noarch.rpm', 'somedest')

    def test_download(self, repository_factory, nexus_client):
        repository = repository_factory(YumHostedRepository)
        repository.upload_file('tests/fixtures/yum/example-0-0-0.noarch.rpm', 'somedest2')
        repository.download('packages/example/0.0.0/example-0-0-0.noarch.rpm', '/dev/null')

    def test_delete(self, nexus_client, repository_factory):
        repository = repository_factory(YumHostedRepository)
        nexus_client.repositories.delete(repository.name)
