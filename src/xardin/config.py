import os

DB_PATH = os.environ.get("GARDEN_DB_PATH", os.path.join("data", "garden.db"))
GROWING_ZONE = os.environ.get("GARDEN_GROWING_ZONE")
REGION = os.environ.get("GARDEN_REGION")
LAST_FROST = os.environ.get("GARDEN_LAST_FROST")
FIRST_FROST = os.environ.get("GARDEN_FIRST_FROST")
