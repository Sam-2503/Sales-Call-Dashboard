def test_source_modules_import_without_side_effects() -> None:
    import cli

    assert cli.app.info.help == "Evidence-backed sales-call analysis."
