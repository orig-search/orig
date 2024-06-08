import ast
import unittest

from orig.normalize import normalize


class NormalizeTest(unittest.TestCase):
    def test_noop(self):
        self.assertEqual("x = 1", ast.unparse(normalize(ast.parse("x=1"))))

    def test_annassign(self):
        self.assertEqual("x = 1", ast.unparse(normalize(ast.parse("x:int=1"))))

    def test_annassign_no_value(self):
        # not ideal, but there's no "local" statement that would do the
        # equivalent without a type or initial value
        self.assertEqual("x: int", ast.unparse(normalize(ast.parse("x:int"))))

    def test_funcdef(self):
        self.assertEqual(
            "def f(x):\n    pass", ast.unparse(normalize(ast.parse("def f(x): pass")))
        )

    def test_funcdef_type(self):
        self.assertEqual(
            "def f(x):\n    pass",
            ast.unparse(normalize(ast.parse("def f(x: int): pass"))),
        )

    def test_string_expr(self):
        # this does not change
        self.assertEqual("x = 'f'", ast.unparse(normalize(ast.parse("x = 'f'"))))

    def test_int_stmt(self):
        # this does not change
        self.assertEqual("1", ast.unparse(normalize(ast.parse("1"))))

    def test_string_stmt(self):
        self.assertEqual("x", ast.unparse(normalize(ast.parse("'f'\nx"))))
