from mcp_server.settings import load_postgres_source_config


def test_postgres_sources_config_loads() -> None:
    config = load_postgres_source_config()

    assert "public" in config.schemas
    assert config.query_schema == "public"
    assert config.qualified_table == "public.vw_ft_dados_analiticos_union"
