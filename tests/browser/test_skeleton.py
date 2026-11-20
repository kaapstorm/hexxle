from testsweet import test

from hexxle.site import site_server
from tests.browser.support import open_page


@test
def page_runs_micropython_and_imports_core():
    with site_server() as base, open_page(base) as page:
        text = page.locator('#message').inner_text()
        assert text == 'core ok'


@test
def page_works_from_a_subdirectory():
    with site_server(prefix='sub/') as base, open_page(base) as page:
        text = page.locator('#message').inner_text()
        assert base.endswith('/sub/')
        assert text == 'core ok'
