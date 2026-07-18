from sphinx.ext import viewcode

class SimpleMock:
    def __getattr__(self, name):
        return SimpleMock()
    def __call__(self, *args, **kwargs):
        return SimpleMock()
    def __str__(self):
        return "mock"

class MockConfig(SimpleMock):
    viewcode_enable_epub = False

class MockEnv(SimpleMock):
    def __init__(self):
        # Provide a realistic entry to test if pages are incorrectly collected
        self._viewcode_modules = {'test_module': ("def foo(): pass", {}, {}, "test_ref")}
        self.config = MockConfig()
        self.app = SimpleMock()

class MockBuilder(SimpleMock):
    def __init__(self):
        self.name = 'epub'
        self.format = 'html'
        self.env = MockEnv()
        self.config = MockConfig()
        self.highlighter = SimpleMock()
        
    def get_relative_uri(self, from_, to):
        return ''

class MockApp(SimpleMock):
    def __init__(self):
        self.builder = MockBuilder()
        self.config = MockConfig()

def test_viewcode():
    app = MockApp()
    try:
        # If the bug is fixed, the function returns early due to builder='epub' 
        # and viewcode_enable_epub=False, yielding 0 pages.
        # If the bug is present, it will process the dummy entry and either 
        # successfully yield a page or crash. Both indicate the bug is present.
        pages = list(viewcode.collect_pages(app))
        if len(pages) > 0:
            return "FAIL", f"Expected 0 pages, got {len(pages)}"
        return "PASS", ""
    except Exception as e:
        return "FAIL", f"Exception {type(e).__name__}: {e} (likely didn't return early)"

if __name__ == "__main__":
    try:
        status, detail = test_viewcode()
        if status == "PASS":
            print(f"RESULT={('PASS',)!r}")
        else:
            print(f"RESULT={('FAIL', detail)!r}")
    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")
