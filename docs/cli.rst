Command-line Interface
======================

Before using the CLI, you need to run `nexus3 login <#nexus3-login>`_ to enter
the Nexus endpoint and user credentials, which will be persisted in cleartext
dotfiles. Alternatively, you may use environment variables as below.


Environment Variables
---------------------

The configuration configuration can be set via environment variables, which take precedence over
configuration saved on file:

    - ``NEXUS3_PASSWORD`` (required)
    - ``NEXUS3_USERNAME`` (required)
    - ``NEXUS3_URL`` (required)
    - ``NEXUS3_API_VERSION`` (optional)
    - ``NEXUS3_X509_VERIFY`` (optional)

The client logging level can be configured by setting an environment variable named
``LOG_LEVEL``. Valid values are: ``DEBUG``, ``INFO``, ``WARNING`` (default),
``ERROR``, ``CRITICAL``.


Commands
--------

After installing the ``nexus3-cli`` Python package, the ``nexus3`` command  will be available to
your shell. It accepts several different commands.

.. click:: nexuscli.cli:nexus_cli
   :prog: nexus3
   :show-nested:
