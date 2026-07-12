import pytest

from adr_toolkit.selection import (
    UnknownPackError,
    order_packs,
    resolve_all,
    resolve_interactions,
    resolve_selection,
)
from conftest import make_manifest, make_pack


def test_unknown_selected_pack_raises_listing_the_unknown_ids() -> None:
    manifest = make_manifest({"universal": make_pack("universal")})

    with pytest.raises(UnknownPackError) as excinfo:
        resolve_selection(manifest, ["universal", "zebra", "apple"])

    assert excinfo.value.unknown == ["apple", "zebra"]  # sorted, only the unknowns
    assert "apple, zebra" in str(excinfo.value)


def test_selecting_a_pack_pulls_in_its_dependency() -> None:
    manifest = make_manifest(
        {
            "js-ts": make_pack("language"),
            "react": make_pack("ui-tech", depends_on=["js-ts"]),
        }
    )

    selected = resolve_selection(manifest, ["react"])

    assert set(selected) == {"react", "js-ts"}


def test_dependencies_are_resolved_transitively() -> None:
    manifest = make_manifest(
        {
            "jvm": make_pack("language"),
            "compose": make_pack("ui-tech", depends_on=["jvm"]),
            "native-ui": make_pack("app-shape", depends_on=["compose"]),
        }
    )

    selected = resolve_selection(manifest, ["native-ui"])

    assert set(selected) == {"native-ui", "compose", "jvm"}


def test_shared_dependency_is_included_once() -> None:
    manifest = make_manifest(
        {
            "jvm": make_pack("language"),
            "kotlin": make_pack("language", depends_on=["jvm"]),
            "spring-boot": make_pack("framework", depends_on=["jvm"]),
        }
    )

    selected = resolve_selection(manifest, ["kotlin", "spring-boot"])

    assert sorted(selected) == ["jvm", "kotlin", "spring-boot"]
    assert selected.count("jvm") == 1


def test_interaction_included_only_when_both_endpoint_packs_selected() -> None:
    manifest = make_manifest(
        packs={},
        interactions=[
            {"when": ["d3", "react"], "adr": "d3-react"},
            {"when": ["d3", "plain-js"], "adr": "d3-plain"},
        ],
    )

    interactions = resolve_interactions(manifest, {"d3", "react", "js-ts"})

    assert interactions == ["d3-react"]


def test_packs_ordered_by_axis() -> None:
    manifest = make_manifest(
        {
            "react": make_pack("ui-tech"),
            "tdd": make_pack("universal"),
            "kotlin": make_pack("language"),
            "spring-boot": make_pack("framework"),
        }
    )

    ordered = order_packs(manifest, ["react", "tdd", "spring-boot", "kotlin"])

    assert ordered == ["tdd", "kotlin", "spring-boot", "react"]


def test_order_places_dependencies_before_dependents_within_an_axis() -> None:
    manifest = make_manifest(
        {
            "jvm": make_pack("language"),
            "kotlin": make_pack("language", depends_on=["jvm"]),
        }
    )

    # Deterministic and dependency-respecting regardless of input order.
    assert order_packs(manifest, ["kotlin", "jvm"]) == ["jvm", "kotlin"]
    assert order_packs(manifest, ["jvm", "kotlin"]) == ["jvm", "kotlin"]


def test_resolve_all_expands_deps_adds_interactions_and_orders() -> None:
    manifest = make_manifest(
        {
            "js-ts": make_pack("language"),
            "react": make_pack("ui-tech", depends_on=["js-ts"]),
            "d3": make_pack("library"),
            "d3-react": make_pack("interaction"),
        },
        interactions=[{"when": ["d3", "react"], "adr": "d3-react"}],
    )

    assert resolve_all(manifest, ["react", "d3"]) == ["js-ts", "react", "d3", "d3-react"]
