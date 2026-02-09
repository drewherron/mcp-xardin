from xardin.tools.manage import add_location, add_plant
from xardin.resources import get_schema, get_plants, get_locations


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
