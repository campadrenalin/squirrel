from .identifier import ns
from .snippet import Snippet, Const as const
from .chain import Chain

def AND(*sections):
    return Chain.join(const.AND, sections)

def OR(*sections):
    return Chain.join(const.OR, sections)

def _ensure_table(table):
    if isinstance(table, str):
        return ns[table]
    return table

def _ensure_column(table, col):
    if isinstance(col, str):
        return table[col]
    return col

def _split_cols(*cols):
    if len(cols) == 1 and ' ' in cols[0]:
        return cols[0].split()
    return cols

def _table_columns(table, *cols):
    table = _ensure_table(table)
    return [_ensure_column(table, col) for col in _split_cols(*cols)]

def SELECT(table, *cols):
    cols = cols or (const.STAR,)
    return Chain([
        const.SELECT,
        Chain.join(const.COMMA, _table_columns(table, *cols)),
        const.FROM,
        _ensure_table(table),
    ])

def _comparisons(table, **kwargs):
    table = _ensure_table(table)
    return [table[k] == v for k,v in kwargs.items()]

def WHERE(*args, **kwargs):
    if kwargs:
        return _where(_ensure_table(args[0]), *args[1:], **kwargs)
    return _where(None, *args)

def _where(table, *args, **kwargs):
    clauses = list(args) + _comparisons(table, **kwargs)
    return Chain([ const.WHERE, AND(*clauses) ])

def _table_comparisons(primary_table, secondary_table, *cols):
    primary_table = _ensure_table(primary_table)
    secondary_table = _ensure_table(secondary_table)
    return [
        _ensure_column(secondary_table, c) == _ensure_column(primary_table, c)
        for c in _split_cols(*cols)
    ]

def JOIN(join_type, primary_table, secondary_table, *cols, raw_clauses=[], **kwargs):
    clauses = _table_comparisons(primary_table, secondary_table, *cols) \
            + _comparisons(secondary_table, **kwargs) \
            + raw_clauses
    assert clauses, "JOIN must have clauses"
    return Chain([join_type, _ensure_table(secondary_table), const.ON, AND(*clauses)])

def _is_blank(c):
    if c is None:
        return True
    if hasattr(c, '__len__') and len(c) == 0:
        return True
    return False

def _if_content(prefix, *content):
    if content == ():
        return Chain([])
    if len(content) == 1 and _is_blank(content[0]):
        return Chain([])
    return Chain([prefix, *content])

def GROUP_BY(*content):
    return _if_content(const.GROUP_BY, *content)

def ORDER_BY(*content):
    return _if_content(const.ORDER_BY, *content)

def LIMIT(*content):
    return _if_content(const.LIMIT, *content)

def OFFSET(*content):
    return _if_content(const.OFFSET, *content)

class FN(object):
    def __getattr__(self, name):
        def fn(*args, AS=None):
            if AS:
                AS = Snippet.from_sql(AS)
                args = [Chain([arg, const.AS, AS]) for arg in args]
            return Chain([
                Snippet.from_sql(name, pad_right=False),
                const.LPAREN,
                Chain.join(const.COMMA, args),
                const.RPAREN,
            ])
        return fn

fn = FN()
