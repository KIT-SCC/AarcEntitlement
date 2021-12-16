# pylint: disable=too-many-arguments, invalid-name, missing-docstring, no-self-use

from enum import Enum

import pytest

from aarc_entitlement import (
    AarcEntitlementG002,
    AarcEntitlementG069,
    KEY,
    AarcEntitlementError,
)

# parsing strictness
STRICT = True
LAX = False

# Rel describes relationships between two entitlements
# Entitlement 'Actual' is a user provided entitlement which is checked against 'Required'
# Entitlement 'Required' is defined by a service provider
class Rel(Enum):
    EQUAL = 1
    ACTUAL_CONTAINS_REQUIRED = 2
    REQUIRED_CONTAINS_ACTUAL = 3  # this does not permit the user to use the service
    DISJOINT = 4  # this does not permit the user to use the service


@pytest.mark.parametrize("aarc_class", [AarcEntitlementG002, AarcEntitlementG069])
class TestAarcEntitlement:
    AUTHORITY_FOO = "unity.helmholtz-data-federation.de"
    AUTHORITY_BAR = "backupserver.used.for.developmt.de"

    @pytest.mark.parametrize(
        "name,strict,rel,required,actual",
        [
            (
                "entitlements_disjoint",
                LAX,
                Rel.DISJOINT,
                "urn:geant:h-df.de:group:aai-admin",
                "urn:geant:kit.edu:group:bwUniCluster",
            ),
            (
                "entitlements_disjoint2",
                LAX,
                Rel.DISJOINT,
                f"urn:geant:h-df.de:group:myExampleColab#{AUTHORITY_FOO}",
                "urn:geant:kit.edu:group:bwUniCluster",
            ),
            (
                "entitlements_disjoint3",
                LAX,
                Rel.DISJOINT,
                "urn:geant:h-df.de:group:aai-admin",
                "urn:geant:kit.edu:group:aai-admin",
            ),
            (
                "equal",
                LAX,
                Rel.EQUAL,
                f"urn:geant:h-df.de:group:aai-admin#{AUTHORITY_FOO}",
                f"urn:geant:h-df.de:group:aai-admin#{AUTHORITY_FOO}",
            ),
            (
                "equal_subgroup_role",
                LAX,
                Rel.EQUAL,
                f"urn:geant:h-df.de:group:aai-admin:subadmins#{AUTHORITY_FOO}",
                f"urn:geant:h-df.de:group:aai-admin:subadmins#{AUTHORITY_FOO}",
            ),
            (
                "equal_role",
                LAX,
                Rel.EQUAL,
                f"urn:geant:h-df.de:group:aai-admin:role=member#{AUTHORITY_FOO}",
                f"urn:geant:h-df.de:group:aai-admin:role=member#{AUTHORITY_FOO}",
            ),
            (
                "intentional_authority_mismatch",
                LAX,
                Rel.EQUAL,
                f"urn:geant:h-df.de:group:aai-admin:role=member#{AUTHORITY_FOO}",
                f"urn:geant:h-df.de:group:aai-admin:role=member#{AUTHORITY_BAR}",
            ),
            (
                "intentional_authority_mismatch_2",
                LAX,
                Rel.EQUAL,
                "urn:geant:h-df.de:group:aai-admin",
                "urn:geant:h-df.de:group:aai-admin#totally_different_authority",
            ),
            (
                "actual_has_optional_subgroup",
                LAX,
                Rel.ACTUAL_CONTAINS_REQUIRED,
                "urn:geant:h-df.de:group:aai-admin",
                f"urn:geant:h-df.de:group:aai-admin:special-admins#{AUTHORITY_FOO}",
            ),
            (
                "subnamespace_order",
                STRICT,
                Rel.DISJOINT,
                f"urn:geant:h-df.de:subns1:subns2:group:aai-admin:role=member#{AUTHORITY_FOO}",
                f"urn:geant:h-df.de:subns2:subns1:group:aai-admin:role=member#{AUTHORITY_FOO}",
            ),
            (
                "subnamespace_deeper",
                STRICT,
                Rel.REQUIRED_CONTAINS_ACTUAL,
                f"urn:geant:h-df.de:subns1:subns2:subns0:group:aai-admin:role=member#{AUTHORITY_FOO}",
                f"urn:geant:h-df.de:subns1:subns2:group:aai-admin:role=member#{AUTHORITY_FOO}",
            ),
            (
                "subgroup_order",
                STRICT,
                Rel.DISJOINT,
                f"urn:geant:h-df.de:group:aai-admin:subgroup1:subgroup2:subgroup3:role=member#{AUTHORITY_FOO}",
                f"urn:geant:h-df.de:group:aai-admin:subgroup2:subgroup1:subgroup3:role=member#{AUTHORITY_FOO}",
            ),
            (
                "subgroup_deeper",
                STRICT,
                Rel.DISJOINT,
                f"urn:geant:h-df.de:group:aai-admin:subgroup1:subgroup2:subgroup3:role=member#{AUTHORITY_FOO}",
                f"urn:geant:h-df.de:group:aai-admin:subgroup1:subgroup2:role=member#{AUTHORITY_FOO}",
            ),
            (
                "role_not_required",
                STRICT,
                Rel.ACTUAL_CONTAINS_REQUIRED,
                f"urn:geant:h-df.de:group:aai-admin#{AUTHORITY_FOO}",
                f"urn:geant:h-df.de:group:aai-admin:role=member#{AUTHORITY_BAR}",
            ),
            (
                "role_required",
                STRICT,
                Rel.REQUIRED_CONTAINS_ACTUAL,
                f"urn:geant:h-df.de:group:aai-admin:role=member#{AUTHORITY_FOO}",
                f"urn:geant:h-df.de:group:aai-admin#{AUTHORITY_BAR}",
            ),
            (
                "role_required_for_supergroup",
                STRICT,
                Rel.DISJOINT,
                f"urn:geant:h-df.de:group:aai-admin:role=admin#{AUTHORITY_FOO}",
                f"urn:geant:h-df.de:group:aai-admin:special-admins:role=admin#{AUTHORITY_BAR}",
            ),
            (
                "subgroup_required",
                STRICT,
                Rel.REQUIRED_CONTAINS_ACTUAL,
                f"urn:geant:h-df.de:group:aai-admin:special-admins#{AUTHORITY_FOO}",
                f"urn:geant:h-df.de:group:aai-admin#{AUTHORITY_BAR}",
            ),
        ],
    )
    def test_rel(self, aarc_class, name, strict, rel, required, actual):
        _ = name
        parser_args = {}
        if aarc_class != AarcEntitlementG069:
            parser_args["strict"] = strict

        ent_required = aarc_class(required, **parser_args)
        ent_actual = aarc_class(actual, **parser_args)

        if rel == Rel.EQUAL:
            assert ent_required == ent_actual
            assert ent_required.is_contained_in(ent_actual)
            assert ent_actual.is_contained_in(ent_required)
        elif rel == Rel.ACTUAL_CONTAINS_REQUIRED:
            assert ent_required != ent_actual
            assert ent_required.is_contained_in(ent_actual)
            assert not ent_actual.is_contained_in(ent_required)
        elif rel == Rel.REQUIRED_CONTAINS_ACTUAL:
            assert ent_required != ent_actual
            assert not ent_required.is_contained_in(ent_actual)
            assert ent_actual.is_contained_in(ent_required)
        elif rel == Rel.DISJOINT:
            assert ent_required != ent_actual
            assert not ent_required.is_contained_in(ent_actual)
            assert not ent_actual.is_contained_in(ent_required)

    @pytest.mark.parametrize(
        "required",
        [
            "urn:geant:h-df.de:group:aai-admin:role=admin",
            "urn:geant:h-df.de:group:aai-admin",
            "urn:geant:kit.edu:group:DFN-SLCS",
        ],
    )
    def test_failure_incomplete_but_valid_entitlement(self, aarc_class, required):
        if aarc_class != AarcEntitlementG069:
            aarc_class(required, strict=False)

    @pytest.mark.parametrize(
        "parts",
        [
            {
                KEY.NAMESPACE_ID: "geant",
                KEY.DELEGATED_NAMESPACE: "example.org",
                KEY.GROUP: "foo",
            },
            {
                KEY.NAMESPACE_ID: "geant",
                KEY.DELEGATED_NAMESPACE: "example.org",
                KEY.SUBNAMESPACES: ["abc", "def", "ghi"],
                KEY.GROUP: "foo",
            },
            {
                KEY.NAMESPACE_ID: "geant",
                KEY.DELEGATED_NAMESPACE: "example.org",
                KEY.GROUP: "foo",
                KEY.SUBGROUPS: ["bar"],
            },
            {
                KEY.NAMESPACE_ID: "geant",
                KEY.DELEGATED_NAMESPACE: "example.org",
                KEY.GROUP: "foo",
                KEY.ROLE: "admin",
            },
            {
                KEY.NAMESPACE_ID: "geant",
                KEY.DELEGATED_NAMESPACE: "example.org",
                KEY.GROUP: "foo",
                KEY.ROLE: "admin",
            },
        ],
    )
    def test_init_using_parts(self, aarc_class, parts):
        parser_args = {}
        if aarc_class == AarcEntitlementG002:
            parser_args["strict"] = bool(parts.get(KEY.GROUP_AUTHORITY, None))

        aarc_class(parts, **parser_args)

    def test_set_part(self, aarc_class):
        parser_args = {}
        if aarc_class == AarcEntitlementG002:
            parser_args["strict"] = False

        required = aarc_class(
            {
                KEY.NAMESPACE_ID: "geant",
                KEY.DELEGATED_NAMESPACE: "example.org",
                KEY.GROUP: "foo",
                KEY.ROLE: "admin",
            },
            **parser_args,
        )

        actual = aarc_class(
            {
                KEY.NAMESPACE_ID: "geant",
                KEY.DELEGATED_NAMESPACE: "example.org",
                KEY.GROUP: "foo",
            },
            **parser_args,
        )

        assert not required.is_contained_in(actual)
        actual.set_part(KEY.ROLE, "admin")
        assert required.is_contained_in(actual)

        # test deleting optional part
        actual.set_part(KEY.ROLE, None)
        assert not required.is_contained_in(actual)


class TestAarcEntitlementG002:
    def test_strict_parsing(self):
        parts_missing_auth = {
            KEY.NAMESPACE_ID: "geant",
            KEY.DELEGATED_NAMESPACE: "example.org",
            KEY.GROUP: "foo",
        }
        with pytest.raises(AarcEntitlementError):
            AarcEntitlementG002(parts_missing_auth, strict=True)


class TestAarcEntitlementG069:
    aarc_class = AarcEntitlementG069

    @pytest.mark.parametrize(
        "percent_encoded_group",
        [
            "colon%3A",  # ':'
            "equals%3D",  # '='
            "space%0A",  # ' '
            "hash%23",  # '#'
            "questionmark%3F",  # '?'
        ],
    )
    def test_valid_percent_encodings(self, percent_encoded_group):
        must_parse = f"urn:geant:h-df.de:group:{percent_encoded_group}"
        self.aarc_class(must_parse)

    @pytest.mark.parametrize(
        "unnormalized",
        [
            "URN:NID:EXAMPLE.ORG:group:Minun%20Ryhm%C3%A4ni",
            "UrN:NiD:ExAmPlE.oRg:group:Minun%20Ryhm%c3%a4ni",
            "URN:nid:example.org:group:Minun%20Ryhm%C3%A4ni",
            "urn:nid:example.org:group:Minun%20Ryhm%c3%a4ni",
            "urn:nid:example.org:group:Minun%20Ryhm%c3%A4ni",
        ],
    )
    def test_normalization(self, unnormalized):
        normalized = "urn:nid:example.org:group:Minun%20Ryhm%C3%A4ni"
        normalized_ent = self.aarc_class(normalized)
        unnormalized_ent = self.aarc_class(unnormalized)
        assert normalized == repr(unnormalized_ent)
        assert normalized_ent == unnormalized_ent

    @pytest.mark.parametrize(
        "with_optional_comp",
        [
            "urn:nid:example.org?+foo:group:g",
            "urn:nid:example.org?+foo#baz:group:g",
            "urn:nid:example.org?+foo?=bar:group:g",
            "urn:nid:example.org?+foo?=bar#baz:group:g",
            "urn:nid:example.org?=bar:group:g",
            "urn:nid:example.org?=bar#baz:group:g",
        ],
    )
    def test_optional_urn_components(self, with_optional_comp):
        without_comp = self.aarc_class("urn:nid:example.org:group:g")
        with_comp = self.aarc_class(with_optional_comp)
        assert without_comp == with_comp

    def test_set_part_normalization(self):

        entitlement = self.aarc_class(
            {
                KEY.NAMESPACE_ID: "geant",
                KEY.DELEGATED_NAMESPACE: "example.org",
                KEY.GROUP: "foo",
            },
        )

        # set not normalized
        entitlement.set_part(KEY.ROLE, "super%3aadmin")
        assert entitlement.get_part(KEY.ROLE) == "super%3Aadmin"

        # set not normalized
        entitlement.set_part(KEY.SUBNAMESPACES, tuple("FOO"))
        assert entitlement.get_part(KEY.SUBNAMESPACES) == tuple("foo")
