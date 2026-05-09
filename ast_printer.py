"""
CalcScript AST Printer
Pretty-prints the AST for --debug mode.
"""

from ast_nodes import *


def print_ast(node: ASTNode, indent: int = 0) -> str:
    pad = "  " * indent
    lines = []

    if isinstance(node, Program):
        lines.append(f"{pad}Program")
        for stmt in node.statements:
            lines.append(print_ast(stmt, indent + 1))

    elif isinstance(node, NumberLiteral):
        lines.append(f"{pad}Number({node.value})")

    elif isinstance(node, StringLiteral):
        lines.append(f'{pad}String("{node.value}")')

    elif isinstance(node, BoolLiteral):
        lines.append(f"{pad}Bool({'true' if node.value else 'false'})")

    elif isinstance(node, Identifier):
        lines.append(f"{pad}Var({node.name})")

    elif isinstance(node, BinaryOp):
        lines.append(f"{pad}BinaryOp({node.op})")
        lines.append(print_ast(node.left,  indent + 1))
        lines.append(print_ast(node.right, indent + 1))

    elif isinstance(node, UnaryOp):
        lines.append(f"{pad}UnaryOp({node.op})")
        lines.append(print_ast(node.operand, indent + 1))

    elif isinstance(node, BuiltinCall):
        lines.append(f"{pad}Builtin({node.name})")
        lines.append(print_ast(node.arg, indent + 1))

    elif isinstance(node, FunctionCall):
        lines.append(f"{pad}Call({node.name})")
        for arg in node.args:
            lines.append(print_ast(arg, indent + 1))

    elif isinstance(node, VarDecl):
        lines.append(f"{pad}VarDecl({node.name})")
        lines.append(print_ast(node.value, indent + 1))

    elif isinstance(node, Assignment):
        lines.append(f"{pad}Assign({node.name})")
        lines.append(print_ast(node.value, indent + 1))

    elif isinstance(node, PrintStmt):
        lines.append(f"{pad}Print")
        lines.append(print_ast(node.expr, indent + 1))

    elif isinstance(node, ReturnStmt):
        lines.append(f"{pad}Return")
        lines.append(print_ast(node.expr, indent + 1))

    elif isinstance(node, IfStmt):
        lines.append(f"{pad}If")
        lines.append(f"{pad}  [condition]")
        lines.append(print_ast(node.condition, indent + 2))
        lines.append(f"{pad}  [then]")
        for s in node.then_body:
            lines.append(print_ast(s, indent + 2))
        if node.else_body:
            lines.append(f"{pad}  [else]")
            for s in node.else_body:
                lines.append(print_ast(s, indent + 2))

    elif isinstance(node, WhileStmt):
        lines.append(f"{pad}While")
        lines.append(f"{pad}  [condition]")
        lines.append(print_ast(node.condition, indent + 2))
        lines.append(f"{pad}  [body]")
        for s in node.body:
            lines.append(print_ast(s, indent + 2))

    elif isinstance(node, FuncDef):
        params = ', '.join(node.params) if node.params else 'none'
        lines.append(f"{pad}FuncDef({node.name}, params=[{params}])")
        for s in node.body:
            lines.append(print_ast(s, indent + 1))

    elif isinstance(node, ModeStmt):
        lines.append(f"{pad}ModeSet({node.mode})")

    else:
        lines.append(f"{pad}<Unknown: {type(node).__name__}>")

    return '\n'.join(lines)
