import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    sun_exposure TEXT,   -- e.g. 'full sun', 'partial shade', 'full shade'
    size TEXT,           -- e.g. '4x8 ft'
    notes TEXT,          -- free-form spatial or soil notes
    active INTEGER NOT NULL DEFAULT 1,  -- 0 = removed/no longer in use
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS location_adjacency (
    location_id INTEGER NOT NULL REFERENCES locations(id),
    adjacent_id INTEGER NOT NULL REFERENCES locations(id),
    PRIMARY KEY (location_id, adjacent_id)
);

CREATE TABLE IF NOT EXISTS plants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    species TEXT,
    variety TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS plantings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_id INTEGER NOT NULL REFERENCES plants(id),
    location_id INTEGER REFERENCES locations(id),
    quantity INTEGER,           -- number of individual plants, if known
    date_planted DATE,
    date_removed DATE,
    active INTEGER NOT NULL DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    planting_id INTEGER REFERENCES plantings(id),
    location_id INTEGER REFERENCES locations(id),
    activity_type TEXT NOT NULL,  -- planted, fertilized, harvested, moved, etc.
    description TEXT NOT NULL,    -- original natural language text
    quantity TEXT,
    timestamp TIMESTAMP NOT NULL,
    source TEXT NOT NULL,         -- 'org_sync' or 'direct_log'
    org_timestamp_key TEXT,       -- dedup key from org-mode entries
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    planting_id INTEGER REFERENCES plantings(id),
    location_id INTEGER REFERENCES locations(id),
    observation TEXT NOT NULL,
    possible_cause TEXT,
    timestamp TIMESTAMP NOT NULL,
    source TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_timestamp TEXT NOT NULL UNIQUE,
    content_hash TEXT NOT NULL,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def init_db(conn: sqlite3.Connection):
    conn.executescript(SCHEMA)
