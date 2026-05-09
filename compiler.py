#!/usr/bin/env python3
"""
CalcScript Compiler/Interpreter
Usage:
  python compiler.py input.calc              # Run a program
  python compiler.py input.calc --debug      # Show tokens + AST + symbol table
  python compiler.py --interactive           # REPL mode
"""

import sys
import os
import argparse

# Make sure src/ is on the path when running from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from lexer import Lexer, LexerError
from parser import Parser, ParseError
from semantic import SemanticAnalyzer
from interpreter import Interpreter, RuntimeError_
from ast_printer import print_ast
from token_printer import format_tokens


BANNER = """\
╔══════════════════════════════════════╗
║   CalcScript v1.0  —  CalcScript     ║
║   A Programmable Calculator Language ║
╚══════════════════════════════════════╝
Type 'exit' or 'quit' to leave REPL.
Type 'mode deg' or 'mode rad' to switch angle mode.
"""


def compile_and_run(source: str, filename: str = "<stdin>",
                    debug: bool = False) -> bool:
    """
    Full pipeline: lex → parse → semantic check → interpret.
    Returns True on success, False on any error.
    """
    # ── Lexing ────────────────────────────────────────────────────────────────
    try:
        lexer = Lexer(source)
        tokens = lexer.tokenize()
    except LexerError as e:
        print(f"\n{e}", file=sys.stderr)
        return False

    if debug:
        print(format_tokens(tokens))
        print()

    # ── Parsing ───────────────────────────────────────────────────────────────
    try:
        parser = Parser(tokens)
        ast = parser.parse()
    except ParseError as e:
        print(f"\n{e}", file=sys.stderr)
        return False

    if debug:
        print("=== Abstract Syntax Tree ===")
        print(print_ast(ast))
        print()

    # ── Semantic Analysis ─────────────────────────────────────────────────────
    analyzer = SemanticAnalyzer()
    errors = analyzer.analyze(ast)
    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        return False

    # ── Interpretation ────────────────────────────────────────────────────────
    interp = Interpreter()
    try:
        interp.execute(ast)
    except RuntimeError_ as e:
        print(f"\n{e}", file=sys.stderr)
        return False

    if debug:
        print()
        print(interp.dump_symbol_table())

    return True


def run_repl():
    """Interactive REPL mode."""
    print(BANNER)
    interp = Interpreter()

    # Pre-warm the interpreter so global scope persists across inputs
    history = []

    while True:
        try:
            line = input("calc> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not line:
            continue
        if line.lower() in ('exit', 'quit'):
            print("Bye!")
            break
        if line.lower() == 'help':
            print_help()
            continue
        if line.lower() == 'clear':
            interp = Interpreter()
            history = []
            print("[Interpreter reset]")
            continue

        # Append to history and re-run everything so scope accumulates
        history.append(line)
        source = '\n'.join(history)

        try:
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            analyzer = SemanticAnalyzer()
            errors = analyzer.analyze(ast)
            if errors:
                for e in errors:
                    print(e)
                history.pop()   # revert bad line
                continue
            interp = Interpreter()
            interp.execute(ast)
        except (LexerError, ParseError, RuntimeError_) as e:
            print(e)
            history.pop()   # revert bad line


def print_help():
    print("""
CalcScript Quick Reference
──────────────────────────
Variables:    var x = 10
Arithmetic:   x + y  x - y  x * y  x / y  x ^ y  x mod y
Comparison:   ==  !=  <  <=  >  >=
Logic:        and  or  not
If/Else:      if x > 0 { print x } else { print -x }
While:        while x < 10 { x = x + 1 }
Functions:    func double(n) { return n * 2 }
Print:        print x
Builtins:     sin cos tan asin acos atan sqrt log abs
Angle mode:   deg   or   rad
Strings:      var s = "hello"
Comments:     # this is a comment
""")


def main():
    ap = argparse.ArgumentParser(
        prog='compiler',
        description='CalcScript — Programmable Calculator Language'
    )
    ap.add_argument('source', nargs='?', help='Source file (.calc)')
    ap.add_argument('-o', '--output', help='Output file (reserved for future use)')
    ap.add_argument('--debug', action='store_true',
                    help='Show tokens, AST, and symbol table')
    ap.add_argument('--interactive', action='store_true',
                    help='Launch REPL mode')

    args = ap.parse_args()

    if args.interactive:
        run_repl()
        return

    if not args.source:
        ap.print_help()
        sys.exit(1)

    if not os.path.isfile(args.source):
        print(f"Error: File not found: '{args.source}'", file=sys.stderr)
        sys.exit(1)

    ext = os.path.splitext(args.source)[1].lower()
    if ext != '.calc':
        print(f"Warning: Expected a .calc file, got '{ext}'", file=sys.stderr)

    with open(args.source, 'r', encoding='utf-8') as f:
        source = f.read()

    ok = compile_and_run(source, filename=args.source, debug=args.debug)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
