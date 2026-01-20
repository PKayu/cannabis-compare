# Database Rollback Guide

This guide covers common database migration scenarios and rollback procedures for the Utah Cannabis Aggregator.

## Alembic Commands

### Check Current Migration Status

```bash
cd backend
alembic current  # Show current migration version
alembic history  # Show migration history
```

### Rollback to Previous Migration

```bash
cd backend
alembic downgrade -1  # Rollback one migration
alembic downgrade <revision_id>  # Rollback to specific revision
alembic downgrade base  # Rollback to initial schema (all tables dropped)
```

### Apply Migrations

```bash
cd backend
alembic upgrade head  # Apply all pending migrations
alembic upgrade +1  # Apply next migration only
alembic upgrade <revision_id>  # Upgrade to specific revision
```

## Recreate Database from Scratch

### Option 1: Drop and Recreate Schema

```bash
# Connect to PostgreSQL and drop/recreate schema
psql -U postgres -d cannabis_aggregator -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Apply all migrations
cd backend
alembic upgrade head
```

### Option 2: Drop and Recreate Database

```bash
# Drop and recreate database
psql -U postgres -c "DROP DATABASE IF EXISTS cannabis_aggregator;"
psql -U postgres -c "CREATE DATABASE cannabis_aggregator;"

# Apply all migrations
cd backend
alembic upgrade head
```

## Backup Procedures

### Before Migration

Always backup before applying migrations to production:

```bash
# Full database backup
pg_dump -U postgres cannabis_aggregator > backup_$(date +%Y%m%d_%H%M%S).sql

# Specific table backup
pg_dump -U postgres -t products cannabis_aggregator > products_backup.sql
```

### Restore from Backup

```bash
# Full restore
psql -U postgres cannabis_aggregator < backup_20260119_120000.sql

# Restore specific table
psql -U postgres cannabis_aggregator < products_backup.sql
```

## Migration Best Practices

### DO:
- Always test migrations on a copy of production data first
- Create backups before applying migrations
- Review auto-generated migrations before applying
- Keep migration files for audit trail
- Use descriptive migration messages

### DON'T:
- Modify migrations after applying them to production
- Delete migration files from version control
- Run migrations directly on production without testing
- Skip migration versions

## Troubleshooting

### Migration Version Mismatch

If alembic reports version mismatch:

```bash
# Check current database version
alembic current

# Stamp database with specific version (dangerous - use carefully)
alembic stamp <revision_id>
```

### Failed Migration

If a migration fails partway:

1. Check error message for specific issue
2. Fix the migration file if possible
3. Rollback to previous version: `alembic downgrade -1`
4. Re-apply fixed migration: `alembic upgrade head`

### Table Already Exists

If creating tables that already exist:

```bash
# Option 1: Stamp the database to skip the migration
alembic stamp <revision_id>

# Option 2: Drop tables manually and re-run
psql -U postgres cannabis_aggregator -c "DROP TABLE IF EXISTS <table_name> CASCADE;"
alembic upgrade head
```

## Migration File Locations

- Alembic config: `backend/alembic.ini`
- Alembic env: `backend/alembic/env.py`
- Migrations: `backend/alembic/versions/`

## Current Schema Tables

| Table | Description |
|-------|-------------|
| users | User accounts for authentication |
| brands | Cannabis cultivators/brands |
| dispensaries | Utah pharmacy details |
| products | Master product entries |
| prices | Product-dispensary price junction |
| reviews | User product reviews |
| scraper_flags | Products needing manual review |
| promotions | Deals and discounts |
| alembic_version | Migration tracking (internal) |
