from mcp_server.settings import load_postgres_source_config


def test_postgres_sources_config_loads() -> None:
    config = load_postgres_source_config()

    assert "public" in config.schemas
    assert config.query_schema == "public"
    assert config.qualified_table == "public.vw_ft_dados_analiticos_union"


def test_qualified_table_for_detail_source() -> None:
    config = load_postgres_source_config()

    assert config.qualified_table_for("orchard_detail") == "public.ft_orchard_dados_analiticos"
    assert config.qualified_table_for("warner_chappell_detail") == "warner_chappell.stg_warner_statement"
