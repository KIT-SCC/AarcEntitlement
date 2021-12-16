AARC Entitlement Library
========================

This package provides python classes to create, parse and compare entitlements according
to the AARC recommendations G002 <https://aarc-community.org/guidelines/aarc-g002> and G069 <TODO LINK>.

Installation
------------
Install using pip::

    pip install aarc-entitlement


Examples:
--------

Check if a user entitlement permits usage of a service
______________________________________________________
.. code-block:: python

    from aarc_entitlement import AarcEntitlementG002

    # This entitlement is needed to use a service
    required = AarcEntitlementG002('urn:geant:h-df.de:group:aai-admin')

    # This entitlement is held by a user who wants to use the service
    actual =   AarcEntitlementG002('urn:geant:h-df.de:group:aai-admin:role=member')

    # Is the user permitted to use the service, because of its entitlement `actual`?
    permitted = actual.satisfies(required)
    # -> True here

    # Are the two entitlements the same?
    equals = required == actual
    # -> False here

Other examples for entitlements and comparisions can be found in :download:`examples.py <../../examples.py>`

G069 Entitlement Normalization
_____________________
Starting with recommendation G069 the specification requires normalization of entitlements.
When using `AarcEntitlementG069` the library produces normalized representations.

.. code-block:: python

    from aarc_entitlement import AarcEntitlementG069

    not_normalized = "UrN:NiD:ExAmPlE.oRg:group:Minun%20Ryhm%c3%a4ni"

    normalized = repr(AarcEntitlementG069(not_normalized))
    # -> "urn:nid:example.org:group:Minun%20Ryhm%C3%A4ni"
