from analyser_api.db.dsn import asyncpg_dsn
from analyser_api.db.models import Base


def test_neon_dsn_is_normalized_for_asyncpg() -> None:
    value = "postgresql://user:pass@host/db?sslmode=require&channel_binding=require"
    assert asyncpg_dsn(value) == "postgresql+asyncpg://user:pass@host/db?ssl=require"


def test_plain_postgres_dsn_preserves_non_provider_options() -> None:
    value = "postgres://user:pass@host/db?application_name=analyser"
    assert asyncpg_dsn(value) == (
        "postgresql+asyncpg://user:pass@host/db?application_name=analyser"
    )


def test_metadata_contains_required_tables_and_indexes() -> None:
    tables = set(Base.metadata.tables)
    assert {
        "workspaces",
        "agents",
        "calls",
        "jobs",
        "job_events",
        "reports",
        "call_category_scores",
        "call_item_results",
        "report_findings",
        "feedback",
        "stage_cache",
    } <= tables
    indexes = {index.name for table in Base.metadata.tables.values() for index in table.indexes}
    assert "uq_active_job_per_call" in indexes
    assert "ix_job_events_job_id_id" in indexes
