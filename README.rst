AARC Entitlements G002 / G069
======================

This package provides a python class to parse and compare entitlements according
to the AARC-G002 Recommendation https://aarc-community.org/guidelines/aarc-g002.


Example: Check if a user entitlement fits requirements
-------

.. code-block:: python

     from aarc_entitlement import AarcEntitlement

     required = AarcEntitlementG002(
         'urn:geant:h-df.de:group:aai-admin',
         strict=False,
     )
     actual = AarcEntitlement(
         'urn:geant:h-df.de:group:aai-admin:role=member#backupserver.used.for.developmt.de',
     )

     # is a user with actual permitted to use a resource which needs required?
     permitted = required.is_contained_in(actual) # True in this case

     # are the two entitlements the same?
     equals = required == actual # False in this case

API
---
.. automodule:: aarc_entitlement
   :members:
