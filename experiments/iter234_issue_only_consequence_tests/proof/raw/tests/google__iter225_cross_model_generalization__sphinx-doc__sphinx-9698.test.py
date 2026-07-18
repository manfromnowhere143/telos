import docutils.utils
import docutils.statemachine
from docutils import nodes
from sphinx.domains.python import PyMethod

class Mock:
    def __getattr__(self, name): return None

def run():
    try:
        config = Mock()
        config.add_function_parentheses = True
        config.toc_object_entries = True
        config.toc_object_entries_show_parents = 'domain'
        config.python_use_unqualified_type_names = False
        
        domain = Mock()
        domain.name = 'py'
        domain.note_object = lambda *a, **kw: None
        
        env = Mock()
        env.config = config
        env.domaindata = {'py': {'objects': {}, 'modules': {}}}
        env.ref_context = {}
        env.temp_data = {}
        env.domains = {'py': domain}
        env.app = Mock()
        env.app.emit = lambda *a, **kw: None
        env.new_serialno = lambda cat: 0
        env.get_domain = lambda name: env.domains[name]
        
        settings = Mock()
        settings.env = env
        settings.language_code = 'en'
        settings.id_prefix = ''
        settings.auto_id_prefix = 'id'
        
        document = docutils.utils.new_document('test', settings)
        state = Mock()
        state.document = document
        
        directive = PyMethod(
            name='py:method', arguments=['Foo.bar'], options={'property': None},
            content=docutils.statemachine.StringList([]), lineno=1, content_offset=0,
            block_text='.. py:method:: Foo.bar\n   :property:\n',
            state=state, state_machine=None,
        )
        
        def get_entries(nodes_list):
            entries = []
            for n in nodes_list:
                if isinstance(n, nodes.index):
                    entries.extend(n['entries'])
                elif hasattr(n, 'children'):
                    entries.extend(get_entries(n.children))
            return entries

        entries = get_entries(directive.run())
        if not entries:
            print(f"RESULT={('FAIL', 'No entries in index node')!r}")
            return
            
        text = entries[0][1]
        if "bar()" in text:
            print(f"RESULT={('FAIL', f'Index entry has parens: {text}')!r}")
        else:
            print(f"RESULT={('PASS',)!r}")

    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")

run()
