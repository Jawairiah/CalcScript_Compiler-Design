# CalcScript — Programmable Calculator Language

**CS4031 Compiler Construction · Spring 2026**  
Team: Nehdia Shah · Jawairia Hammad · Abeera Amir

---

## What is CalcScript?

CalcScript is a high-level interpreted language with a clean, calculator-style syntax.
It supports variables, arithmetic, trig/math functions, conditionals, loops, and
user-defined functions — processed through a full custom compiler pipeline.

---

## Project Structure

```
calcscript/
├── compiler.py          ← Main entry point (run this)
├── src/
│   ├── lexer.py         ← Tokenizer / Lexical Analysis
│   ├── parser.py        ← Recursive-descent Parser → AST
│   ├── ast_nodes.py     ← AST node dataclasses
│   ├── semantic.py      ← Semantic Analyzer + Symbol Table
│   ├── interpreter.py   ← Tree-walk Interpreter
│   ├── ast_printer.py   ← Debug: AST pretty-printer
│   └── token_printer.py ← Debug: Token list formatter
└── examples/
    ├── circle.calc      ← Circle area/perimeter (from proposal)
    ├── sequences.calc   ← Factorial & Fibonacci
    └── scientific.calc  ← Trig, sqrt, log, quadratic formula
```

---

## Requirements

- **Python 3.8 or higher** (uses dataclasses and f-strings)
- No external packages required — pure standard library

Check your Python version:
```bash
python --version
# or
python3 --version
```

---

## Step-by-Step: How to Run

### Step 1 — Download / Clone the project

Place the `calcscript/` folder anywhere on your machine.

---

### Step 2 — Open a terminal

- **Windows**: Press `Win+R`, type `cmd`, press Enter  
- **macOS/Linux**: Open Terminal

Navigate to the project folder:
```bash
cd path/to/calcscript
```

---

### Step 3 — Run a source file

```bash
python compiler.py examples/circle.calc
```

Expected output:
```
153
43
0
1
Large circle
```

Run the other examples:
```bash
python compiler.py examples/sequences.calc
python compiler.py examples/scientific.calc
```

---

### Step 4 — Debug mode (shows tokens + AST + symbol table)

```bash
python compiler.py examples/circle.calc --debug
```

This will print:
1. **Token list** — every token with its line/column number
2. **Abstract Syntax Tree** — hierarchical structure of the program
3. **Symbol Table** — all variables and functions after execution

---

### Step 5 — Interactive REPL mode

```bash
python compiler.py --interactive
```

You'll see a prompt:
```
╔══════════════════════════════════════╗
║   CalcScript v1.0  —  CalcScript     ║
║   A Programmable Calculator Language ║
╚══════════════════════════════════════╝
calc>
```

Try typing:
```
calc> var x = 10
calc> var y = 20
calc> print x + y
30
calc> func square(n) { return n ^ 2 }
calc> print square(7)
49
calc> deg
calc> print sin(45)
0.7071067811865476
calc> exit
```

REPL commands:
| Command  | Effect                          |
|----------|---------------------------------|
| `exit`   | Quit the REPL                   |
| `quit`   | Quit the REPL                   |
| `clear`  | Reset interpreter state         |
| `help`   | Show language quick reference   |

---

### Step 6 — Write your own .calc program

Create a file `myprogram.calc`:
```
# My first CalcScript program
var radius = 5
var pi = 3.14159

func area(r) {
    return pi * r ^ 2
}

print area(radius)
```

Run it:
```bash
python compiler.py myprogram.calc
```

---

## Language Reference

### Variables
```
var x = 42
var name = "hello"
var flag = true
```

### Arithmetic
```
x + y    # addition
x - y    # subtraction
x * y    # multiplication
x / y    # division
x ^ y    # exponentiation (right-associative)
x mod y  # modulo
```

### Comparison & Logic
```
x == y   x != y
x < y    x <= y
x > y    x >= y
x and y  x or y  not x
```

### Control Flow
```
if x > 0 {
    print "positive"
} else {
    print "non-positive"
}

while x < 10 {
    x = x + 1
}
```

### Functions
```
func add(a, b) {
    return a + b
}

var result = add(3, 4)
print result
```

### Built-in Functions
| Function   | Description                        |
|------------|------------------------------------|
| `sin(x)`   | Sine                               |
| `cos(x)`   | Cosine                             |
| `tan(x)`   | Tangent                            |
| `asin(x)`  | Inverse sine                       |
| `acos(x)`  | Inverse cosine                     |
| `atan(x)`  | Inverse tangent                    |
| `sqrt(x)`  | Square root                        |
| `log(x)`   | Base-10 logarithm                  |
| `abs(x)`   | Absolute value                     |

### Angle Mode
```
deg    # switch to degrees (default)
rad    # switch to radians
```

### Comments
```
# This is a comment
var x = 10  # inline comment
```

---

## Error Messages

CalcScript gives precise error messages with line and column numbers:

| Error Type       | Example Message                                    |
|------------------|----------------------------------------------------|
| Lexer error      | `[Line 3, Col 7] LexerError: Unexpected character` |
| Parse error      | `[Line 5, Col 1] ParseError: Expected '}'`         |
| Semantic error   | `[Line 8, Col 5] SemanticError: Undefined variable 'x'` |
| Runtime error    | `[Line 12, Col 3] RuntimeError: Division by zero`  |

---

## Compiler Pipeline

```
Source (.calc)
     │
     ▼
 [Lexer]  → Token stream
     │
     ▼
 [Parser] → Abstract Syntax Tree (AST)
     │
     ▼
 [Semantic Analyzer] → Symbol Table + Error checks
     │
     ▼
 [Interpreter] → Output / Results
```

