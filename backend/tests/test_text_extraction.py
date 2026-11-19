def test_pypdf_repair_warnings_are_silenced():
    import logging

    import app.processing.text_extraction  # noqa: F401

    assert not logging.getLogger("pypdf._utils").isEnabledFor(logging.WARNING)
