import click

#############################################################################
# repository create options
CLEANUP = [
    click.option('--cleanup-policy',
                 help='Name of existing clean-up policy to use'),
]

COMMON = [
    click.argument('name'),
    click.option('--blob-store-name', default='default',
                 help='Blobstore name to use with new repository'),
    click.option('--strict-content/--no-strict-content', default=False,
                 help='Toggle strict content type validation'),
]

GROUP = COMMON + [
    click.option('--member-names', '-m', multiple=True, help='Repository name(s) to add to group. '
                 'Use once per member. E.g.: `-m name-a '
                 '-m name-b`.')
]

HOSTED = COMMON + CLEANUP + [
    click.option('--write-policy', help='Write policy to use', default='allow',
                 type=click.Choice(['allow', 'allow_once', 'deny'], case_sensitive=False))
]

PROXY = COMMON + CLEANUP + [
    click.argument('remote-url'),
    click.option('--auto-block/--no-auto-block', default=True,
                 help='Disable outbound connections on remote-url access errors'),
    click.option('--negative-cache/--no-negative-cache', default=True,
                 help='Cache responses for content missing in the remote-url'),
    click.option('--negative-cache-ttl', type=click.INT, default=1440,
                 help='Cache time in minutes'),
    click.option('--content-max-age', type=click.INT, default=1440,
                 help='Maximum age of cached artefacts'),
    click.option('--metadata-max-age', type=click.INT, default=1440,
                 help='Maximum age of cached artefacts metadata'),
    click.option('--remote-auth-type', help='Only username is supported',
                 type=click.Choice(['username'], case_sensitive=False)),
    click.option('--health-check/--no-health-check', default=False,
                 help='Enable Repository Health Check'),
    # TODO: require `--remote-auth-type username` when these are specified
    click.option('--remote-username', help='Username for remote URL'),
    click.option('--remote-password', help='Password for remote URL'),
]


APT = [
    click.option('--distribution', required=True, help='Distribution to fetch; e.g.: bionic')
]

DOCKER = [
    click.option('--v1-enabled/--no-v1-enabled', default=False, help='Enable v1 registry'),
    click.option('--force-basic-auth/--no-force-basic-auth', default=False,
                 help='Force use of basic authentication'),
    click.option('--http-port', type=click.INT, help='Port for HTTP service'),
    click.option('--https-port', type=click.INT, help='Port for HTTPS service'),
]


MAVEN = [
    click.option('--version-policy', help='Version policy to use', default='release',
                 type=click.Choice(['release', 'snapshot', 'mixed'], case_sensitive=False)),
    click.option('--layout-policy', help='Layout policy to use', default='strict',
                 type=click.Choice(['strict', 'permissive'], case_sensitive=False)),
]
