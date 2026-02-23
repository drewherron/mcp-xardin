# mcp-xardin

An MCP server for garden management. Connects to any MCP-compatible AI client
and gives it persistent memory of your garden (what's planted, where, and what's
happened to it). Then you can use the LLM's general knowledge for gardening advice,
using your own garden data for context. I was often asking various LLMs for
gardening advice, and I thought it would be nice to get advice without repeatedly
typing out huge amounts of context about my current situation.

The server manages a SQLite database of plants, locations, and activity history.
The AI client handles all the natural language understanding; the server handles
structured storage and retrieval.

It does work from a standard LLM prompt input, but currently the only option for
file import is with Emacs' Org mode format. Markdown support should be coming soon.

I built this to fit my own personal workflow: while gardening I create a quick note
using the [Orgzly](https://github.com/orgzly) widget on my phone. Notes then sync
to a desktop/laptop via [Syncthing](https://github.com/syncthing). Later, I can
have an LLM use the `sync_notes` tool, which parses the Org file and hands the entries
back for the AI to interpret and log.

With minimal changes, this code could easily be adapted to many other
uses where you just want to preserve a structured, persistent memory for an LLM.

## Tools

Tools available to the AI to interact with the SQLite database:

| Tool              | What it does                                                           |
|-------------------|------------------------------------------------------------------------|
| `sync_notes`      | Parse an Org file and import new entries                               |
| `log_activity`    | Log a single activity or observation                                   |
| `log_activities`  | Log a batch of activities                                              |
| `add_plant`       | Register a plant type (species, variety)                               |
| `update_plant`    | Update a plant type's species, variety, or notes                       |
| `add_planting`    | Record a group of a plant type growing in a specific location          |
| `update_planting` | Update a planting's status, quantity, or dates                         |
| `add_location`    | Add a garden location                                                  |
| `update_location` | Update a location's attributes or adjacency links                      |
| `get_plant_info`  | Full details and history for a plant type, including all its plantings |
| `execute_query`   | Run a read-only SQL query against the database                         |

## Resources

Resources give the AI ambient context without explicit queries:

- `garden://context` — growing zone and region
- `garden://plants` — all registered plant types; those with active plantings show location details, others appear as catalog entries (e.g. seeds on hand)
- `garden://locations` — locations with attributes and what's planted in each
- `garden://recent-activity` — last 30 activities and observations
- `garden://schema` — database schema (for SQL generation)

## Setup

```bash
pip install -e ".[dev]"
```

Configure the MCP server in your client. For Claude Code:

```bash
claude mcp add xardin -- python -m xardin
```

By default the database is created automatically at `data/garden.db` on first run.

### Configuration

These values are read from environment variables at startup. Set them in your
shell profile or pass them inline when registering the MCP server. All location
variables are optional but recommended — they are exposed via the `garden://context`
resource so the AI can give location-appropriate advice without you having to repeat
yourself. These are supplied to the LLM so there's not really any mandatory format.

| Variable              | Default          | Description                 |
|-----------------------|------------------|-----------------------------|
| `GARDEN_DB_PATH`      | `data/garden.db` | Path to the SQLite database |
| `GARDEN_GROWING_ZONE` | _(unset)_        | USDA hardiness zone         |
| `GARDEN_REGION`       | _(unset)_        | Region for climate context  |
| `GARDEN_LAST_FROST`   | _(unset)_        | Average last frost date     |
| `GARDEN_FIRST_FROST`  | _(unset)_        | Average first frost date    |

For Claude Code, environment variables can be set in `.mcp.json` at the project
root:

```json
{
  "mcpServers": {
    "xardin": {
      "command": "python",
      "args": ["-m", "xardin"],
      "env": {
        "GARDEN_GROWING_ZONE": "6b",
        "GARDEN_REGION": "Midwest",
        "GARDEN_LAST_FROST": "April 15",
        "GARDEN_FIRST_FROST": "October 15"
      }
    }
  }
}
```

## Plants and plantings

Plants and plantings are separate concepts. A plant type is registered once with
`add_plant` — it holds the species, variety, and general notes. Each group of that
plant growing somewhere is a separate planting, created with `add_planting`, which
has its own location, optional quantity, dates, and active status.

This means you can start peppers in a seed tray, then transplant some to the raised
bed and some to pots, and track each group independently. If one group dies from
frost while the others are fine, you call `update_planting` with `active=false` for
just that group.

When a planting is finished (harvested, died, pulled out), mark it inactive with
`update_planting`. When a physical location is removed or no longer in use, mark it
inactive with `update_location`. In both cases the historical data is preserved.

## Locations

Locations support attributes for richer gardening advice:

```
update_location("Bed A", sun_exposure="full sun", size="4x8 ft",
                notes="South-facing, against fence",
                adjacent_to=["Bed B"])
```

Adjacency links are symmetric — marking A adjacent to B also marks B adjacent to A.
They're additive; call `update_location` again to add more neighbors.

When a bed or pot is removed, it is marked inactive rather than deleted. This is to
preserve historical data. If you later create a new location with the same name
(e.g. after moving), it gets a fresh record with no inherited attributes or adjacency links.

## Org-mode workflow

All entries in the Org file must be top-level headings; sub-headings are treated as body text and their timestamps are ignored. This would probably cause unwanted results. If you want to add clearly separate entries to the same note/timestamp, the LLM should create multiple entries using the same timestamp. Sometimes that doesn't matter at all: `plants` have no timestamp, so when I buy a bunch of seed packs I just list them all in one note, the AI gets each into the `plants` table on its own row.

Re-importing the same file won't cause any issues, there's a built-in deduplication
check by timestamp + content. Two entries with the same timestamp are treated as the
same entry. Edited entries (same timestamp, changed text) are flagged as updated and
re-imported.

Note: since standard Org timestamps don't include seconds, two entries created within
the same minute will collide.

Entries should be top-level headings with a `:CREATED:` property:

```org
* Planted 4 Super Sweet 100 tomatoes in the raised bed 
:PROPERTIES:
:CREATED:  [2026-04-25 Sat 13:05]
:END:
```

**Time is optional in the timestamp.** Inline timestamps would also work, with either angled or square brackets.

The initial mention of a plant or location should be more detailed, so that the details can be added to
the respective tables. A later entry could say "fertilized the tomatoes", and if there's only one option
for tomatoes, that event will be recorded for the correct plant.

An entry about an existing plant (an active planting) might be about an event (e.g., fertilized, pruned, harvested,
moved, treated, etc.) or simply an observation, and it will be recorded in the database,
basically like a gardening diary/log entry.

```org
* Basil underwatered, wilted in the sun
:PROPERTIES:
:CREATED:  [2026-06-28 Sun 17:45]
:END:
```

Org notes can be more than a heading; you can provide additional data in the note text. Assuming we'd
already put the calendula in the database when starting the seeds indoors, we could import the note:

```org
* Transplanted calendula outdoors
:PROPERTIES:
:CREATED:  [2026-04-21 Tue 15:32]
:END:
Put them in pots 3, 4, 5, and 6. 6 and 5 are by the front door and the other two are near the tomatoes.
```

The LLM should be smart enough to take this note and:

1. Read `garden://plants` to confirm calendula exists and to find which location
   the tomatoes are in
2. Read `garden://locations` to see which of the four pots already exist
3. Call `add_planting` for calendula in each of the four pots, creating any pots
   that don't exist yet automatically
4. Call `log_activities` to record the transplant event for each pot
5. Call `update_location` for pots 5 and 6 with `notes="by the front door"` rather
   than creating a spurious "front door" location
6. Call `update_location` for pots 3 and 4 with `adjacent_to` pointing to whichever
   location the tomatoes are in (looked up in step 1)

However, you do want to be clear and unambiguous for the LLM. You could use this MCP server without
knowing anything in this README beyond the installation. But knowing details like the SQL schema and the available
MCP tools/resources allows you as a user to be very precise in your notes. I would probably never enter a
note like the last example. Instead I might have two notes:

```org
* Create locations for Pots 3 through 6
:PROPERTIES:
:CREATED:  [2026-04-21 Tue 15:32]
:END:
3 and 4 are adjacent to Bed A
5 and 6 are near the front door

* Transplant calendula outdoors
:PROPERTIES:
:CREATED:  [2026-04-21 Tue 15:35]
:END:
To pots 3, 4, 5, and 6
```

There's a good chance the result will be the same in either case, but you don't want to leave room for surprises.

## Name

In case you're curious:

[**xardín**](https://en.wiktionary.org/wiki/xard%C3%ADn) /ʃaɾˈdin/ - Galician/Asturian for 'garden'
