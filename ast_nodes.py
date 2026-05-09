"""
CalcScript AST Nodes
"""

from dataclasses import dataclass
from typing import List, Optional, Any


# ── Base ──────────────────────────────────────────────────────────────────────

@dataclass
class ASTNode:
    line: int = 0
    col: int  = 0


# ── Expressions ───────────────────────────────────────────────────────────────

@dataclass
class NumberLiteral(ASTNode):
    value: float = 0.0

@dataclass
class StringLiteral(ASTNode):
    value: str = ""

@dataclass
class BoolLiteral(ASTNode):
    value: bool = False

@dataclass
class Identifier(ASTNode):
    name: str = ""

@dataclass
class BinaryOp(ASTNode):
    op: str = ""
    left: Any = None
    right: Any = None

@dataclass
class UnaryOp(ASTNode):
    op: str = ""
    operand: Any = None

@dataclass
class BuiltinCall(ASTNode):
    name: str = ""
    arg: Any = None

@dataclass
class FunctionCall(ASTNode):
    name: str = ""
    args: List[Any] = None

    def __post_init__(self):
        if self.args is None:
            self.args = []


# ── Statements ────────────────────────────────────────────────────────────────

@dataclass
class VarDecl(ASTNode):
    name: str = ""
    value: Any = None

@dataclass
class Assignment(ASTNode):
    name: str = ""
    value: Any = None

@dataclass
class PrintStmt(ASTNode):
    expr: Any = None

@dataclass
class ReturnStmt(ASTNode):
    expr: Any = None

@dataclass
class IfStmt(ASTNode):
    condition: Any = None
    then_body: List[Any] = None
    else_body: Optional[List[Any]] = None

    def __post_init__(self):
        if self.then_body is None:
            self.then_body = []

@dataclass
class WhileStmt(ASTNode):
    condition: Any = None
    body: List[Any] = None

    def __post_init__(self):
        if self.body is None:
            self.body = []

@dataclass
class FuncDef(ASTNode):
    name: str = ""
    params: List[str] = None
    body: List[Any] = None

    def __post_init__(self):
        if self.params is None:
            self.params = []
        if self.body is None:
            self.body = []

@dataclass
class ModeStmt(ASTNode):
    mode: str = "deg"

@dataclass
class Program(ASTNode):
    statements: List[Any] = None

    def __post_init__(self):
        if self.statements is None:
            self.statements = []
