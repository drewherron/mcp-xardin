from xardin.tools.manage import add_location, update_location, add_plant
from xardin.resources import get_context, get_schema, get_plants, get_locations


def test_context_resource(db):
    result = get_context()
    assert "Growing zone" in result


def test_schema_resource(db):
    result = get_schema()
    assert "CREATE TABLE" in result
    assert "plants" in result
    assert "locations" in result


def test_plants_resource_empty(db):
    result = get_plants()
    assert "No active plants" in result


def test_plants_resource(db):
    add_plant("basil", location="porch", variety="Thai")
    add_plant("tomatoes", location="raised bed")
    result = get_plants()
    assert "basil (Thai)" in result
    assert "porch" in result
    assert "tomatoes" in result


def test_locations_resource_empty(db):
    result = get_locations()
    assert "No locations" in result


def test_locations_resource(db):
    add_plant("basil", location="porch")
    add_location("empty spot")
    result = get_locations()
    assert "porch" in result
    assert "basil" in result
    assert "empty spot" in result
    assert "(empty)" in result


def test_locations_resource_hides_inactive(db):
    add_location("old bed")
    update_location("old bed", active=False)
    add_location("current bed")
    result = get_locations()
    assert "old bed" not in result
    assert "current bed" in result


def test_locations_resource_with_attributes(db):
    add_location("raised bed A")
    add_location("raised bed B")
    update_location("raised bed A", sun_exposure="full sun", size="4x8 ft",
                    notes="South-facing", adjacent_to=["raised bed B"])
    result = get_locations()
    assert "full sun" in result
    assert "4x8 ft" in result
    assert "South-facing" in result
    assert "Adjacent to: raised bed B" in result
