from xardin.tools.manage import add_location, update_location, add_plant, add_planting
from xardin.resources import get_context, get_schema, get_plants, get_locations


def test_context_resource(db):
    result = get_context()
    assert "Growing zone" in result


def test_schema_resource(db):
    result = get_schema()
    assert "CREATE TABLE" in result
    assert "plants" in result
    assert "plantings" in result
    assert "locations" in result


def test_plants_resource_empty(db):
    result = get_plants()
    assert "No active plants" in result


def test_plants_resource(db):
    add_plant("basil", variety="Thai")
    add_planting("basil", location="porch")
    add_plant("tomatoes")
    add_planting("tomatoes", location="raised bed")
    result = get_plants()
    assert "basil (Thai)" in result
    assert "porch" in result
    assert "tomatoes" in result


def test_plants_resource_with_quantity(db):
    add_plant("peppers")
    add_planting("peppers", location="side yard", quantity=6)
    add_planting("peppers", location="back yard", quantity=3)
    result = get_plants()
    assert "side yard" in result
    assert "6 plants" in result
    assert "back yard" in result
    assert "3 plants" in result


def test_plants_resource_hides_inactive_plantings(db):
    add_plant("basil")
    add_planting("basil", location="porch")
    update_location("porch", active=False)
    # plant type still exists but no active plantings shown
    add_planting("basil")  # no location
    result = get_plants()
    assert "basil" in result


def test_locations_resource_empty(db):
    result = get_locations()
    assert "No locations" in result


def test_locations_resource(db):
    add_plant("basil")
    add_planting("basil", location="porch")
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


def test_locations_resource_shows_quantity(db):
    add_plant("peppers")
    add_planting("peppers", location="side yard", quantity=6)
    result = get_locations()
    assert "peppers" in result
    assert "6 plants" in result
