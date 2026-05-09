"""
CalcScript Interpreter
Tree-walk interpreter that directly evaluates the AST.
"""

import math
from typing import Any, List, Optional
from ast_nodes import *
from semantic import SymbolTable


class RuntimeError_(Exception):
    def __init__(self, message: str, line: int = 0, col: int = 0):
        super().__init__(f"[Line {line}, Col {col}] RuntimeError: {message}")
        self.line = line
        self.col = col


class ReturnSignal(Exception):
    """Used to unwind the call stack on 'return'."""
    def __init__(self, value):
        self.value = value


class Interpreter:
    def __init__(self):
        self.global_scope = SymbolTable()
        self.current_scope = self.global_scope
        self.functions = {}
        self.angle_mode = 'deg'   # 'deg' or 'rad'
        self.output: List[str] = []

    def _to_rad(self, x):
        return math.radians(x) if self.angle_mode == 'deg' else x

    def _from_rad(self, x):
        return math.degrees(x) if self.angle_mode == 'deg' else x

    # ── Execution entry ───────────────────────────────────────────────────────

    def execute(self, program: Program):
        # Collect functions first
        for stmt in program.statements:
            if isinstance(stmt, FuncDef):
                self.functions[stmt.name] = stmt
        for stmt in program.statements:
            self.exec_stmt(stmt)

    def exec_block(self, stmts: List[ASTNode], scope: SymbolTable):
        prev = self.current_scope
        self.current_scope = scope
        try:
            for stmt in stmts:
                self.exec_stmt(stmt)
        finally:
            self.current_scope = prev

    def exec_stmt(self, node: ASTNode):
        if isinstance(node, VarDecl):
            val = self.eval_expr(node.value)
            self.current_scope.define(node.name, val)

        elif isinstance(node, Assignment):
            val = self.eval_expr(node.value)
            if not self.current_scope.assign(node.name, val):
                raise RuntimeError_(f"Undefined variable '{node.name}'", node.line, node.col)

        elif isinstance(node, PrintStmt):
            val = self.eval_expr(node.expr)
            out = self._fmt(val)
            self.output.append(out)
            print(out)

        elif isinstance(node, ReturnStmt):
            raise ReturnSignal(self.eval_expr(node.expr))

        elif isinstance(node, IfStmt):
            cond = self.eval_expr(node.condition)
            self._assert_bool_or_num(cond, node.condition)
            if self._truthy(cond):
                scope = SymbolTable(parent=self.current_scope)
                self.exec_block(node.then_body, scope)
            elif node.else_body is not None:
                scope = SymbolTable(parent=self.current_scope)
                self.exec_block(node.else_body, scope)

        elif isinstance(node, WhileStmt):
            iterations = 0
            MAX_ITER = 100_000
            while True:
                cond = self.eval_expr(node.condition)
                if not self._truthy(cond):
                    break
                iterations += 1
                if iterations > MAX_ITER:
                    raise RuntimeError_(
                        f"Loop exceeded {MAX_ITER} iterations (infinite loop guard)",
                        node.line, node.col
                    )
                scope = SymbolTable(parent=self.current_scope)
                self.exec_block(node.body, scope)

        elif isinstance(node, FuncDef):
            self.functions[node.name] = node

        elif isinstance(node, ModeStmt):
            self.angle_mode = node.mode
            print(f"[Angle mode set to {self.angle_mode.upper()}]")

    # ── Expression evaluator ──────────────────────────────────────────────────

    def eval_expr(self, node: ASTNode) -> Any:
        if isinstance(node, NumberLiteral):
            return node.value

        if isinstance(node, StringLiteral):
            return node.value

        if isinstance(node, BoolLiteral):
            return node.value

        if isinstance(node, Identifier):
            val = self.current_scope.lookup(node.name)
            if val is None and not self.current_scope.exists(node.name):
                raise RuntimeError_(f"Undefined variable '{node.name}'", node.line, node.col)
            return val

        if isinstance(node, UnaryOp):
            operand = self.eval_expr(node.operand)
            if node.op == '-':
                self._assert_number(operand, node)
                return -operand
            if node.op == 'not':
                return not self._truthy(operand)

        if isinstance(node, BinaryOp):
            return self.eval_binary(node)

        if isinstance(node, BuiltinCall):
            return self.eval_builtin(node)

        if isinstance(node, FunctionCall):
            return self.call_function(node)

        raise RuntimeError_(f"Unknown AST node: {type(node).__name__}", node.line, node.col)

    def eval_binary(self, node: BinaryOp) -> Any:
        op = node.op

        # Short-circuit logical
        if op == 'and':
            left = self.eval_expr(node.left)
            return left if not self._truthy(left) else self.eval_expr(node.right)
        if op == 'or':
            left = self.eval_expr(node.left)
            return left if self._truthy(left) else self.eval_expr(node.right)

        left  = self.eval_expr(node.left)
        right = self.eval_expr(node.right)

        # Arithmetic
        if op == '+':
            if isinstance(left, str) or isinstance(right, str):
                return str(left) + str(right)
            self._assert_number(left, node); self._assert_number(right, node)
            return left + right
        if op == '-':
            self._assert_number(left, node); self._assert_number(right, node)
            return left - right
        if op == '*':
            self._assert_number(left, node); self._assert_number(right, node)
            return left * right
        if op == '/':
            self._assert_number(left, node); self._assert_number(right, node)
            if right == 0:
                raise RuntimeError_("Division by zero", node.line, node.col)
            return left / right
        if op == '^':
            self._assert_number(left, node); self._assert_number(right, node)
            return left ** right
        if op == 'mod':
            self._assert_number(left, node); self._assert_number(right, node)
            if right == 0:
                raise RuntimeError_("Modulo by zero", node.line, node.col)
            return left % right

        # Comparison
        if op == '==': return left == right
        if op == '!=': return left != right
        if op == '<':
            self._assert_same_type(left, right, node)
            return left < right
        if op == '<=':
            self._assert_same_type(left, right, node)
            return left <= right
        if op == '>':
            self._assert_same_type(left, right, node)
            return left > right
        if op == '>=':
            self._assert_same_type(left, right, node)
            return left >= right

        raise RuntimeError_(f"Unknown operator '{op}'", node.line, node.col)

    def eval_builtin(self, node: BuiltinCall) -> float:
        arg = self.eval_expr(node.arg)
        self._assert_number(arg, node)
        name = node.name

        if name == 'abs':  return abs(arg)
        if name == 'sqrt':
            if arg < 0:
                raise RuntimeError_("sqrt of negative number", node.line, node.col)
            return math.sqrt(arg)
        if name == 'log':
            if arg <= 0:
                raise RuntimeError_("log of non-positive number", node.line, node.col)
            return math.log10(arg)
        if name == 'sin':  return math.sin(self._to_rad(arg))
        if name == 'cos':  return math.cos(self._to_rad(arg))
        if name == 'tan':
            r = self._to_rad(arg)
            if abs(math.cos(r)) < 1e-15:
                raise RuntimeError_("tan undefined at this angle", node.line, node.col)
            return math.tan(r)
        if name == 'asin':
            if not (-1 <= arg <= 1):
                raise RuntimeError_("asin argument out of range [-1, 1]", node.line, node.col)
            return self._from_rad(math.asin(arg))
        if name == 'acos':
            if not (-1 <= arg <= 1):
                raise RuntimeError_("acos argument out of range [-1, 1]", node.line, node.col)
            return self._from_rad(math.acos(arg))
        if name == 'atan':
            return self._from_rad(math.atan(arg))

        raise RuntimeError_(f"Unknown builtin '{name}'", node.line, node.col)

    def call_function(self, node: FunctionCall) -> Any:
        if node.name not in self.functions:
            raise RuntimeError_(f"Undefined function '{node.name}'", node.line, node.col)
        fd = self.functions[node.name]
        if len(node.args) != len(fd.params):
            raise RuntimeError_(
                f"Function '{node.name}' expects {len(fd.params)} arg(s), got {len(node.args)}",
                node.line, node.col
            )
        arg_vals = [self.eval_expr(a) for a in node.args]
        local_scope = SymbolTable(parent=self.global_scope)
        for param, val in zip(fd.params, arg_vals):
            local_scope.define(param, val)

        prev = self.current_scope
        self.current_scope = local_scope
        result = None
        try:
            for stmt in fd.body:
                self.exec_stmt(stmt)
        except ReturnSignal as r:
            result = r.value
        finally:
            self.current_scope = prev
        return result

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _truthy(self, val) -> bool:
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)):
            return val != 0
        if isinstance(val, str):
            return len(val) > 0
        return val is not None

    def _assert_number(self, val, node):
        if not isinstance(val, (int, float)):
            raise RuntimeError_(
                f"Expected number, got {type(val).__name__} ({val!r})",
                node.line, node.col
            )

    def _assert_bool_or_num(self, val, node):
        if not isinstance(val, (int, float, bool)):
            raise RuntimeError_(
                f"Condition must be a number or boolean, got {type(val).__name__}",
                node.line, node.col
            )

    def _assert_same_type(self, a, b, node):
        # Numbers (int and float) are compatible with each other
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return
        if type(a) != type(b):
            raise RuntimeError_(
                f"Cannot compare {type(a).__name__} and {type(b).__name__}",
                node.line, node.col
            )

    def _fmt(self, val) -> str:
        if isinstance(val, bool):
            return 'true' if val else 'false'
        if isinstance(val, float) and val == int(val):
            return str(int(val))
        if val is None:
            return 'null'
        return str(val)

    # ── Debug helpers ─────────────────────────────────────────────────────────

    def dump_symbol_table(self) -> str:
        lines = ["=== Symbol Table ==="]
        for k, v in self.global_scope.table.items():
            lines.append(f"  {k} = {v!r}")
        if self.functions:
            lines.append("--- Functions ---")
            for name, fd in self.functions.items():
                lines.append(f"  func {name}({', '.join(fd.params)})")
        return '\n'.join(lines)
