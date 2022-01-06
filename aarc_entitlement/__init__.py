"""
Check entitlements according to the AARC recommendations G002 and G069.

The documentation is available at https://aarcentitlement.readthedocs.io.

The G002 is available at https://aarc-community.org/guidelines/aarc-g002.

This code is distributed under the MIT License.
"""

import re
from typing import Tuple, Union, Dict
from urllib.parse import unquote

import regex

_namespace_parts = (
    r":(?P<namespace_id>[^:]+)"  # Namespace-ID
    r":(?P<delegated_namespace>[^:?#]+)"  # Delegated URN namespace
    r"(:(?P<subnamespaces>[^:?#]+))*"  # Sub-namespaces
)
# ignore the optional r, q and f components of urns
_r_comp = r"(?:\?\+[^?#:]+)?"
_q_comp = r"(?:\?=[^#:]+)?"
_f_comp = r"(?:#[^:]+)?"
_ignored_optional_components = f"{_r_comp}{_q_comp}{_f_comp}"
_NAMESPACE_REGEX_STRICT = f"urn{_namespace_parts}"
_NAMESPACE_REGEX_LAX = f"[uU][rR][nN]{_namespace_parts}{_ignored_optional_components}"

_GROUP_SUBGROUPS_ROLE_REGEX = (
    r":group:"
    r"(?P<group>[^:#]+)"  # Root group
    r"(:(?P<subgroups>[^:#]+))*?"  # Sub-groups
    r"(:role=(?P<role>[^#]+))?"  # Role of the user in the deepest group
)

_AUTH_REGEX_STRICT = (
    r"#(?P<group_authority>.+)"  # Authoritative source of the entitlement
)
_AUTH_REGEX_LAX = f"({_AUTH_REGEX_STRICT})?"  # Optional Authority


class Error(Exception):
    """A generic error for this module"""


class ParseError(Error):
    """Error during parsing an entitlement"""


class KEY:
    NAMESPACE_ID = "namespace_id"
    DELEGATED_NAMESPACE = "delegated_namespace"
    SUBNAMESPACES = "subnamespaces"
    GROUP = "group"
    SUBGROUPS = "subgroups"
    ROLE = "role"
    GROUP_AUTHORITY = "group_authority"


KEYS_ALL = [
    KEY.NAMESPACE_ID,
    KEY.DELEGATED_NAMESPACE,
    KEY.SUBNAMESPACES,
    KEY.GROUP,
    KEY.SUBGROUPS,
    KEY.ROLE,
    KEY.GROUP_AUTHORITY,
]
""" All possible keys of entitlement parts """


KEYS_OPTIONAL = [
    KEY.SUBNAMESPACES,
    KEY.ROLE,
    KEY.SUBGROUPS,
    KEY.GROUP_AUTHORITY,
]
""" parts with these keys are optional """

KEYS_TUPLES = [KEY.SUBNAMESPACES, KEY.SUBGROUPS]
""" parts with these keys must be tuples or lists """


def _part_is_tuple(key):
    return key in KEYS_TUPLES


class ParseOptions:
    def __init__(self, need_group_authority: bool):
        self.need_group_authority = need_group_authority

    def __str__(self):
        return f"need_group_authority={self.need_group_authority}"

    def is_optional(self, key):
        if self.need_group_authority:
            return key == KEY.ROLE

        return key in [KEY.ROLE, KEY.GROUP_AUTHORITY]


LAX_PARSING = ParseOptions(need_group_authority=False)
STRICT_PARSING = ParseOptions(need_group_authority=True)


class Base:
    """
    `Base` is the parent class of the actual entitlements.
    Use :class:`G069` or :class:`G002` directly.

    """

    _parse_opts: ParseOptions
    _parts: Dict[str, Union[str, tuple]]

    def _preprocess(self, entitlement: str) -> str:
        return entitlement

    def _get_regex_str(self) -> str:  # pragma: no cover
        """must be overwritten in child subclasses"""
        print("Implement in subclass")
        return ""

    @staticmethod
    def _normalize_part(key, value: str) -> str:
        _ = key
        return value

    def _set_part(self, key, value):
        self._parts[key] = self._normalize_part(key, value)

    def _parse(self, raw: str):

        # These regexes are not compatible with stdlib 're', we need 'regex'!
        # (because of repeated captures, see https://bugs.python.org/issue7132)
        spec_regex = regex.compile(self._get_regex_str())
        match = spec_regex.fullmatch(raw)
        if match is None:
            raise ParseError(
                f"Entitlement does not conform to specification ({self._parse_opts}): {raw}"
            )

        capturesdict = match.capturesdict()
        for key in KEYS_ALL:
            value = capturesdict.get(key, None)
            if _part_is_tuple(key):
                self._set_part(key, tuple(value))
            elif isinstance(value, list):
                if len(value) == 1:
                    self._set_part(key, value[0])
                elif not self._parse_opts.is_optional(key):
                    # given the regex these cases can not happen
                    raise ParseError(
                        f"Error extracting attribute '{key}' got {value}"
                    )  # pragma: no cover
            else:
                raise ParseError(
                    f"Error extracting attribute '{key}' got {value}"
                )  # pragma: no cover

    def _init_from_parts(self, parts: Dict[str, Union[str, tuple, list]]):
        for key in KEYS_ALL:
            is_optional = self._parse_opts.is_optional(key)
            is_tuple = _part_is_tuple(key)

            val = parts.get(key, None)
            if val is None:
                if not is_optional and not is_tuple:
                    raise ParseError(f"Part with key '{key}' must not be None")
            else:
                if _part_is_tuple(key):
                    if isinstance(val, list):
                        val = tuple(val)
                    elif not isinstance(val, tuple):
                        raise ParseError(f"Part with key '{key}' must be tuple: {val}")

                self._set_part(key, val)

    def __init__(
        self,
        entitlement: Union[str, Dict[str, Union[str, tuple, list]]],
        parse_opts: ParseOptions = None,
    ):
        """
        Instances can be tested for equality and less-than-or-equality.
        :meth:`.satisfies` can be used to check if a user with an entitlement `user_has`
        is permitted to use a resource which requires a certain entitlement `service_wants` using: `user_has.satisfies(resource_wants)`

        :param Union[str,dict] entitlement: Usually a raw string representation of the entitlement.
            Alternatively a dict with the needed parts may be provided.
        :raises ParseError: If the raw entitlement is not following the respective AARC
            recommendation and cannnot be parsed.
        :raises Error:
            If the attributes extracted from the entitlement could not be assigned to this instance.

        """
        self._parts = {}
        self._parse_opts = parse_opts if parse_opts is not None else LAX_PARSING

        if isinstance(entitlement, str):
            self._parse(self._preprocess(entitlement))
        elif isinstance(entitlement, dict):
            self._init_from_parts(entitlement)
        else:
            raise ParseError(
                "Arg 'entitlement' must be an entitlement string or a dict containing entitlement parts"
            )

    def _part_repr(self, key):
        part = self.get_part(key)
        if _part_is_tuple(key) and isinstance(part, tuple):
            return "".join([f":{v}" for v in part])

        if key == KEY.ROLE:
            return f":role={part}" if part is not None else ""

        if key == KEY.GROUP_AUTHORITY:
            return f"#{part}" if part is not None else ""

        return part

    def __repr__(self):
        """Serialize the entitlement to its respective format.

        This is the inverse to `__init__` and thus `ent_str == repr(aarc_entitlement.Base(ent_str))`
        holds for any valid entitlement.
        """
        return (
            f"urn:{self._part_repr('namespace_id')}:{self._part_repr('delegated_namespace')}{self._part_repr('subnamespaces')}"
            f":group:{self._part_repr('group')}{self._part_repr('subgroups')}{self._part_repr('role')}{self._part_repr('group_authority')}"
        )

    def _part_str(self, key):
        value = self.get_part(key)
        if isinstance(value, tuple):
            return ",".join(value)

        return value

    def __str__(self):
        return "<{self.__name__} " + " ".join(
            f"{key}={self._part_str(key)}" for key in KEYS_ALL
        )

    def __hash__(self):
        return hash(
            tuple(self.get_part(key) for key in KEYS_ALL if key != KEY.GROUP_AUTHORITY)
        )

    def __le__(self, other):
        def compare(key, strict=False):
            self_val = self.get_part(key)
            other_val = other.get_part(key)

            if isinstance(self_val, tuple) and isinstance(other_val, tuple):
                self_len = len(self_val)
                other_len = len(other_val)
                t = (
                    self_len == other_len if strict else self_len <= other_len
                ) and all(tup[0] == tup[1] for tup in zip(self_val, other_val))
            else:
                t = self_val == other_val

            if key == KEY.ROLE:
                if self_val is not None:
                    t = t and compare(KEY.SUBGROUPS, strict=True)
                else:
                    t = True  # other may have a role, but this doesnt break the comparison

            return t

        return all(compare(key) for key in KEYS_ALL if key != KEY.GROUP_AUTHORITY)

    def satisfies(self, required):
        """
        Check if `self` satisfies the demands of `required`.
        `self` satisfies the requirement if it is equal to or more permissive than `required`.

        :param  required: An entitlement which is required e.g. for using a service.
        :return: True, if the requirement is satisfied. Otherwise, `False` is returned.
        """
        return required.is_contained_in(self)

    def is_contained_in(self, other):
        """
        `self` is contained in `other` if `other is equal or more permissive than `self`
        """
        return self <= other

    def __eq__(self, other):
        """Check if other object is equal."""
        is_equal = hash(self) == hash(other)
        return is_equal

    @property
    def parts(self) -> dict:
        """
        :return: A copy of the parts of the entitlement.
            This cannot be used to modify the entitlement.
            Use :meth:`set_part` instead.

        """
        return dict(self._parts)

    def get_part(self, key: str) -> Union[tuple, str, None]:
        """
        :return: Entitlement part indicated by `key`
        """
        if _part_is_tuple(key):
            return self._parts.get(key, ())

        if self._parse_opts.is_optional(key):
            return self._parts.get(key, None)

        return self._parts.get(key, "")

    def set_part(self, key: str, value: Union[tuple, list, str, None]):
        """
        `set_part` can be used to modify this entitlement.
        Values will be properly normalized.

        :param str key: Key of the entitlement part. Valid values can be found in `aarc_entitlement.ALL_KEYS`
        :param Union[tuple, list, str, None] value: The value to be set. If `None` and the part indicated by `key` is optional, then the part is deleted.
        """
        if key not in KEYS_ALL:
            raise Error(f"Not a valid key for entitlement part: {key}")

        if value is None:
            if _part_is_tuple(key) or self._parse_opts.is_optional(key):
                del self._parts[key]
            else:
                raise Error(f"Setting key '{key}' to None is not permitted")

        else:
            self._set_part(key, value)

    @property
    def namespace_id(self):
        return self.get_part(KEY.NAMESPACE_ID)

    @property
    def delegated_namespace(self):
        return self.get_part(KEY.DELEGATED_NAMESPACE)

    @property
    def subnamespaces(self):
        return self.get_part(KEY.SUBNAMESPACES)

    @property
    def group(self):
        return self.get_part(KEY.GROUP)

    @property
    def subgroups(self):
        return self.get_part(KEY.SUBGROUPS)

    @property
    def role(self):
        return self.get_part(KEY.ROLE)

    @property
    def group_authority(self):
        return self.get_part(KEY.GROUP_AUTHORITY)


class G002(Base):
    """Create, parse and compare AARC Entitlements G002

    Reference specification: https://aarc-community.org/guidelines/aarc-g002

    The entitlement is always '%xx' decoded before parsing.

    """

    def __init__(self, entitlement: Union[str, dict], strict=False):
        """
        In addition to the parameters from :class:`` the strict parametr is available:

        :param bool,optional strict: If set to true, only entitlements with a group_authority part are valid.
            If `raw` does not contain a group_authority part, a :class:`ParseError` will be raised.

        """
        parse_opts = LAX_PARSING if not strict else STRICT_PARSING
        super().__init__(entitlement, parse_opts)

    def _get_regex_str(self):
        if self._parse_opts.need_group_authority:
            return f"^{_NAMESPACE_REGEX_STRICT}{_GROUP_SUBGROUPS_ROLE_REGEX}{_AUTH_REGEX_STRICT}$"
        return (
            f"^{_NAMESPACE_REGEX_STRICT}{_GROUP_SUBGROUPS_ROLE_REGEX}{_AUTH_REGEX_LAX}$"
        )

    def _preprocess(self, entitlement: str) -> str:
        return unquote(entitlement)


class G069(Base):
    def __init__(self, entitlement: Union[str, dict]):
        """
        In contrast to :class:`G002` this entitlement spec allows '%xx' encoded parts.
        Hence, a string `entitlement` is not '%xx' decoded.

        :class:`G069` uses the same parameters as :class:`Base`.

        """
        super().__init__(entitlement)

    def _get_regex_str(self):
        # the AUTHORITY component is deprecated as of G069 -> the lax regex of G002 allowed this already
        return f"^{_NAMESPACE_REGEX_LAX}{_GROUP_SUBGROUPS_ROLE_REGEX}{_AUTH_REGEX_LAX}$"

    @staticmethod
    def _normalize_part(key, value: Union[str, Tuple]) -> Union[str, Tuple]:
        if key in [KEY.GROUP, KEY.SUBGROUPS, KEY.ROLE, KEY.GROUP_AUTHORITY]:
            # make percent encodings uppercase
            normalize = lambda v: re.sub(
                "%[0-9a-z]{2}", lambda m: m.group(0).upper(), v
            )
        else:
            # make namespace part lower case
            normalize = lambda v: v.lower()

        if isinstance(value, tuple):
            return tuple(normalize(field) for field in value)

        return normalize(value)


# vim: tw=100 foldmethod=indent
