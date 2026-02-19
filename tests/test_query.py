from xardin.tools.manage import add_plant, add_planting, add_location
from xardin.tools.query import execute_query


def test_select_query(db):
    add_plant("tomatoes")
    add_plant("basil")
    result = execute_query("SELECT name FROM plants")
    assert "tomatoes" in result
    assert "basil" in result


def test_rejects_insert(db):
    result = execute_query("INSERT INTO plants (name) VALUES ('x')")
    assert "only SELECT" in result


def test_rejects_drop(db):
    result = execute_query("DROP TABLE plants")
    assert "only SELECT" in result


def test_rejects_delete(db):
    result = execute_query("DELETE FROM plants")
    assert "only SELECT" in result


def test_rejects_update(db):
    result = execute_query("UPDATE plants SET notes = 'x'")
    assert "only SELECT" in result


def test_bad_sql(db):
    result = execute_query("SELECT * FROM nonexistent_table")
    assert "Query error" in result


def test_empty_result(db):
    result = execute_query("SELECT * FROM plants")
    assert "No results" in result


def test_join_query(db):
    add_plant("tomatoes")
    add_planting("tomatoes", location="raised bed")
    result = execute_query(
        """SELECT p.name, l.name as location
           FROM plants p
           JOIN plantings pt ON pt.plant_id = p.id
           LEFT JOIN locations l ON pt.location_id = l.id"""
    )
    assert "tomatoes" in result
    assert "raised bed" in result
