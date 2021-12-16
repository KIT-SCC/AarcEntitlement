#!/usr/bin/env python
from aarc_entitlement import AarcEntitlementG002


def example(i, required, actual, desc, entitlement_cls=AarcEntitlementG002):
    required_ent = entitlement_cls(required)
    actual_ent = entitlement_cls(actual)
    print(f"\n{i}: {desc}")
    print(f"\tActual:    {required}")
    print(f"\tRequired:  {actual}")
    print(f"\tSatisfied: {actual_ent.satisfies(required_ent)}")
    print(f"\tEqual:     {required_ent== actual_ent}")


def main():
    examples = enumerate(
        [
            (
                "urn:geant:h-df.de:group:aai-admin:role=member#unity.helmholtz-data-federation.de",
                "urn:geant:h-df.de:group:aai-admin:role=member#unity.helmholtz-data-federation.de",
                "Simple case: Everything the same",
            ),
            (
                "urn:geant:h-df.de:group:aai-admin:role=member#unity.helmholtz-data-federation.de",
                "urn:geant:h-df.de:group:aai-admin:role=member#backupserver.used.for.developmt.de",
                "Simple case: Different authorities, everything else same",
            ),
            (
                "urn:geant:h-df.de:group:aai-admin#unity.helmholtz-data-federation.de",
                "urn:geant:h-df.de:group:aai-admin:role=member#backupserver.used.for.developmt.de",
                "Role assigned but not required",
            ),
            (
                "urn:geant:h-df.de:group:aai-admin:role=member#unity.helmholtz-data-federation.de",
                "urn:geant:h-df.de:group:aai-admin#backupserver.used.for.developmt.de",
                "Role required but not assigned",
            ),
            (
                "urn:geant:h-df.de:group:aai-admin:special-admins#unity.helmholtz-data-federation.de",
                "urn:geant:h-df.de:group:aai-admin#backupserver.used.for.developmt.de",
                "Subgroup required, but not available",
            ),
            (
                "urn:geant:h-df.de:group:aai-admin#unity.helmholtz-data-federation.de",
                "urn:geant:h-df.de:group:aai-admin:testgroup:special-admins#backupserver.used.for.developmt.de",
                "Edge case: User in subgroup, but only supergroup required",
            ),
            (
                "urn:geant:h-df.de:group:aai-admin:role=admin#unity.helmholtz-data-federation.de",
                "urn:geant:h-df.de:group:aai-admin:special-admins:role=admin#backupserver.used.for.developmt.de",
                "Role required for supergroup but only assigned for subgroup",
            ),
        ]
    )

    for (i, (required_group, actual_group, desc)) in examples:
        example(i, required_group, actual_group, desc)


if __name__ == "__main__":
    main()
