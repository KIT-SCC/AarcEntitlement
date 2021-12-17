AARC Entitlement Library
========================

This package provides python classes to create, parse and compare entitlements according
to the AARC recommendations G002 and G069.

Installation
------------
Install using pip::

    pip install aarc-entitlement

Documentation
-------------
The documentation is available at https://aarcentitlement.readthedocs.io.

The G002 recommendation can be found at https://aarc-community.org/guidelines/aarc-g002.

Examples
---------

Check if a user entitlement permits usage of a service
______________________________________________________
.. code-block:: python

    import aarc_entitlement

    # This entitlement is needed to use a service
    required = aarc_entitlement.G002("urn:geant:h-df.de:group:aai-admin")

    # This entitlement is held by a user who wants to use the service
    actual =   aarc_entitlement.G002("urn:geant:h-df.de:group:aai-admin:role=member")

    # Is the user permitted to use the service, because of its entitlement `actual`?
    permitted = actual.satisfies(required)
    # -> True here

    # Are the two entitlements the same?
    equals = required == actual
    # -> False here

..
    does not work on github:
    Other examples for entitlements and comparisions can be found in :download:`examples.py <../../examples.py>`

G069 Entitlement Normalization
______________________________
Starting with recommendation G069 the specification requires normalization of entitlements.
When using `AarcEntitlementG069` the library produces normalized representations.

.. code-block:: python

    import aarc_entitlement

    not_normalized = "UrN:NiD:ExAmPlE.oRg:group:Minun%20Ryhm%c3%a4ni"

    normalized = repr(aarc_entitlement.G069(not_normalized))
    # -> "urn:nid:example.org:group:Minun%20Ryhm%C3%A4ni"

Tests, Linting and Documentation
--------------------------------
Run tests for all supported python versions::

    # run tests, coverage and linter
    tox

    # build docs
    tox -e docs

    # After this, the documentation should be located at `doc/build/index.html`.


Funding Notice
--------------
The AARC project has received funding from the European Union’s Horizon
2020 research and innovation programme under grant agreement No 653965 and
730941.
