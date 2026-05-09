"""
CalcScript Semantic Analyzer & Symbol Table
Checks for undefined variables, type mismatches, return paths, etc.
"""

from typing import Dict, List, Optional, Any
from ast_nodes import *


class SemanticError(Exception):
    def __init__(self, message: str, line: int, col: int):
        super().__init__(f"[Line {line}, Col {col}] SemanticError: {message}")
        self.line = line
        self.col = col


class SymbolTable:
    """Scoped symbol table."""

    def __init__(self, parent: Optional['SymbolTable'] = None):
        self.table: Dict[str, Any] = {}
        self.parent = parent

    def define(self, name: str, value: Any):
        self.table[name] = value

    def lookup(self, name: str) -> Any:
        if name in self.table:
            return self.table[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def exists(self, name: str) -> bool:
        return self.lookup(name) is not None

    def assign(self, name: str, value: Any) -> bool:
        """Update existing variable in nearest scope that has it."""
        if name in self.table:
            self.table[name] = value
            return True
        if self.parent:
            return self.parent.assign(name, value)
        return False

    def dump(self, indent=0) -> str:
        lines = []
        pad = '  ' * indent
        for k, v in self.table.items():
            lines.append(f"{pad}{k} = {v!r}")
        if self.parent:
            lines.append(f"{pad}[parent scope]")
            lines.append(self.parent.dump(indent + 1))
        return '\n'.join(lines)


BUILTIN_NAMES = {'sin','cos','tan','asin','acos','atan','sqrt','log','abs'}


class SemanticAnalyzer:
    """
    Walk the AST once and report semantic errors.
    Does not evaluate – only checks names and simple types.
    """

    def __init__(self):
        self.global_scope = SymbolTable()
        self.current_scope = self.global_scope
        self.functions: Dict[str, FuncDef] = {}
        self.errors: List[str] = []
        self.in_function = False

    def error(self, msg, line, col):
        self.errors.append(f"[Line {line}, Col {col}] SemanticError: {msg}")

    def analyze(self, program: Program):
        # First pass: collect all function definitions
        for stmt in program.statements:
            if isinstance(stmt, FuncDef):
                self.functions[stmt.name] = stmt
                self.global_scope.define(stmt.name, f"<func:{stmt.name}>")

        # Second pass: full walk
        for stmt in program.statements:
            self.check_stmt(stmt)

        return self.errors

    def check_stmt(self, node: ASTNode):
        if isinstance(node, VarDecl):
            self.check_expr(node.value)
            self.current_scope.define(node.name, True)

        elif isinstance(node, Assignment):
            if not self.current_scope.exists(node.name):
                self.error(f"Assignment to undeclared variable '{node.name}'", node.line, node.col)
            self.check_expr(node.value)

        elif isinstance(node, PrintStmt):
            self.check_expr(node.expr)

        elif isinstance(node, ReturnStmt):
            if not self.in_function:
                self.error("'return' used outside of a function", node.line, node.col)
            self.check_expr(node.expr)

        elif isinstance(node, IfStmt):
            self.check_expr(node.condition)
            for s in node.then_body:
                self.check_stmt(s)
            if node.else_body:
                for s in node.else_body:
                    self.check_stmt(s)

        elif isinstance(node, WhileStmt):
            self.check_expr(node.condition)
            for s in node.body:
                self.check_stmt(s)

        elif isinstance(node, FuncDef):
            prev_scope = self.current_scope
            self.current_scope = SymbolTable(parent=self.global_scope)
            prev_in_func = self.in_function
            self.in_function = True
            for param in node.params:
                self.current_scope.define(param, True)
            for s in node.body:
                self.check_stmt(s)
            self.in_function = prev_in_func
            self.current_scope = prev_scope

        elif isinstance(node, ModeStmt):
            pass  # always valid

    def check_expr(self, node: ASTNode):
        if isinstance(node, (NumberLiteral, StringLiteral, BoolLiteral)):
            pass

        elif isinstance(node, Identifier):
            if not self.current_scope.exists(node.name):
                self.error(f"Undefined variable '{node.name}'", node.line, node.col)

        elif isinstance(node, BinaryOp):
            self.check_expr(node.left)
            self.check_expr(node.right)

        elif isinstance(node, UnaryOp):
            self.check_expr(node.operand)

        elif isinstance(node, BuiltinCall):
            self.check_expr(node.arg)

        elif isinstance(node, FunctionCall):
            if node.name not in self.functions:
                self.error(f"Undefined function '{node.name}'", node.line, node.col)
            else:
                fd = self.functions[node.name]
                if len(node.args) != len(fd.params):
                    self.error(
                        f"Function '{node.name}' expects {len(fd.params)} arg(s), "
                        f"got {len(node.args)}",
                        node.line, node.col
                    )
            for arg in node.args:
                self.check_expr(arg)
