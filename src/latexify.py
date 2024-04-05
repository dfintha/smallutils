#! /usr/bin/env python3
"""Tool that converts Python expressions to a LaTeX formulae."""

import ast
import datetime
import os
import subprocess
import sys
import textwrap

# # latexify
#
# This tool converts Python expressions to LaTeX, and creates a PNG file using
# pdflatex and the standalone document class. Multiple expressions can be given,
# with all of them added to the same document/image.
#
# ## Requirements
#
# The tool uses pdflatex to compile the generated LaTeX code, ImageMagick to
# convert the resulting PDF file to PNG format, and Python (version 3.11) to
# parse the Python language.
#
# ## Language
#
# The Python language serves as the input, but some extra functionality is added
# to correctly denote mathematical expressions.
#
# ### Constants
#
# Numeric constants are simply put into the equation.
# String constants are put in a \text{...} tag.
#
# ### Variables
#
# Variable names starting with the name of a special symbol (greek letter,
# hebrew letters used in math, or infinity) are replaced with their LaTeX symbol
# counterparts. Variable names containing an underscore treat the part after
# the underscore as the subscript.
#
# ### Functions
#
# Function calls are simply converted, except for a few "built-in" functions.
# - integral(expression, [subscript], [superscript], [end])
#   This will translate to an integral with the given subscript and superscript.
#   The 'end' variable can be used to add 'dx' at the end of the function.
# - sum(expression, [subscript], [superscript], [end])
#   Similar to the integral, but with a sum sign.
# - product(expression, [subscript], [superscript], [end])
#   Similar to the integral, but with a product sign.
# - d(expression)
#   The derivative of an expression. If it is a function or a variable, a ' is
#   added to its name, otherwise it is enclosed in parentheses and a ' is added
#   to that.
# - abs(expression)
#   Absolute value lines are added to both sides.
# - floor(expression)
#   Lines denoting flooring (integer part) are added to both sides.
# - ceil(expression)
#   Lines denoting ceiling (integer part plus one) are added to both sides.
# - root(n, expression)
#   Expression is put under a denoted Nth root.
# - cbrt(expression)
#   An alias for root(3, expression).
# - sqrt(expression)
#   Expression is put under a simple root (without notation).
#
# ### Unary operators
#
# Unary operators are converted to their corresponding mathematical symbols as
# prefixes, except the bitwise inversion, which is noted with an overline.
#
# ### Binary operators, boolean operators, and comparisons
#
# These are also converted to their corresponding symbols as infixes. In this
# context, equality and non-equality is denoted as comparison.
# Notable exceptions are the power operator, which is denoted as a superscript,
# and division, which is denoted using fraction bars. Occurrences of the 'in'
# keyword are translated to set inclusion operators.
#
# ### Sets and tuples
#
# Sets are noted using curly braces on both sides, and tuples are simply
# comma-separated lists. The latter may be used to put more expressions in a
# single line, separated by commas.


def export_to_png(expressions: list, output: str) -> bool:
    """Exports a list of expressions to a single PNG file."""

    preferences = "preview, varwidth, border=0.25cm"
    skeleton = textwrap.dedent(
        """\
        \\documentclass[{}, convert={{outext=.png}}]{{standalone}}
        \\usepackage{{amsmath}}
        \\usepackage{{amssymb}}
        \\begin{{document}}
        {}
        \\end{{document}}
    """
    )

    content = ""
    for argument in expressions:
        content += latexify(argument) + "\n"
    document = skeleton.format(preferences, content).encode("utf-8")
    subprocess.run(
        ["pdflatex", "--shell-escape"],
        input=document,
        check=False,
        capture_output=True,
    )
    subprocess.run(
        ["pdflatex", "--shell-escape"],
        input=document,
        check=False,
        capture_output=True,
    )

    _attempt_remove(["texput.aux", "texput.log", "texput.pdf"])
    try:
        os.rename("texput.png", output)
    except FileNotFoundError:
        return False
    return True


def latexify(expression: str) -> str:
    """Create a LaTeX equation based on a Python expression."""
    module = ast.parse(expression)
    root = list(ast.iter_child_nodes(module))[0]
    return "$$" + _latexify_node(root) + "$$"


def _latexify_node(node: ast.AST) -> str:
    """Create a part of a LaTeX equation based on a node."""
    result = "?" + type(node).__name__ + "?"
    match type(node):
        case ast.Expr:
            result = _latexify_node(node.value)
        case ast.Constant:
            result = _latexify_constant(node)
        case ast.Name:
            result = _latexify_name(node)
        case ast.Call:
            result = _latexify_call(node)
        case ast.UnaryOp:
            result = _latexify_unop(node)
        case ast.BinOp:
            result = _latexify_binop(node)
        case ast.BoolOp:
            result = _latexify_boolop(node)
        case ast.Compare:
            result = _latexify_compare(node)
        case ast.Set:
            result = _latexify_set(node)
        case ast.Tuple:
            result = _latexify_tuple(node)
    return result


def _latexify_constant(node: ast.Constant) -> str:
    """Create a part of a LaTeX equation for constants."""
    result = "?" + type(node.value).__name__ + "?"
    if isinstance(node.value, str):
        result = "\\text{" + node.value + "}"
    if type(node.value) in (int, float):
        result = str(node.value).strip()
    return result


def _latexify_name(node: ast.Name) -> str:
    """Create a part of a LaTeX equation for variables."""
    result = node.id
    special = {
        "alpha": "\\alpha{}",
        "beta": "\\beta{}",
        "gamma": "\\gamma{}",
        "Gamma": "\\Gamma{}",
        "delta": "\\delta{}",
        "Delta": "\\Delta{}",
        "epsilon": "\\varepsilon{}",
        "zeta": "\\zeta{}",
        "eta": "\\eta{}",
        "theta": "\\theta{}",
        "Theta": "\\Theta{}",
        "iota": "\\iota{}",
        "kappa": "\\kappa{}",
        "lambda": "\\lambda{}",
        "Lambda": "\\Lambda{}",
        "mu": "\\mu{}",
        "nu": "\\nu{}",
        "xi": "\\xi{}",
        "Xi": "\\Xi{}",
        "pi": "\\pi{}",
        "Pi": "\\Pi{}",
        "rho": "\\rho{}",
        "sigma": "\\sigma{}",
        "Sigma": "\\Sigma{}",
        "tau": "\\tau{}",
        "upsilon": "\\upsilon{}",
        "Upsilon": "\\Upsilon{}",
        "phi": "\\phi{}",
        "Phi": "\\Phi{}",
        "chi": "\\chi{}",
        "psi": "\\psi{}",
        "Psi": "\\Psi{}",
        "omega": "\\omega{}",
        "Omega": "\\Omega{}",
        "aleph": "\\aleph{}",
        "beth": "\\beth{}",
        "gimel": "\\gimel{}",
        "daleth": "\\daleth{}",
        "infinity": "\\infty{}",
    }
    parts = result.split("_")
    if parts[0] in special:
        result = special[parts[0]]
        if len(parts) > 1:
            result += "_{" + parts[1] + "}"
    return result


def _latexify_call(node: ast.Call) -> str:
    """Create a part of a LaTeX equation for functions."""
    if node.func.id in ("integral", "sum", "product"):
        return _latexify_iterated(node)
    if node.func.id == "d":
        return _latexify_derive(node)
    if node.func.id in ("abs", "floor", "ceil"):
        return _latexify_parens(node)
    if node.func.id in ("root", "sqrt", "cbrt"):
        return _latexify_root(node)
    arguments = list(map(_latexify_node, node.args))
    return node.func.id + "(" + " , ".join(arguments) + ")"


def _latexify_iterated(node: ast.Call) -> str:
    """Create a part of a LaTeX equation for integrals."""
    result = ""
    match node.func.id:
        case "integral":
            result = "\\int"
        case "sum":
            result = "\\sum"
        case "product":
            result = "\\prod"
    under = _latexify_node(node.args[1]) if len(node.args) > 1 else None
    over = _latexify_node(node.args[2]) if len(node.args) > 2 else None
    variable = _latexify_node(node.args[3]) if len(node.args) > 3 else None
    if over is not None:
        result += "^{" + str(over).strip() + "}"
    if under is not None:
        result += "_{" + str(under).strip() + "}"
    result += "{" + _latexify_node(node.args[0])
    if variable is not None:
        result += "\\;{}" + str(variable).strip()
    result += "}"
    return result


def _latexify_derive(node: ast.Call) -> str:
    """Create a part of a LaTeX equation for derivatives."""
    argument = node.args[0]
    match type(argument):
        case ast.Call:
            argument.func.id += "'"
            return _latexify_node(argument)
        case ast.Name:
            return node.id + "'"
        case ast.Constant:
            return str(node.value) + "'"
    return "\\left({}" + _latexify_node(argument) + "\\right){}'"


def _latexify_parens(node: ast.Call) -> str:
    """Create a part of a LaTeX equation for "parentheses" calls."""
    left = ""
    right = ""
    match node.func.id:
        case "abs":
            left = "\\left|{}"
            right = "\\right|{}"
        case "floor":
            left = "\\lfloor{}"
            right = "\\rfloor{}"
        case "ceil":
            left = "\\lceil{}"
            right = "\\rceil{}"
    return left + _latexify_node(node.args[0]) + right


def _latexify_root(node: ast.Call) -> str:
    """Create a part of a LaTeX equation for roots."""
    match node.func.id:
        case "root":
            count = _latexify_node(node.args[0])
        case "cbrt":
            count = "3"
        case "sqrt":
            count = ""
    return "\\sqrt[" + count + "]{" + _latexify_node(node.args[-1]) + "}"


def _latexify_unop(node: ast.UnaryOp) -> str:
    """Create a part of a LaTeX equation for unary operators."""
    match type(node.op):
        case ast.UAdd:
            operator = "+"
        case ast.USub:
            operator = "-"
        case ast.Not:
            operator = "\\neg{}"
        case ast.Invert:
            return "\\overline{" + node.operand.id + "}"
    return operator + _latexify_node(node.operand)


def _latexify_binop(node: ast.BinOp) -> str:
    """Create a part of a LaTeX equation for binary operators."""
    result = "??" + type(node.op).__name__ + "??"
    match type(node.op):
        case ast.Add:
            result = (
                _latexify_node(node.left) + " + " + _latexify_node(node.right)
            )
        case ast.Sub:
            result = (
                _latexify_node(node.left) + " - " + _latexify_node(node.right)
            )
        case ast.Mult:
            result = (
                _latexify_node(node.left)
                + "\\cdot{}"
                + _latexify_node(node.right)
            )
        case ast.Div:
            result = (
                "\\dfrac{"
                + _latexify_node(node.left)
                + "}{"
                + _latexify_node(node.right)
                + "}"
            )
        case ast.FloorDiv:
            result = (
                "\\dfrac{"
                + _latexify_node(node.left)
                + "}{"
                + _latexify_node(node.right)
                + "}"
            )
        case ast.Mod:
            result = (
                _latexify_node(node.left)
                + "\\text{{ mod }}"
                + _latexify_node(node.right)
            )
        case ast.Pow:
            result = (
                _latexify_node(node.left)
                + "^{"
                + _latexify_node(node.right)
                + "}"
            )
        case ast.LShift:
            result = (
                _latexify_node(node.left)
                + "\\lll{}"
                + _latexify_node(node.right)
            )
        case ast.RShift:
            result = (
                _latexify_node(node.left)
                + "\\ggg{}"
                + _latexify_node(node.right)
            )
        case ast.BitOr:
            result = (
                _latexify_node(node.left)
                + "\\lor{}"
                + _latexify_node(node.right)
            )
        case ast.BitXor:
            result = (
                _latexify_node(node.left)
                + "\\oplus{}"
                + _latexify_node(node.right)
            )
        case ast.BitAnd:
            result = (
                _latexify_node(node.left)
                + "\\land{}"
                + _latexify_node(node.right)
            )
        case ast.MatMult:
            result = (
                _latexify_node(node.left)
                + " \\cdot{}"
                + _latexify_node(node.right)
            )
    return result


def _latexify_boolop(node: ast.BoolOp) -> str:
    """Create a part of a LaTeX equation for boolean operators."""
    match type(node.op):
        case ast.And:
            return (
                _latexify_node(node.left)
                + "\\land{}"
                + _latexify_node(node.right)
            )
        case ast.Or:
            return (
                _latexify_node(node.left)
                + "\\lor{}"
                + _latexify_node(node.right)
            )


def _latexify_compare(node: ast.Compare) -> str:
    """Create a part of a LaTeX equation for unary operators."""
    result = _latexify_node(node.left)
    # The length-based enumeration is used to index two separate lists.
    # pylint: disable-next=C0200
    for i in range(len(node.ops)):
        match type(node.ops[i]):
            case ast.Eq:
                operator = "="
            case ast.NotEq:
                operator = "\\neq{}"
            case ast.Lt:
                operator = "<"
            case ast.LtE:
                operator = "\\leqslant{}"
            case ast.Gt:
                operator = ">"
            case ast.GtE:
                operator = "\\geqslant{}"
            case ast.Is:
                operator = "="
            case ast.IsNot:
                operator = "\\neq{}"
            case ast.In:
                operator = "\\in{}"
            case ast.NotIn:
                operator = "\\notin{}"
        result += operator + _latexify_node(node.comparators[i])
    return result


def _latexify_set(node: ast.Set) -> str:
    """Create a part of a LaTeX equation for sets."""
    elements = ",".join(map(_latexify_node, node.elts))
    return "\\left\\{" + elements + "\\right\\}"


def _latexify_tuple(node: ast.Tuple) -> str:
    """Create a part of a LaTeX equation for comma-separated expressions."""
    elements = ",\\;{}".join(map(_latexify_node, node.elts))
    return elements


def _latexify_main():
    """Entry point of the program."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    export_to_png(list(sys.argv[1:]), f"latexify-{timestamp}.png")


def _attempt_remove(paths: list) -> None:
    """Attempts to remove a file if it exists."""
    for path in paths:
        try:
            os.remove(path)
        except FileNotFoundError:
            continue


if __name__ == "__main__":
    _latexify_main()
