"""
CalcScript Parser
Builds an AST from the token stream produced by the Lexer.

Grammar (simplified):
  program     → statement* EOF
  statement   → varDecl | funcDef | ifStmt | whileStmt
              | printStmt | returnStmt | modeStmt
              | assignment | exprStmt
  ...
"""

from typing import List, Optional
from lexer import Token, TokenType
from ast_nodes import *


class ParseError(Exception):
    def __init__(self, message: str, line: int, col: int):
        super().__init__(f"[Line {line}, Col {col}] ParseError: {message}")
        self.line = line
        self.col = col


BUILTIN_FUNCS = {
    TokenType.SIN, TokenType.COS, TokenType.TAN,
    TokenType.ASIN, TokenType.ACOS, TokenType.ATAN,
    TokenType.SQRT, TokenType.LOG, TokenType.ABS,
}


class Parser:
    def __init__(self, tokens: List[Token]):
        # Strip leading/trailing newlines for cleanliness
        self.tokens = [t for t in tokens if t.type != TokenType.NEWLINE or
                       self._keep_newline(tokens, tokens.index(t))]
        # Rebuild without decorator logic – keep all tokens, handle NL in grammar
        self.tokens = tokens
        self.pos = 0

    def _keep_newline(self, tokens, idx):
        return True  # Keep all; we'll skip them contextually

    # ── Navigation ───────────────────────────────────────────────────────────

    def peek(self, offset=0) -> Token:
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else self.tokens[-1]

    def advance(self) -> Token:
        t = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return t

    def check(self, *types) -> bool:
        return self.peek().type in types

    def match(self, *types) -> Optional[Token]:
        if self.check(*types):
            return self.advance()
        return None

    def expect(self, ttype: TokenType, msg: str = None) -> Token:
        if self.check(ttype):
            return self.advance()
        t = self.peek()
        raise ParseError(
            msg or f"Expected {ttype.name}, got '{t.value}' ({t.type.name})",
            t.line, t.col
        )

    def skip_newlines(self):
        while self.check(TokenType.NEWLINE):
            self.advance()

    def at_end(self) -> bool:
        return self.peek().type == TokenType.EOF

    # ── Entry ─────────────────────────────────────────────────────────────────

    def parse(self) -> Program:
        stmts = []
        self.skip_newlines()
        while not self.at_end():
            stmts.append(self.parse_statement())
            self.skip_newlines()
        return Program(statements=stmts, line=1, col=1)

    # ── Statements ────────────────────────────────────────────────────────────

    def parse_statement(self) -> ASTNode:
        t = self.peek()

        if t.type == TokenType.VAR:
            return self.parse_var_decl()
        if t.type == TokenType.FUNC:
            return self.parse_func_def()
        if t.type == TokenType.IF:
            return self.parse_if()
        if t.type == TokenType.WHILE:
            return self.parse_while()
        if t.type == TokenType.PRINT:
            return self.parse_print()
        if t.type == TokenType.RETURN:
            return self.parse_return()
        if t.type in (TokenType.DEG, TokenType.RAD):
            return self.parse_mode()
        if t.type == TokenType.IDENTIFIER:
            # Look ahead: assignment or expression statement
            if self.peek(1).type == TokenType.EQ:
                return self.parse_assignment()
        return self.parse_expr_stmt()

    def parse_var_decl(self) -> VarDecl:
        t = self.expect(TokenType.VAR)
        name_tok = self.expect(TokenType.IDENTIFIER, "Expected variable name after 'var'")
        self.expect(TokenType.EQ, f"Expected '=' after variable name '{name_tok.value}'")
        value = self.parse_expr()
        self.expect_newline_or_eof()
        return VarDecl(name=name_tok.value, value=value, line=t.line, col=t.col)

    def parse_assignment(self) -> Assignment:
        name_tok = self.expect(TokenType.IDENTIFIER)
        t = self.expect(TokenType.EQ)
        value = self.parse_expr()
        self.expect_newline_or_eof()
        return Assignment(name=name_tok.value, value=value, line=name_tok.line, col=name_tok.col)

    def parse_func_def(self) -> FuncDef:
        t = self.expect(TokenType.FUNC)
        name_tok = self.expect(TokenType.IDENTIFIER, "Expected function name after 'func'")
        self.expect(TokenType.LPAREN, "Expected '(' after function name")
        params = []
        if not self.check(TokenType.RPAREN):
            params.append(self.expect(TokenType.IDENTIFIER, "Expected parameter name").value)
            while self.match(TokenType.COMMA):
                params.append(self.expect(TokenType.IDENTIFIER, "Expected parameter name").value)
        self.expect(TokenType.RPAREN, "Expected ')' after parameters")
        self.skip_newlines()
        self.expect(TokenType.LBRACE, "Expected '{' before function body")
        body = self.parse_block()
        return FuncDef(name=name_tok.value, params=params, body=body, line=t.line, col=t.col)

    def parse_block(self) -> List[ASTNode]:
        stmts = []
        self.skip_newlines()
        while not self.check(TokenType.RBRACE) and not self.at_end():
            stmts.append(self.parse_statement())
            self.skip_newlines()
        self.expect(TokenType.RBRACE, "Expected '}' to close block")
        return stmts

    def parse_if(self) -> IfStmt:
        t = self.expect(TokenType.IF)
        condition = self.parse_expr()
        self.skip_newlines()
        self.expect(TokenType.LBRACE, "Expected '{' after if condition")
        then_body = self.parse_block()
        else_body = None
        self.skip_newlines()
        if self.match(TokenType.ELSE):
            self.skip_newlines()
            self.expect(TokenType.LBRACE, "Expected '{' after 'else'")
            else_body = self.parse_block()
        return IfStmt(condition=condition, then_body=then_body, else_body=else_body,
                      line=t.line, col=t.col)

    def parse_while(self) -> WhileStmt:
        t = self.expect(TokenType.WHILE)
        condition = self.parse_expr()
        self.skip_newlines()
        self.expect(TokenType.LBRACE, "Expected '{' after while condition")
        body = self.parse_block()
        return WhileStmt(condition=condition, body=body, line=t.line, col=t.col)

    def parse_print(self) -> PrintStmt:
        t = self.expect(TokenType.PRINT)
        expr = self.parse_expr()
        self.expect_newline_or_eof()
        return PrintStmt(expr=expr, line=t.line, col=t.col)

    def parse_return(self) -> ReturnStmt:
        t = self.expect(TokenType.RETURN)
        expr = self.parse_expr()
        self.expect_newline_or_eof()
        return ReturnStmt(expr=expr, line=t.line, col=t.col)

    def parse_mode(self) -> ModeStmt:
        t = self.advance()
        self.expect_newline_or_eof()
        return ModeStmt(mode=t.value, line=t.line, col=t.col)

    def parse_expr_stmt(self):
        # Bare expression – evaluate and discard (used in REPL for auto-print)
        expr = self.parse_expr()
        self.expect_newline_or_eof()
        return PrintStmt(expr=expr, line=expr.line, col=expr.col)

    def expect_newline_or_eof(self):
        if self.check(TokenType.NEWLINE) or self.at_end() or self.check(TokenType.RBRACE):
            self.match(TokenType.NEWLINE)
        else:
            t = self.peek()
            raise ParseError(
                f"Expected newline after statement, got '{t.value}'",
                t.line, t.col
            )

    # ── Expressions (Pratt-style precedence) ─────────────────────────────────

    def parse_expr(self) -> ASTNode:
        return self.parse_or()

    def parse_or(self) -> ASTNode:
        left = self.parse_and()
        while self.check(TokenType.OR):
            op_tok = self.advance()
            right = self.parse_and()
            left = BinaryOp(op='or', left=left, right=right,
                            line=op_tok.line, col=op_tok.col)
        return left

    def parse_and(self) -> ASTNode:
        left = self.parse_not()
        while self.check(TokenType.AND):
            op_tok = self.advance()
            right = self.parse_not()
            left = BinaryOp(op='and', left=left, right=right,
                            line=op_tok.line, col=op_tok.col)
        return left

    def parse_not(self) -> ASTNode:
        if self.check(TokenType.NOT):
            op_tok = self.advance()
            operand = self.parse_not()
            return UnaryOp(op='not', operand=operand, line=op_tok.line, col=op_tok.col)
        return self.parse_comparison()

    def parse_comparison(self) -> ASTNode:
        left = self.parse_addition()
        CMP = {TokenType.EQEQ:'==', TokenType.NEQ:'!=',
               TokenType.LT:'<',   TokenType.LE:'<=',
               TokenType.GT:'>',   TokenType.GE:'>='}
        while self.peek().type in CMP:
            op_tok = self.advance()
            right = self.parse_addition()
            left = BinaryOp(op=CMP[op_tok.type], left=left, right=right,
                            line=op_tok.line, col=op_tok.col)
        return left

    def parse_addition(self) -> ASTNode:
        left = self.parse_multiplication()
        while self.check(TokenType.PLUS, TokenType.MINUS):
            op_tok = self.advance()
            right = self.parse_multiplication()
            left = BinaryOp(op=op_tok.value, left=left, right=right,
                            line=op_tok.line, col=op_tok.col)
        return left

    def parse_multiplication(self) -> ASTNode:
        left = self.parse_unary()
        while self.check(TokenType.STAR, TokenType.SLASH, TokenType.MOD):
            op_tok = self.advance()
            op = 'mod' if op_tok.type == TokenType.MOD else op_tok.value
            right = self.parse_unary()
            left = BinaryOp(op=op, left=left, right=right,
                            line=op_tok.line, col=op_tok.col)
        return left

    def parse_unary(self) -> ASTNode:
        if self.check(TokenType.MINUS):
            op_tok = self.advance()
            operand = self.parse_power()
            return UnaryOp(op='-', operand=operand, line=op_tok.line, col=op_tok.col)
        return self.parse_power()

    def parse_power(self) -> ASTNode:
        base = self.parse_primary()
        if self.check(TokenType.CARET):
            op_tok = self.advance()
            exp = self.parse_unary()   # right-associative
            return BinaryOp(op='^', left=base, right=exp,
                            line=op_tok.line, col=op_tok.col)
        return base

    def parse_primary(self) -> ASTNode:
        t = self.peek()

        # Number literal
        if t.type == TokenType.NUMBER:
            self.advance()
            return NumberLiteral(value=t.value, line=t.line, col=t.col)

        # String literal
        if t.type == TokenType.STRING:
            self.advance()
            return StringLiteral(value=t.value, line=t.line, col=t.col)

        # Bool literal
        if t.type == TokenType.BOOL:
            self.advance()
            return BoolLiteral(value=t.value, line=t.line, col=t.col)

        # Built-in math function call
        if t.type in BUILTIN_FUNCS:
            self.advance()
            self.expect(TokenType.LPAREN, f"Expected '(' after built-in '{t.value}'")
            arg = self.parse_expr()
            self.expect(TokenType.RPAREN, f"Expected ')' to close '{t.value}' call")
            return BuiltinCall(name=t.value, arg=arg, line=t.line, col=t.col)

        # User-defined function call or variable
        if t.type == TokenType.IDENTIFIER:
            self.advance()
            if self.check(TokenType.LPAREN):
                self.advance()
                args = []
                if not self.check(TokenType.RPAREN):
                    args.append(self.parse_expr())
                    while self.match(TokenType.COMMA):
                        args.append(self.parse_expr())
                self.expect(TokenType.RPAREN, "Expected ')' to close function call")
                return FunctionCall(name=t.value, args=args, line=t.line, col=t.col)
            return Identifier(name=t.value, line=t.line, col=t.col)

        # Grouped expression
        if t.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expr()
            self.expect(TokenType.RPAREN, "Expected ')' to close expression")
            return expr

        raise ParseError(
            f"Unexpected token '{t.value}' ({t.type.name}) in expression",
            t.line, t.col
        )
