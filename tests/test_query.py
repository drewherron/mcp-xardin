from xardin.tools.manage import add_plant, add_location
from xardin.tools.query import execute_query


def test_select_query(db):
    add_plant("tomatoes", location="raised bed")
    add_plant("basil", location="porch")
    result = execute_query("SELECT name, active FROM plants")
    assert "tomatoes" in result
    assert "basil" in result


def test_rejects_insert(db):
    result = execute_query("INSERT INTO plants (name, active) VALUES ('x', 1)")
    assert "only SELECT" in result


def test_rejects_drop(db):
    result = execute_query("DROP TABLE plants")
    assert "only SELECT" in result


def test_rejects_delete(db):
    result = execute_query("DELETE FROM plants")
    assert "only SELECT" in result


def test_rejects_update(db):
    result = execute_query("UPDATE plants SET active = 0")
    assert "only SELECT" in result


def test_bad_sql(db):
    result = execute_query("SELECT * FROM nonexistent_table")
    assert "Query error" in result


def test_empty_result(db):
    result = execute_query("SELECT * FROM plants")
    assert "No results" in result


def test_join_query(db):
    add_plant("tomatoes", location="raised bed")
    result = execute_query(
        """SELECT p.name, l.name as location
           FROM plants p
           LEFT JOIN locations l ON p.location_id = l.id"""
    )
    assert "tomatoes" in result
    assert "raised bed" in result
