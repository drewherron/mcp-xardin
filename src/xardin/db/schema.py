import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS plants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    species TEXT,
    variety TEXT,
    date_planted DATE,
    date_removed DATE,
    location_id INTEGER REFERENCES locations(id),
    status TEXT NOT NULL DEFAULT 'active',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_id INTEGER REFERENCES plants(id),
    location_id INTEGER REFERENCES locations(id),
    activity_type TEXT NOT NULL,
    description TEXT NOT NULL,
    quantity TEXT,
    timestamp TIMESTAMP NOT NULL,
    source TEXT NOT NULL,
    org_timestamp_key TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_id INTEGER REFERENCES plants(id),
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
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'success'
);
"""


def init_db(conn: sqlite3.Connection):
    conn.executescript(SCHEMA)
