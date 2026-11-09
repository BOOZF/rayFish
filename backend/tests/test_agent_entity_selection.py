import pytest

from app.services.oasis_profile_generator import OasisProfileGenerator
from app.services.zep_entity_reader import ZepEntityReader


@pytest.mark.parametrize("entity_type", ["Homeowner", "ApplianceShopper", "ContentCreator", "Person", "student"])
def test_custom_person_types_use_the_individual_persona(entity_type):
    generator = OasisProfileGenerator.__new__(OasisProfileGenerator)
    assert generator._is_individual_entity(entity_type)


@pytest.mark.parametrize("entity_type", ["LocalMerchant", "CommunityGroup", "Organization", "university"])
def test_group_types_use_the_group_persona(entity_type):
    generator = OasisProfileGenerator.__new__(OasisProfileGenerator)
    assert not generator._is_individual_entity(entity_type)


def test_excluded_names_do_not_become_agents():
    def node(name):
        return {"uuid": name, "name": name, "labels": ["Entity", "Person"], "summary": "", "attributes": {}}

    reader = ZepEntityReader.__new__(ZepEntityReader)
    reader.get_all_nodes = lambda graph_id: [node("Kevin Lim"), node("Google"), node(" shopee ")]

    result = reader.filter_defined_entities(
        "graph", enrich_with_edges=False, excluded_entity_names=["google", "Shopee"]
    )

    assert [entity.name for entity in result.entities] == ["Kevin Lim"]
    assert result.filtered_count == 1
    assert result.total_count == 3
