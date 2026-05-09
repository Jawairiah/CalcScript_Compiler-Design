"""
CalcScript Lexer
Tokenizes .calc source files into a stream of tokens.
"""

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional


class TokenType(Enum):
    # Literals
    NUMBER      = auto()
    STRING      = auto()
    BOOL        = auto()

    # Identifiers & keywords
    IDENTIFIER  = auto()
    VAR         = auto()
    FUNC        = auto()
    RETURN      = auto()
    IF          = auto()
    ELSE        = auto()
    WHILE       = auto()
    PRINT       = auto()
    DEG         = auto()
    RAD         = auto()

    # Built-in math functions
    SIN         = auto()
    COS         = auto()
    TAN         = auto()
    ASIN        = auto()
    ACOS        = auto()
    ATAN        = auto()
    SQRT        = auto()
    LOG         = auto()
    ABS         = auto()

    # Operators
    PLUS        = auto()
    MINUS       = auto()
    STAR        = auto()
    SLASH       = auto()
    CARET       = auto()
    MOD         = auto()
    EQ          = auto()   # =
    EQEQ        = auto()   # ==
    NEQ         = auto()   # !=
    LT          = auto()
    LE          = auto()
    GT          = auto()
    GE          = auto()
    AND         = auto()
    OR          = auto()
    NOT         = auto()

    # Delimiters
    LPAREN      = auto()
    RPAREN      = auto()
    LBRACE      = auto()
    RBRACE      = auto()
    COMMA       = auto()
    NEWLINE     = auto()

    # Special
    EOF         = auto()


KEYWORDS = {
    'var':    TokenType.VAR,
    'func':   TokenType.FUNC,
    'return': TokenType.RETURN,
    'if':     TokenType.IF,
    'else':   TokenType.ELSE,
    'while':  TokenType.WHILE,
    'print':  TokenType.PRINT,
    'deg':    TokenType.DEG,
    'rad':    TokenType.RAD,
    'true':   TokenType.BOOL,
    'false':  TokenType.BOOL,
    'sin':    TokenType.SIN,
    'cos':    TokenType.COS,
    'tan':    TokenType.TAN,
    'asin':   TokenType.ASIN,
    'acos':   TokenType.ACOS,
    'atan':   TokenType.ATAN,
    'sqrt':   TokenType.SQRT,
    'log':    TokenType.LOG,
    'abs':    TokenType.ABS,
    'and':    TokenType.AND,
    'or':     TokenType.OR,
    'not':    TokenType.NOT,
    'mod':    TokenType.MOD,
}


@dataclass
class Token:
    type: TokenType
    value: object
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.col})"


class LexerError(Exception):
    def __init__(self, message: str, line: int, col: int):
        super().__init__(f"[Line {line}, Col {col}] LexerError: {message}")
        self.line = line
        self.col = col


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []

    def error(self, msg):
        raise LexerError(msg, self.line, self.col)

    def peek(self, offset=0) -> Optional[str]:
        idx = self.pos + offset
        return self.source[idx] if idx < len(self.source) else None

    def advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def match(self, expected: str) -> bool:
        if self.peek() == expected:
            self.advance()
            return True
        return False

    def skip_whitespace_and_comments(self):
        while self.pos < len(self.source):
            ch = self.peek()
            if ch in (' ', '\t', '\r'):
                self.advance()
            elif ch == '#':          # line comment
                while self.peek() and self.peek() != '\n':
                    self.advance()
            else:
                break

    def read_number(self) -> Token:
        start_line, start_col = self.line, self.col
        num_str = ''
        has_dot = False
        while self.peek() and (self.peek().isdigit() or self.peek() == '.'):
            ch = self.peek()
            if ch == '.':
                if has_dot:
                    break
                has_dot = True
            num_str += self.advance()
        value = float(num_str) if has_dot else int(num_str)
        return Token(TokenType.NUMBER, value, start_line, start_col)

    def read_string(self) -> Token:
        start_line, start_col = self.line, self.col
        self.advance()  # consume opening "
        s = ''
        while self.peek() and self.peek() != '"':
            if self.peek() == '\n':
                self.error("Unterminated string literal")
            s += self.advance()
        if not self.peek():
            self.error("Unterminated string literal")
        self.advance()  # consume closing "
        return Token(TokenType.STRING, s, start_line, start_col)

    def read_identifier_or_keyword(self) -> Token:
        start_line, start_col = self.line, self.col
        ident = ''
        while self.peek() and (self.peek().isalnum() or self.peek() == '_'):
            ident += self.advance()
        ttype = KEYWORDS.get(ident, TokenType.IDENTIFIER)
        value = ident
        if ttype == TokenType.BOOL:
            value = (ident == 'true')
        return Token(ttype, value, start_line, start_col)

    def tokenize(self) -> List[Token]:
        while self.pos < len(self.source):
            self.skip_whitespace_and_comments()
            if self.pos >= len(self.source):
                break

            start_line, start_col = self.line, self.col
            ch = self.peek()

            if ch == '\n':
                self.advance()
                # Collapse multiple blank lines into one NEWLINE token
                if not self.tokens or self.tokens[-1].type != TokenType.NEWLINE:
                    self.tokens.append(Token(TokenType.NEWLINE, '\n', start_line, start_col))
                continue

            if ch.isdigit() or (ch == '.' and self.peek(1) and self.peek(1).isdigit()):
                self.tokens.append(self.read_number())
                continue

            if ch == '"':
                self.tokens.append(self.read_string())
                continue

            if ch.isalpha() or ch == '_':
                self.tokens.append(self.read_identifier_or_keyword())
                continue

            # Single/double char operators
            self.advance()
            if ch == '+':
                self.tokens.append(Token(TokenType.PLUS,   '+', start_line, start_col))
            elif ch == '-':
                self.tokens.append(Token(TokenType.MINUS,  '-', start_line, start_col))
            elif ch == '*':
                self.tokens.append(Token(TokenType.STAR,   '*', start_line, start_col))
            elif ch == '/':
                self.tokens.append(Token(TokenType.SLASH,  '/', start_line, start_col))
            elif ch == '^':
                self.tokens.append(Token(TokenType.CARET,  '^', start_line, start_col))
            elif ch == '%':
                self.tokens.append(Token(TokenType.MOD,    '%', start_line, start_col))
            elif ch == '(':
                self.tokens.append(Token(TokenType.LPAREN, '(', start_line, start_col))
            elif ch == ')':
                self.tokens.append(Token(TokenType.RPAREN, ')', start_line, start_col))
            elif ch == '{':
                self.tokens.append(Token(TokenType.LBRACE, '{', start_line, start_col))
            elif ch == '}':
                self.tokens.append(Token(TokenType.RBRACE, '}', start_line, start_col))
            elif ch == ',':
                self.tokens.append(Token(TokenType.COMMA,  ',', start_line, start_col))
            elif ch == '=':
                if self.match('='):
                    self.tokens.append(Token(TokenType.EQEQ, '==', start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.EQ,   '=',  start_line, start_col))
            elif ch == '!':
                if self.match('='):
                    self.tokens.append(Token(TokenType.NEQ,  '!=', start_line, start_col))
                else:
                    self.error(f"Unexpected character '!'")
            elif ch == '<':
                if self.match('='):
                    self.tokens.append(Token(TokenType.LE,   '<=', start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.LT,   '<',  start_line, start_col))
            elif ch == '>':
                if self.match('='):
                    self.tokens.append(Token(TokenType.GE,   '>=', start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.GT,   '>',  start_line, start_col))
            else:
                self.error(f"Unexpected character '{ch}'")

        self.tokens.append(Token(TokenType.EOF, None, self.line, self.col))
        return self.tokens
