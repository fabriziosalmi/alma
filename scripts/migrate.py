#!/usr/bin/env python
"""Database migration helper script."""

import sys
from pathlib import Path

from alembic import command
from alembic.config import Config

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def get_alembic_config() -> Config:
    """Get Alembic configuration."""
    alembic_cfg = Config(str(project_root / "alembic.ini"))
    return alembic_cfg


def upgrade(revision: str = "head") -> None:
    """
    Upgrade database to a specific revision.

    Args:
        revision: Target revision (default: head)
    """
    print(f"Upgrading database to {revision}...")
    alembic_cfg = get_alembic_config()
    command.upgrade(alembic_cfg, revision)
    print("✓ Database upgraded successfully")


def downgrade(revision: str = "-1") -> None:
    """
    Downgrade database to a specific revision.

    Args:
        revision: Target revision (default: -1, previous version)
    """
    print(f"Downgrading database to {revision}...")
    alembic_cfg = get_alembic_config()
    command.downgrade(alembic_cfg, revision)
    print("✓ Database downgraded successfully")


def current() -> None:
    """Show current database revision."""
    alembic_cfg = get_alembic_config()
    command.current(alembic_cfg)


def history() -> None:
    """Show migration history."""
    alembic_cfg = get_alembic_config()
    command.history(alembic_cfg)


def create_migration(message: str, autogenerate: bool = True) -> None:
    """
    Create a new migration.

    Args:
        message: Migration message
        autogenerate: Auto-generate migration from models
    """
    print(f"Creating migration: {message}")
    alembic_cfg = get_alembic_config()
    command.revision(
        alembic_cfg,
        message=message,
        autogenerate=autogenerate,
    )
    print("✓ Migration created successfully")


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/migrate.py upgrade [revision]")
        print("  python scripts/migrate.py downgrade [revision]")
        print("  python scripts/migrate.py current")
        print("  python scripts/migrate.py history")
        print("  python scripts/migrate.py create <message>")
        sys.exit(1)

    command_name = sys.argv[1]

    if command_name == "upgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "head"
        upgrade(revision)
    elif command_name == "downgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "-1"
        downgrade(revision)
    elif command_name == "current":
        current()
    elif command_name == "history":
        history()
    elif command_name == "create":
        if len(sys.argv) < 3:
            print("Error: Migration message required")
            sys.exit(1)
        message = sys.argv[2]
        create_migration(message)
    else:
        print(f"Unknown command: {command_name}")
        sys.exit(1)


if __name__ == "__main__":
    main()
