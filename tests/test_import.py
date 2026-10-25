def test_package_imports_without_side_effects() -> None:
    import call_analyser

    assert call_analyser.__version__ == "0.1.0"
