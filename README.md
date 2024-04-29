# nexus3-cli

A python-based command-line interface and API client for Sonatype's [Nexus
OSS 3](https://www.sonatype.com/download-oss-sonatype).

## Features

1. Compatible with [Nexus 3 OSS](https://www.sonatype.com/download-oss-sonatype). It may work with the commercial release, but it's untested.
   1. [Nexus versions tested](https://gitlab.com/thiagocsf/nexus3-cli/-/blob/master/.gitlab-ci.yml#L103-116)
1. Python API and command-line support.
1. Artefact management: list, delete, bulk upload and download.
1. Repository management:
   1. Create hosted and proxy.
   1. Create apt, bower, docker, maven, npm, nuget, pypi, raw, rubygems, yum.
   1. Content type validation, version and write policy.
   1. Delete.
1. Groovy script management: list, upload, delete, run.
1. Clean-up policy management: create, list.
1. Task management: list, run, show stop.
1. Security management: realms.
1. Blob store management: list, show, create, delete, update (API only).

The actions above are performed using the Nexus REST API if the endpoint is
available, otherwise a Groovy script is used.

Please note that some Nexus 3 features are not currently supported. Assistance
implementing missing support is very welcome. Please have a look at the
[issues](https://gitlab.com/thiagocsf/nexus3-cli/-/issues)
and [contribution guidelines](https://gitlab.com/thiagocsf/nexus3-cli/-/blob/master/CONTRIBUTING.md).

## Installation

The `nexus3-cli` package is available on PyPi. You can install using `pip` / `pip3`:

```bash
pip install nexus3-cli
```

There's also a [Docker image with `nexus3-cli` 
pre-installed](https://gitlab.com/thiagocsf/docker-nexus3-cli).

### Enable Groovy scripts

Some of the functionality in this client was written before the Nexus REST API 
exposed the necessary endpoints. For this reason, you may need to enable Groovy
script execution in your instance.

See the [FAQ in this blog post](https://support.sonatype.com/hc/en-us/articles/360045220393-Scripting-Nexus-Repository-Manager-3)
and the [example `nexus.properties`](https://gitlab.com/thiagocsf/nexus3-cli/-/blob/master/tests/fixtures/nexus-data/etc/nexus.properties) in this project.

If you decide to leave Groovy scripts disabled in your Nexus 3 instance, you need to disable its
use in this client. This can be done by editing the `~/.nexus-cli` configuration and changing
`groovy_enabled` to `false`. Alternatively, you can export the `NEXUS3_GROOVY_ENABLED=false`
environment variable.

## Usage

### Command line

For a quick start, use the [sonatype/nexus3 Docker image](https://hub.docker.com/r/sonatype/nexus3/):

```bash
docker run -d --rm -p 127.0.0.1:8081:8081 --name nexus sonatype/nexus3
```

This container will take a while to start the first time you run it. You can
tell when it's available by looking at the Docker instance logs or browsing to
[http://localhost:8081](http://localhost:8081).

On older versions of the `nexus3` Docker image, the default `admin` password is
`admin123`; on newer versions it's automatically generated and you can find it
by running `docker exec nexus cat /nexus-data/admin.password`.

The `login` command will store the service URL and your credentials in
`~/.nexus-cli` (warning: restrictive file permissions are set but the contents
are saved in cleartext).

Set up credentials:

```bash
$ nexus3 login
Nexus OSS URL (http://localhost:8081):
Nexus admin username (admin):
Nexus admin password (admin123):
Verify server certificate (True):

Configuration saved to /Users/thiago/.nexus-cli
```

Alternatively, you can define environment variables ``NEXUS3_PASSWORD``, ``NEXUS3_USERNAME``, ``NEXUS3_URL``, ``NEXUS3_API_VERSION``, and ``NEXUS3_X509_VERIFY``.



List repositories:

```bash
$ nexus3 repository list
Name              Format   Type     URL
maven-snapshots   maven2   hosted   http://localhost:8081/repository/maven-snapshots
maven-central     maven2   proxy    http://localhost:8081/repository/maven-central
nuget-group       nuget    group    http://localhost:8081/repository/nuget-group
nuget.org-proxy   nuget    proxy    http://localhost:8081/repository/nuget.org-proxy
maven-releases    maven2   hosted   http://localhost:8081/repository/maven-releases
nuget-hosted      nuget    hosted   http://localhost:8081/repository/nuget-hosted
maven-public      maven2   group    http://localhost:8081/repository/maven-public
```

Create a repository:

```bash
nexus3 repository create hosted raw reponame
```

Do a recursive directory upload:

```bash
$ mkdir -p /tmp/some/deep/test/path
$ touch /tmp/some/deep/test/file.txt /tmp/some/deep/test/path/other.txt
$ cd /tmp; nexus3 up some/ reponame/path/
Uploading some/ to reponame/path/
[################################] 2/2 - 00:00:00
Uploaded 2 files to reponame/path/
```

Nota Bene: `nexus3-cli` interprets a path ending in `/` as a directory.

List repository contents:

```bash
$ nexus3 ls reponame/path/
path/some/deep/test/path/other.txt
path/some/deep/test/file.txt
```

For a usage message for commands, subcommands and options, run `nexus3 -h`.
[CLI documentation](https://nexus3-cli.readthedocs.io/en/latest/cli.html)

### API

See [API documentation](https://nexus3-cli.readthedocs.io/en/latest/api.html).

## Development

The automated tests are configured in `.gitlab-ci.yml`. To run tests locally,
install the package with test dependencies and run pytest:

```bash
pip install [--user] -e .[test]
pip install [--user] pytest faker
pytest -m 'not integration'
```

Integration tests require a local Nexus instance listening on 8081/tcp or as
configured in `~/.nexus-cli`. The configuration file can be created using
[nexus3 login](https://nexus3-cli.readthedocs.io/en/latest/cli.html#nexus3-login).

```bash
docker run -v $(pwd)/tests/fixtures/nexus-data/etc:/nexus-data/etc -d --rm -p 127.0.0.1:8081:8081 --name nexus sonatype/nexus3
./tests/wait-for-nexus.sh  # the Nexus instance takes a while to be ready
# use the random admin password generated by the Nexus container to login
nexus3 login -U "http://localhost:8081" -u admin -p $(docker exec nexus cat /nexus-data/admin.password) --no-x509_verify
pytest -m integration
docker kill nexus
```

Nota Bene: if you re-run integration tests without re-creating or cleaning-up the
dev Nexus instance, test will fail because some objects created during tests will
already exist.

Pull requests are welcome; please see [CONTRIBUTING.md](CONTRIBUTING.md).
