from xardin.tools.manage import (
    add_location,
    update_location,
    add_plant,
    update_plant,
    get_plant_info,
)
from xardin.tools.log_activity import log_activity


def test_add_location(db):
    result = add_location("raised bed")
    assert "raised bed" in result
    assert "id=1" in result

    row = db.execute("SELECT * FROM locations WHERE id = 1").fetchone()
    assert row["name"] == "raised bed"


def test_add_location_with_description(db):
    result = add_location("porch", description="south-facing, covered")
    assert "porch" in result

    row = db.execute("SELECT * FROM locations WHERE id = 1").fetchone()
    assert row["description"] == "south-facing, covered"


def test_add_location_creates_new_after_inactive(db):
    add_location("pot 5")
    update_location("pot 5", active=False)
    result = add_location("pot 5")
    assert "Added" in result

    rows = db.execute("SELECT * FROM locations WHERE name = 'pot 5'").fetchall()
    assert len(rows) == 2
    active = [r for r in rows if r["active"] == 1]
    assert len(active) == 1


def test_add_location_already_exists(db):
    add_location("raised bed")
    result = add_location("raised bed")
    assert "already exists" in result


def test_update_location_attributes(db):
    add_location("raised bed A")
    result = update_location("raised bed A", sun_exposure="full sun", size="4x8 ft")
    assert "Updated" in result

    row = db.execute("SELECT * FROM locations WHERE name = 'raised bed A'").fetchone()
    assert row["sun_exposure"] == "full sun"
    assert row["size"] == "4x8 ft"


def test_update_location_notes(db):
    add_location("raised bed C")
    result = update_location("raised bed C", notes="Against north fence, short end faces bed B")
    assert "Updated" in result

    row = db.execute("SELECT * FROM locations WHERE name = 'raised bed C'").fetchone()
    assert "north fence" in row["notes"]


def test_update_location_adjacency(db):
    add_location("raised bed A")
    add_location("raised bed B")
    result = update_location("raised bed A", adjacent_to=["raised bed B"])
    assert "adjacent_to" in result

    a = db.execute("SELECT id FROM locations WHERE name = 'raised bed A'").fetchone()
    b = db.execute("SELECT id FROM locations WHERE name = 'raised bed B'").fetchone()

    link = db.execute(
        "SELECT * FROM location_adjacency WHERE location_id = ? AND adjacent_id = ?",
        (a["id"], b["id"]),
    ).fetchone()
    assert link is not None

    # link is symmetric
    reverse = db.execute(
        "SELECT * FROM location_adjacency WHERE location_id = ? AND adjacent_id = ?",
        (b["id"], a["id"]),
    ).fetchone()
    assert reverse is not None


def test_update_location_adjacency_is_additive(db):
    add_location("bed A")
    add_location("bed B")
    add_location("bed C")
    update_location("bed A", adjacent_to=["bed B"])
    update_location("bed A", adjacent_to=["bed C"])

    a = db.execute("SELECT id FROM locations WHERE name = 'bed A'").fetchone()
    links = db.execute(
        "SELECT * FROM location_adjacency WHERE location_id = ?", (a["id"],)
    ).fetchall()
    assert len(links) == 2


def test_update_location_not_found(db):
    result = update_location("nonexistent", sun_exposure="full sun")
    assert "No active location found" in result


def test_add_plant_basic(db):
    result = add_plant("cherry tomatoes")
    assert "cherry tomatoes" in result

    row = db.execute("SELECT * FROM plants WHERE id = 1").fetchone()
    assert row["name"] == "cherry tomatoes"
    assert row["active"] == 1


def test_add_plant_with_location(db):
    result = add_plant("basil", location="porch")
    assert "basil" in result
    assert "porch" in result

    # location should have been auto-created
    loc = db.execute("SELECT * FROM locations").fetchone()
    assert loc["name"] == "porch"

    plant = db.execute("SELECT * FROM plants WHERE id = 1").fetchone()
    assert plant["location_id"] == loc["id"]


def test_add_plant_creates_new_location_when_inactive(db):
    add_location("pot 5")
    update_location("pot 5", active=False)
    # adding a plant to a name with no active location creates a fresh one
    add_plant("mint", location="pot 5")

    rows = db.execute("SELECT * FROM locations WHERE name = 'pot 5'").fetchall()
    assert len(rows) == 2
    active = [r for r in rows if r["active"] == 1]
    assert len(active) == 1


def test_add_plant_reuses_existing_location(db):
    add_location("raised bed")
    add_plant("tomatoes", location="raised bed")
    add_plant("kale", location="raised bed")

    locations = db.execute("SELECT * FROM locations").fetchall()
    assert len(locations) == 1


def test_update_plant(db):
    add_plant("basil")
    result = update_plant("basil", active=False, notes="dried out")
    assert "Updated" in result

    row = db.execute("SELECT * FROM plants WHERE id = 1").fetchone()
    assert row["active"] == 0
    assert row["notes"] == "dried out"


def test_update_plant_not_found(db):
    result = update_plant("nonexistent")
    assert "No plant found" in result


def test_update_plant_change_location(db):
    add_plant("pepper", location="porch")
    update_plant("pepper", location="raised bed")

    plant = db.execute("SELECT * FROM plants WHERE id = 1").fetchone()
    loc = db.execute(
        "SELECT name FROM locations WHERE id = ?", (plant["location_id"],)
    ).fetchone()
    assert loc["name"] == "raised bed"


def test_get_plant_info(db):
    add_plant("cherry tomatoes", location="raised bed", variety="Sun Gold")
    result = get_plant_info("cherry tomatoes")
    assert "cherry tomatoes" in result
    assert "Sun Gold" in result
    assert "raised bed" in result


def test_get_plant_info_not_found(db):
    result = get_plant_info("nonexistent")
    assert "No plant found" in result


def test_get_plant_info_by_id(db):
    add_plant("basil")
    result = get_plant_info("1")
    assert "basil" in result


def test_get_plant_info_with_history(db):
    add_plant("basil", location="porch")
    log_activity("planted", "Planted basil", plant="basil", timestamp="2026-02-10T10:00:00")
    log_activity("observed", "Looking wilted", plant="basil", timestamp="2026-02-11T17:00:00",
                 possible_cause="overwatering")
    log_activity("fertilized", "Fish emulsion", plant="basil", timestamp="2026-02-12T09:00:00")

    result = get_plant_info("basil")
    assert "History" in result
    assert "planted" in result
    assert "observed" in result
    assert "fertilized" in result
    assert "overwatering" in result

    # should be in reverse chronological order
    fert_pos = result.index("fertilized")
    obs_pos = result.index("observed")
    plant_pos = result.index("planted")
    assert fert_pos < obs_pos < plant_pos
