from xardin.tools.manage import add_plant, add_location
from xardin.tools.log_activity import log_activity, log_activities
from xardin.resources import get_recent_activity


def test_log_basic_activity(db):
    result = log_activity("planted", "Planted tomatoes in raised bed")
    assert "Logged planted" in result

    row = db.execute("SELECT * FROM activities").fetchone()
    assert row["activity_type"] == "planted"


def test_log_activity_with_plant(db):
    add_plant("tomatoes")
    result = log_activity("harvested", "Picked some tomatoes", plant="tomatoes")
    assert "tomatoes" in result

    row = db.execute("SELECT * FROM activities").fetchone()
    assert row["plant_id"] is not None


def test_log_observation(db):
    add_plant("basil")
    log_activity(
        "observed", "Looking wilted",
        plant="basil", possible_cause="overwatering",
    )

    row = db.execute("SELECT * FROM observations").fetchone()
    assert row["observation"] == "Looking wilted"
    assert row["possible_cause"] == "overwatering"


def test_log_activity_unknown_plant(db):
    # should still log, just without a plant_id
    result = log_activity("planted", "Planted something new", plant="mystery plant")
    assert "Logged" in result

    row = db.execute("SELECT * FROM activities").fetchone()
    assert row["plant_id"] is None


def test_log_activities_batch(db):
    add_plant("tomatoes")
    entries = [
        {"activity_type": "planted", "description": "Planted tomatoes", "plant": "tomatoes"},
        {"activity_type": "observed", "description": "Aphids spotted", "plant": "tomatoes"},
    ]
    result = log_activities(entries)
    assert "Logged 2 entries" in result

    assert db.execute("SELECT count(*) FROM activities").fetchone()[0] == 1
    assert db.execute("SELECT count(*) FROM observations").fetchone()[0] == 1


def test_recent_activity_resource(db):
    add_plant("basil", location="porch")
    log_activity("planted", "Planted basil", plant="basil", location="porch")
    log_activity("observed", "Basil wilting", plant="basil")

    result = get_recent_activity()
    assert "planted" in result
    assert "observed" in result
    assert "basil" in result


def test_recent_activity_empty(db):
    result = get_recent_activity()
    assert "No recent activity" in result
