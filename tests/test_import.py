def test_source_modules_import_without_side_effects() -> None:
    import pipeline

    assert pipeline.AnalyseInput.__name__ == "AnalyseInput"
