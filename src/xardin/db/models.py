from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Location:
    id: int
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    @classmethod
    def from_row(cls, row) -> "Location":
        return cls(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            created_at=row["created_at"],
        )


@dataclass
class Plant:
    id: int
    name: str
    species: Optional[str] = None
    variety: Optional[str] = None
    date_planted: Optional[str] = None
    date_removed: Optional[str] = None
    location_id: Optional[int] = None
    active: int = 1
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_row(cls, row) -> "Plant":
        return cls(**{k: row[k] for k in row.keys()})


@dataclass
class Activity:
    id: int
    activity_type: str
    description: str
    timestamp: str
    source: str
    plant_id: Optional[int] = None
    location_id: Optional[int] = None
    quantity: Optional[str] = None
    org_timestamp_key: Optional[str] = None
    created_at: Optional[datetime] = None

    @classmethod
    def from_row(cls, row) -> "Activity":
        return cls(**{k: row[k] for k in row.keys()})


@dataclass
class Observation:
    id: int
    observation: str
    timestamp: str
    source: str
    plant_id: Optional[int] = None
    location_id: Optional[int] = None
    possible_cause: Optional[str] = None
    created_at: Optional[datetime] = None

    @classmethod
    def from_row(cls, row) -> "Observation":
        return cls(**{k: row[k] for k in row.keys()})
