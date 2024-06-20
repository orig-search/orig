import textwrap
import re
import ast

WHITESPACE_RE = re.compile(r'\s+')

class ShortCircuitingVisitor(ast.NodeVisitor):
    """
    This visitor behaves more like libcst.CSTVisitor in that a visit_ method
    can return true or false to specify whether children get visited, and the
    visiting of children is not the responsibility of the visit_ method.
    """
    def visit(self, node):
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        rv = visitor(node)
        if rv:
            self.visit_children(node)

    def visit_children(self, node):
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        self.visit(item)
            elif isinstance(value, ast.AST):
                self.visit(value)

    def generic_visit(self, node) -> bool:
        return True


class FunctionFinder(ShortCircuitingVisitor):
    def __init__(self):
        self.covered_ranges = {}

    def visit_FunctionDef(self, node):
        first_node = node.decorator_list[0] if node.decorator_list else node
        self.covered_ranges[(first_node.lineno-1, node.end_lineno)] = node

def remove_whitespace_bookending(lines):
    while lines and WHITESPACE_RE.fullmatch(lines[0]):
        lines.pop(0)
    while lines and WHITESPACE_RE.fullmatch(lines[-1]):
        lines.pop(-1)
    return lines

def segment(mod: ast.Module):
    # Ensure we don't have unexpected positions by roundtripping first to lose
    # all potentially-custom whitespace, comments
    whitespace_removed_source = ast.unparse(mod)
    mod = ast.parse(whitespace_removed_source)

    ff = FunctionFinder()
    ff.visit(mod)
    lines = whitespace_removed_source.splitlines(True)
    prev = 0
    for (i, j), node in sorted(ff.covered_ranges.items()):
        if prev != i:
            between = "".join(remove_whitespace_bookending(lines[prev:i]))
            if between and not WHITESPACE_RE.fullmatch(between):
                yield (prev, i, textwrap.dedent(between))
        yield (i, j, ast.unparse(node))
        prev = j

    if prev != len(lines):
        between = "".join(remove_whitespace_bookending(lines[prev:len(lines)]))
        if between and not WHITESPACE_RE.fullmatch(between):
            yield (prev, len(lines), textwrap.dedent(between))


if __name__ == "__main__":
    import sys
    from pathlib import Path
    from .normalize import normalize
    for f in sys.argv[1:]:
        try:
            #TODO read_text is not correct
            mod = normalize(ast.parse(Path(f).read_text()))
            for item in list(segment(mod)):
                print("  ", item)
        except Exception as e:
            print(f"{f}: {e}")
