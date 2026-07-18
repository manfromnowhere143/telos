import sphinx
from sphinx.roles import KbdRole

try:
    def role_node(text):
        role = KbdRole()
        nodes, messages = role('kbd', text, text, 1, None)
        assert not messages
        assert len(nodes) == 1
        return nodes[0]

    def standalone(key):
        node = role_node(key)
        assert node.astext() == key
        assert len(node.children) == 1
        assert node.children[0].astext() == key

    def compound(text, key1, separator, key2):
        node = role_node(text)
        assert node.astext() == text
        assert len(node.children) == 3
        assert node.children[0].astext() == key1
        assert node.children[1].astext() == separator
        assert node.children[2].astext() == key2
        assert 'kbd' in node.children[0].get('classes', [])
        assert 'kbd' in node.children[2].get('classes', [])

    standalone('+')
    standalone('^')
    compound('Shift-+', 'Shift', '-', '+')
    compound('Ctrl+^', 'Ctrl', '+', '^')
    compound('Meta^-', 'Meta', '^', '-')
    print(f"RESULT={('PASS',)!r}")
except AssertionError:
    print(f"RESULT={('FAIL', 'kbd structure')!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
