"""
CalcScript Token Printer
Formats the token list for --debug output.
"""

from lexer import Token, TokenType


def format_tokens(tokens) -> str:
    lines = ["=== Tokens ==="]
    lines.append(f"{'LINE':>5}  {'COL':>4}  {'TYPE':<18}  VALUE")
    lines.append("-" * 50)
    for tok in tokens:
        if tok.type == TokenType.EOF:
            break
        if tok.type == TokenType.NEWLINE:
            continue
        val = repr(tok.value) if isinstance(tok.value, str) else str(tok.value)
        lines.append(f"{tok.line:>5}  {tok.col:>4}  {tok.type.name:<18}  {val}")
    return '\n'.join(lines)
