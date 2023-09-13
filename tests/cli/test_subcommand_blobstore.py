import json
import pytest

from nexuscli import exception
from nexuscli.cli import nexus_cli


@pytest.mark.integration
def test_list(cli_runner):
    """Test that the command has valid json output"""
    cmd = 'blobstore list --json'
    result = cli_runner.invoke(nexus_cli, cmd)
    content = json.loads(result.output)

    assert result.exit_code == exception.CliReturnCode.SUCCESS.value
    assert isinstance(content, list)
    assert len(content) > 0


@pytest.mark.integration
@pytest.mark.incremental
class TestBlobstore:
    name = __name__
    path = f'/tmp/{name}'

    def test_create(self, cli_runner):
        cmd = f'blobstore create file {self.name} {self.path}'
        result = cli_runner.invoke(nexus_cli, cmd)

        assert result.exit_code == exception.CliReturnCode.SUCCESS.value

    def test_show(self, cli_runner):
        """Test that the command has valid json output"""
        cmd = f'blobstore show {self.name}'
        result = cli_runner.invoke(nexus_cli, cmd)
        content = json.loads(result.output)

        assert result.exit_code == exception.CliReturnCode.SUCCESS.value
        assert content['type'] == 'File'
        assert content['path'] == self.path
        assert content['name'] == self.name

    def test_delete(self, cli_runner):
        """Test that the command has valid json output"""
        cmd = f'blobstore delete --yes {self.name}'
        result = cli_runner.invoke(nexus_cli, cmd)
        error_result = cli_runner.invoke(nexus_cli, cmd)

        assert result.exit_code == exception.CliReturnCode.SUCCESS.value
        assert "Unable to find blobstore" in error_result.output
