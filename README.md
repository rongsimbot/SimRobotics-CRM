# SimRobotics CRM

Customer Relationship Management database for SimRobotics Corp.

## Overview

PostgreSQL database powering SimRobotics' CRM operations — company profiles, contacts, interactions, military/government outreach, and opportunity tracking.

**Database:** `simrobotics_crm`  
**Host:** GPU Node (DESKTOP-EC24FP3) via SSH tunnel  
**Records:** 24,000+ across 7 tables

## Schema

| Table | Records | Description |
|-------|---------|-------------|
| `companies` | 11,523 | Company profiles with sector/region/business type |
| `contacts` | 12,552 | People at companies with roles, emails, LinkedIn |
| `interactions` | 0 | Communication log (calls, emails, meetings) |
| `military_bases` | 55 | US military installation data |
| `military_contacts` | 4 | Military POC records |
| `military_opportunities` | 0 | Defense contract opportunities |
| `military_outreach` | 85 | Outreach campaign tracking |

## Development

### Connecting

```bash
# Via SSH tunnel to GPU node
ssh -p 2223 simrobotics@localhost
PGPASSWORD='your_password' psql -h localhost -U sim_admin -d simrobotics_crm
```

### Schema Changes

All DDL changes should be tracked via migration files in `migrations/`.

## Status

🚧 Active development — defense sector pipeline, interaction tracking, and agent integration underway.
