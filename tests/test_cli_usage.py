from grafo_aprendizaje.cli import usage


def test_usage_names_the_entrypoints():
    text = usage()
    assert "grafo-ingerir" in text
    assert "grafo-mcp" in text
    assert "grafo-exportar" in text
    assert "neo4j-dump.sh" in text
    assert "neo4j-load.sh" in text
