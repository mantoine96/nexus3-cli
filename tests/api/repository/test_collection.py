import itertools
import pytest
from pprint import pformat

from nexuscli import exception
from nexuscli.api import repository


def test_create_type_error(repository_collection, faker):
    """Ensure the method raises TypeError when not given a Repository"""
    with pytest.raises(TypeError):
        repository_collection.create(faker.pyiterable())


def test_create_repository_error(repository_collection, mocker):
    """Ensure the incorrect response from Nexus results in the expected exception."""
    mocker.patch('json.dumps')
    dummy_repo = repository.model.RawHostedRepository(name='dummy')
    repository_collection.run_script = mocker.Mock(return_value={})

    with pytest.raises(exception.NexusClientCreateRepositoryError):
        repository_collection.create(dummy_repo)


def test_repository_init(nexus_mock_client, mocker):
    """Ensure the property call triggers an installation of groovy script dependencies"""
    nexus_mock_client._scripts = mocker.PropertyMock()
    nexus_mock_client._repositories = None  # force a reload on instantiation
    x_calls = [
        mocker.call('nexus3-cli-repository-delete'),
        mocker.call('nexus3-cli-repository-get'),
        mocker.call('nexus3-cli-repository-create')]

    nexus_mock_client.repositories  # force class instantiation

    nexus_mock_client.scripts.create_if_missing.assert_has_calls(x_calls, any_order=True)


@pytest.mark.parametrize('repo_class, response', itertools.product(
    repository.collection.get_repository_classes(),
    [{}, {'result': 'something'}, {'result': 'null'}]))
def test_create_repository(
        repo_class, response, nexus_mock_client, faker, mocker):
    """Ensure the method behaves as expected for all Repository classes"""
    if repo_class.TYPE == 'group' and repo_class.RECIPE_NAME in ['docker', 'maven', 'yum']:
        pytest.skip('Not Implemented')

    x_configuration = faker.pydict()
    run_script = mocker.patch.object(
        nexus_mock_client.repositories, 'run_script', return_value=response)

    json_dumps = mocker.patch('json.dumps', return_value=x_configuration)

    mocker.patch.object(
        repo_class, 'configuration',
        new_callable=mocker.PropertyMock, return_value=x_configuration)

    kwargs = {}
    if repo_class.TYPE == 'proxy':
        kwargs['remote_url'] = faker.url()

    repo = repo_class(None, name=faker.word(), **kwargs)

    if response.get('result') == 'null':
        nexus_mock_client.repositories.create(repo)
    else:
        with pytest.raises(exception.NexusClientCreateRepositoryError):
            nexus_mock_client.repositories.create(repo)

    json_dumps.assert_called_with(repo.configuration)
    run_script.assert_called_with('nexus3-cli-repository-create', data=json_dumps.return_value)


def test_delete(nexus_mock_client, faker, mocker):
    """
    Ensure the delete method verifies the groovy script is in place and runs it
    with the configuration for the repository to be created as argument. Also
    test that the result is correctly interpreted for success/failure.
    """
    nexus_mock_client._scripts = mocker.PropertyMock()
    x_name = faker.word()

    nexus_mock_client.repositories.delete(x_name)

    nexus_mock_client.repositories.run_script.assert_called_with(
        'nexus3-cli-repository-delete', data=x_name)


# TODO: test all repos, not just the built-in maven ones
@pytest.mark.parametrize('x_configuration', pytest.helpers.default_repos())
@pytest.mark.integration
def test_get_raw_by_name(x_configuration, nexus_client):
    """Ensure the method finds and returns a repo configuration by name"""
    name = x_configuration['repositoryName']
    configuration = nexus_client.repositories.get_raw_by_name(name)

    added, removed, modified, _ = pytest.helpers.compare_dict(
        configuration, x_configuration)

    if added or removed or modified:
        print(
            f'configuration: {pformat(configuration)}\n'
            f'added: {pformat(added)}\n'
            f'removed: {pformat(removed)}\n'
            f'modified: {pformat(modified)}\n')
        pytest.fail('Configuration mismatch')


@pytest.mark.integration
def test_get_raw_by_name_error(nexus_client, faker):
    """Ensure the method raises an exception when a repo is not found"""
    with pytest.raises(exception.NexusClientInvalidRepository):
        nexus_client.repositories.get_raw_by_name(faker.pystr())


@pytest.mark.integration
def test_raw_list(nexus_client):
    """Ensure the method returns a raw list of repositories"""
    repositories = nexus_client.repositories.raw_list()

    assert isinstance(repositories, list)
    assert all(r.get('name') for r in repositories)
    assert all(r.get('format') for r in repositories)
    assert all(r.get('type') for r in repositories)
    assert all(r.get('url') for r in repositories)
