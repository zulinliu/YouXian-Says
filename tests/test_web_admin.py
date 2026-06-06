"""Tests for web admin pages — import and structure checks."""


def test_create_page_imports():
    from web.pages.create import render_create_page
    assert callable(render_create_page)


def test_review_page_imports():
    from web.pages.review import render_review_page
    assert callable(render_review_page)


def test_publish_page_imports():
    from web.pages.publish import render_publish_page
    assert callable(render_publish_page)


def test_dashboard_page_imports():
    from web.pages.dashboard import render_dashboard_page
    assert callable(render_dashboard_page)


def test_settings_page_importable():
    from web.pages.settings import render_settings_page
    assert callable(render_settings_page)


def test_app_importable():
    from web.app import run_streamlit
    assert callable(run_streamlit)


def test_all_pages_in_navigation():
    import inspect
    import web.navigation as navigation_mod

    source = inspect.getsource(navigation_mod)
    assert "render_workspace_page" in source
    assert "render_create_page" in source
    assert "render_review_page" in source
    assert "render_publish_page" in source
    assert "render_dashboard_page" in source
    assert "render_settings_page" in source
