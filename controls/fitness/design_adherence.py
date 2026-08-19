#!/usr/bin/env python3
"""Fitness control: app source refers to Classical tokens, not hardcoded design values.

governance: enforces DEC-1

Fails on a raw hex colour literal, or a `font-family` (or `font` shorthand) naming a
family outside Cormorant Garamond / Lora, anywhere under app/src/**/*.{ts,tsx,css}.
The two token files (app/src/classical.css, app/src/tokens-local.css) are exempt by
exact path — they are where those literals are supposed to live. See DEC-1.

Deliberately does not check raw `px`: Classical's own styles.css is full of it, and a
rule that fires on the design system's own source is the most damaging failure mode
available here. Recorded as understood and declined, not overlooked.

CSS is parsed with tinycss2 (the tokenizer under WeasyPrint) rather than scanned with
a hand-rolled brace counter. Two earlier rounds of brace-counting each produced a
different class of grammar bug — a quoted `}` desyncing depth, an `@media`-nested
selector misread as a declaration — because a depth counter has no idea what a string
literal or an at-rule prelude is. A real CSS parser does, by construction, so those
failure classes are closed rather than patched. See DEC-1's governance history for
the two prior rounds this replaced.

The remaining assumption, stated plainly rather than discovered by a fourth round:
CSS this control cannot parse is treated as a **failure**, never a pass. tinycss2
itself does not surface "a block was never closed before EOF" as an error — the CSS
Syntax spec calls that a parse error but does not require reporting one, and
tinycss2 follows the spec's silent recovery rather than the spec's diagnostic. A
malformed file therefore gets a dedicated, narrowly-scoped well-formedness check
(`_first_unbalanced_bracket_line`) ahead of the real scan, on top of surfacing any
`tinycss2.ast.ParseError` the parser does produce on its own. Neither check makes
any judgement about what a brace *means* (selector vs. declaration) — the mistake
that broke rounds 1 and 2 — only whether the file's brackets and quotes resolve at
all. If a file fails either check, the control refuses to answer for that file
rather than reporting a partial scan of an ambiguous document.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import tinycss2
from tinycss2 import ast as css_ast

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / 'app' / 'src'
SCAN_SUFFIXES = frozenset({'.ts', '.tsx', '.css'})
CSS_SUFFIXES = frozenset({'.css'})
EXEMPT_PATHS = frozenset(
    {
        SRC_DIR / 'classical.css',
        SRC_DIR / 'tokens-local.css',
    }
)

ALLOWED_FONT_FAMILIES = frozenset({'cormorant garamond', 'lora'})

# Keywords that can legally appear alongside a font-family, or in the `font`
# shorthand's leading style/weight/variant/stretch/size component, that are never
# themselves a family name. Anything else encountered as a bare, unquoted ident in
# family position is treated as a candidate family name and checked.
NON_FAMILY_FONT_KEYWORDS = frozenset(
    {
        # generic families, always allowed
        'serif',
        'sans-serif',
        'monospace',
        'cursive',
        'fantasy',
        'system-ui',
        'ui-serif',
        'ui-sans-serif',
        'ui-monospace',
        'ui-rounded',
        'emoji',
        'math',
        'fangsong',
        # CSS-wide keywords
        'inherit',
        'initial',
        'unset',
        'revert',
        'revert-layer',
        # font-style
        'normal',
        'italic',
        'oblique',
        # font-weight
        'bold',
        'bolder',
        'lighter',
        # font-variant
        'small-caps',
        # font-stretch
        'ultra-condensed',
        'extra-condensed',
        'condensed',
        'semi-condensed',
        'semi-expanded',
        'expanded',
        'extra-expanded',
        'ultra-expanded',
    }
)

# A hex colour token: 3, 4, 6 or 8 hex digits. Applied to the digits *after* the `#`
# of a tinycss2 HashToken — the tokenizer has already done the work of finding the
# hash, this just tells a colour-shaped hash from an id-shaped one (`#decisions`
# never reaches this check at all, because it lives in selector prelude position,
# which is never scanned; this regex exists for the rarer case of a hash literal
# sitting in declaration *value* position, e.g. `background: #root-ish-but-hex`).
HEX_DIGITS_RE = re.compile(r'^(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{4}|[0-9a-fA-F]{3})$')

# A hex colour literal appearing in TS/TSX source, scanned only inside string
# literals (see find_hex_violations_ts).
HEX_COLOUR_RE = re.compile(r'(?<![0-9a-fA-F_-])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{4}|[0-9a-fA-F]{3})\b')

# A quoted string literal: single, double, or backtick, with backslash escapes
# respected so an escaped quote doesn't end the string early. DOTALL because a
# template literal can span lines.
STRING_LITERAL_RE = re.compile(r"""('(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*"|`(?:\\.|[^`\\])*`)""", re.DOTALL)


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    text: str
    remedy: str
    kind: str = 'adherence'  # 'adherence' (a real design-value violation) or
    # 'parse-error' (the file could not be parsed at all — a different problem
    # with a different remedy, never to be confused with a clean scan).


def line_of(text: str, offset: int) -> int:
    return text.count('\n', 0, offset) + 1


_BRACKET_CLOSERS = {'{': '}', '(': ')', '[': ']'}
_BRACKET_OPENERS = frozenset(_BRACKET_CLOSERS.values())


def _first_unbalanced_bracket_line(text: str) -> int | None:
    """Return the source line of the first `{`, `(`, or `[` left unclosed at
    EOF, or `None` if every one of them is matched — comments and quoted
    strings (backslash escapes respected) are skipped over, never counted, the
    same way tinycss2's own tokenizer treats them.

    This exists because tinycss2 does not: `parse_component_value_list` always
    groups an opening bracket into a block and keeps appending to it until a
    matching closer *or EOF*, with no signal left behind distinguishing the
    two. A qualified rule whose own `{` is truly missing is still caught by
    tinycss2 (`_consume_qualified_rule` returns a `ParseError` on that specific
    EOF), and a stray extra closer is too (`ParseError('Unmatched }')`) — see
    `_collect_parse_errors`. The one shape neither of those catches is an
    opening bracket — at any depth — that never finds its own closer before
    EOF, which is exactly what a truncated or hand-edited-into-garbage
    stylesheet looks like. This function only ever answers "did every open
    bracket close" — it does not, and must not, decide what any of them mean.
    """
    stack: list[tuple[str, int]] = []
    i = 0
    n = len(text)
    line = 1
    while i < n:
        ch = text[i]
        if ch == '\n':
            line += 1
            i += 1
            continue
        if ch == '/' and text[i : i + 2] == '/*':
            end = text.find('*/', i + 2)
            if end == -1:
                return line  # unterminated comment — nothing past here is trustworthy
            line += text.count('\n', i, end)
            i = end + 2
            continue
        if ch in ('"', "'"):
            quote = ch
            j = i + 1
            while j < n:
                if text[j] == '\\' and j + 1 < n:
                    j += 2
                    continue
                if text[j] == quote:
                    j += 1
                    break
                if text[j] == '\n':
                    break  # an unescaped newline ends a CSS string early (bad-string-token)
                j += 1
            line += text.count('\n', i, j)
            i = j
            continue
        if ch in _BRACKET_CLOSERS:
            stack.append((_BRACKET_CLOSERS[ch], line))
            i += 1
            continue
        if ch in _BRACKET_OPENERS:
            if stack and stack[-1][0] == ch:
                stack.pop()
            # A closer that doesn't match the innermost open bracket is a
            # stray closer, not an unclosed opener — tinycss2 reports that
            # one itself (see the module docstring above).
            i += 1
            continue
        i += 1
    return stack[0][1] if stack else None


def _collect_parse_errors(nodes) -> list[css_ast.ParseError]:
    """Recurse through a parsed CSS tree and collect every `ParseError`
    tinycss2 itself produced — a stray closing bracket, a qualified rule whose
    `{` is missing before EOF, a declaration containing a raw `{}` block, and
    so on. Never filtered out and discarded the way the previous round's
    `_iter_declarations` silently dropped them.
    """
    errors: list[css_ast.ParseError] = []
    for node in nodes:
        if isinstance(node, css_ast.ParseError):
            errors.append(node)
        elif isinstance(node, (css_ast.QualifiedRule, css_ast.AtRule)):
            content = getattr(node, 'content', None)
            if content is not None:
                errors.extend(
                    _collect_parse_errors(
                        tinycss2.parse_blocks_contents(content, skip_comments=True, skip_whitespace=True)
                    )
                )
    return errors


def find_parse_failure(path: Path, text: str) -> Violation | None:
    """`None` if `text` is well-formed CSS this control can reason about;
    otherwise a `kind='parse-error'` `Violation` naming where the first
    problem was found. Checked once per file, ahead of any adherence scan —
    a file that fails this is never also scanned for hex colours or fonts,
    because a partial answer about an ambiguous document is worse than no
    answer: it looks complete without being complete.
    """
    unbalanced_line = _first_unbalanced_bracket_line(text)
    if unbalanced_line is not None:
        return Violation(
            path=path,
            line=unbalanced_line,
            text='cannot parse CSS — refusing to report clean',
            remedy='fix the syntax error; adherence cannot be checked on unparseable CSS',
            kind='parse-error',
        )
    stylesheet = tinycss2.parse_stylesheet(text, skip_comments=True, skip_whitespace=True)
    errors = _collect_parse_errors(stylesheet)
    if errors:
        first = errors[0]
        return Violation(
            path=path,
            line=first.source_line,
            text='cannot parse CSS — refusing to report clean',
            remedy='fix the syntax error; adherence cannot be checked on unparseable CSS',
            kind='parse-error',
        )
    return None


def _iter_value_tokens(tokens):
    """Recurse into a CSS component-value list, descending into function
    arguments and bracketed blocks (e.g. `color-mix(in srgb, #2d2b2b 14%, ...)`,
    `linear-gradient(to right, #0000ff, #123456)`), so a hex colour nested inside
    a function call is found exactly as one sitting bare in a declaration value.
    """
    for token in tokens:
        yield token
        children = getattr(token, 'arguments', None) if isinstance(token, css_ast.FunctionBlock) else None
        if children is None:
            children = getattr(token, 'content', None)
        if children:
            yield from _iter_value_tokens(children)


def _iter_declarations(path: Path, block_content):
    """Walk a CSS block's contents (the inside of `{ ... }`) and yield every
    `Declaration` found, recursing into nested rules.

    `tinycss2.parse_blocks_contents` parses a block generically, returning
    whichever mix of `Declaration`, `QualifiedRule`, and `AtRule` the block
    actually contains — it does not require the caller to guess in advance
    whether an at-rule's content is a declaration list or a rule list (the
    guess that produced defect 2: `@media { #fff123 { ... } }` reading the
    nested selector as if it were inside a declaration block). A
    `QualifiedRule`'s `.prelude` is its selector and is never scanned, no
    matter how deep the nesting; only `.content` — the inside of its own
    braces — is walked further. An `AtRule` with no block (e.g. `@import
    url(...);`) has `content is None` and contributes nothing.
    """
    if block_content is None:
        return
    for node in tinycss2.parse_blocks_contents(block_content, skip_comments=True, skip_whitespace=True):
        if isinstance(node, css_ast.Declaration):
            yield node
        elif isinstance(node, (css_ast.QualifiedRule, css_ast.AtRule)):
            yield from _iter_declarations(path, getattr(node, 'content', None))
        # ParseError: malformed CSS is not this control's job to catch.


def find_hex_violations_css(path: Path, text: str) -> list[Violation]:
    """Flag every hex-shaped `HashToken` found inside a CSS declaration's value —
    never inside a selector prelude, an at-rule prelude, a string, or a comment,
    because those are never visited by `_iter_declarations` in the first place.
    """
    violations = []
    stylesheet = tinycss2.parse_stylesheet(text, skip_comments=True, skip_whitespace=True)
    for top_node in stylesheet:
        if isinstance(top_node, (css_ast.QualifiedRule, css_ast.AtRule)):
            declarations = _iter_declarations(path, getattr(top_node, 'content', None))
        else:
            declarations = ()
        for declaration in declarations:
            for token in _iter_value_tokens(declaration.value):
                if isinstance(token, css_ast.HashToken) and HEX_DIGITS_RE.match(token.value):
                    violations.append(
                        Violation(
                            path=path,
                            line=token.source_line,
                            text=f'#{token.value}',
                            remedy='use var(--token)',
                        )
                    )
    return violations


def _is_var_reference(tokens) -> bool:
    return any(isinstance(token, css_ast.FunctionBlock) and token.lower_name == 'var' for token in tokens)


def _font_family_violations_in_declaration(path: Path, declaration: css_ast.Declaration) -> list[Violation]:
    """The per-declaration half of `find_font_violations_css` — pulled out to a
    top-level function (rather than a closure defined inside the scanning loop)
    so `flush` doesn't capture a loop variable ruff's B023 rightly distrusts.
    """
    violations: list[Violation] = []
    run: list[str] = []
    run_line: int | None = None

    def flush() -> None:
        if not run:
            return
        assert run_line is not None  # set alongside the first token appended to `run`
        name = ' '.join(run)
        if name.lower() not in ALLOWED_FONT_FAMILIES:
            violations.append(
                Violation(
                    path=path,
                    line=run_line,
                    text=name,
                    remedy='use var(--font-heading) or var(--font-body)',
                )
            )
        run.clear()

    for token in declaration.value:
        if isinstance(token, css_ast.IdentToken):
            if token.lower_value in NON_FAMILY_FONT_KEYWORDS:
                flush()
            else:
                if not run:
                    run_line = token.source_line
                run.append(token.value)
        elif isinstance(token, css_ast.StringToken):
            flush()
            if token.value.lower() not in ALLOWED_FONT_FAMILIES:
                violations.append(
                    Violation(
                        path=path,
                        line=token.source_line,
                        text=token.value,
                        remedy='use var(--font-heading) or var(--font-body)',
                    )
                )
        elif isinstance(token, css_ast.WhitespaceToken):
            continue
        else:
            flush()
    flush()
    return violations


def find_font_violations_css(path: Path, text: str) -> list[Violation]:
    """Flag every family name in a `font-family` or `font` declaration that names
    something outside Cormorant Garamond / Lora.

    Checking the property name against both `font-family` and `font` closes the
    shorthand gap the previous round's `font-family`-only regex left open. Within
    the value, a quoted string is checked as a whole family name; consecutive bare
    idents are joined into one candidate (so `Comic Sans MS` unquoted reads as one
    name, not three separate failures to match); any ident matching a known
    non-family keyword (a generic family, a font-style/weight/variant/stretch
    keyword, or a CSS-wide keyword) resets the run instead of joining it, so
    `italic bold 12px/1.5 'Comic Sans MS', fantasy` correctly finds one violation
    (the string) and treats `italic`, `bold`, and `fantasy` as what they are.
    """
    violations = []
    stylesheet = tinycss2.parse_stylesheet(text, skip_comments=True, skip_whitespace=True)
    for top_node in stylesheet:
        if not isinstance(top_node, (css_ast.QualifiedRule, css_ast.AtRule)):
            continue
        for declaration in _iter_declarations(path, getattr(top_node, 'content', None)):
            if declaration.name not in ('font-family', 'font'):
                continue
            if _is_var_reference(declaration.value):
                # A custom-property reference, e.g. `font-family: var(--font-heading)`.
                # What the token resolves to is checked where the token itself is
                # defined, not at every call site.
                continue
            violations.extend(_font_family_violations_in_declaration(path, declaration))
    return violations


def find_hex_violations_ts(path: Path, text: str) -> list[Violation]:
    """Flag every hex-shaped token inside a quoted string literal. A hex colour
    in TS/TSX source is always written as a string — `'#fff'`, `"#fff"`, or a
    template literal — never a bare identifier, so restricting the search to
    string contents is sufficient with no further context check.

    Known gap, accepted rather than hidden: a JSX attribute string that is not
    a colour but happens to be entirely hex characters, e.g. `href="#eee"`,
    would still be flagged — it is indistinguishable from `style="#eee"` by
    this rule, since JSX attribute values are ordinary string literals with no
    structural marker of their own. No such fragment exists in this codebase
    today; if one is ever added deliberately, an inline exemption convention
    would be the next step to consider, not a broader exemption.
    """
    violations = []
    for string_match in STRING_LITERAL_RE.finditer(text):
        start, end = string_match.span()
        for match in HEX_COLOUR_RE.finditer(text, start, end):
            violations.append(
                Violation(
                    path=path,
                    line=line_of(text, match.start()),
                    text=match.group(0),
                    remedy='use var(--token)',
                )
            )
    return violations


def find_font_violations_ts(path: Path, text: str) -> list[Violation]:
    """TS/TSX has no `font-family`/`font` shorthand of its own to police — Classical
    is a CSS cascade, not a CSS-in-JS system, and there is no such property literal
    to find in this codebase's `.ts`/`.tsx` files. Kept as an explicit no-op, named
    the same as its CSS counterpart, rather than silently only calling the CSS
    checker — so the omission reads as a decision, not a gap.
    """
    return []


def scan_file(path: Path) -> list[Violation]:
    try:
        text = path.read_text(encoding='utf-8')
    except (UnicodeDecodeError, OSError):
        return []
    if path.suffix in CSS_SUFFIXES:
        parse_failure = find_parse_failure(path, text)
        if parse_failure is not None:
            return [parse_failure]
        return find_hex_violations_css(path, text) + find_font_violations_css(path, text)
    return find_hex_violations_ts(path, text) + find_font_violations_ts(path, text)


def scan() -> list[Violation]:
    if not SRC_DIR.is_dir():
        return []
    violations: list[Violation] = []
    for path in sorted(SRC_DIR.rglob('*')):
        if not path.is_file() or path.suffix not in SCAN_SUFFIXES:
            continue
        if path.resolve() in EXEMPT_PATHS:
            continue
        violations.extend(scan_file(path))
    return violations


def main() -> int:
    violations = scan()
    if not violations:
        print('ok [DEC-1] no hardcoded design values under app/src/.')
        return 0

    for violation in violations:
        rel = violation.path.relative_to(REPO_ROOT).as_posix()
        if violation.kind == 'parse-error':
            print(f'FAIL [DEC-1] {rel}:{violation.line} {violation.text}', file=sys.stderr)
        else:
            print(f'FAIL [DEC-1] {rel}:{violation.line} {violation.text!r}', file=sys.stderr)
        print(f'    -> {violation.remedy}', file=sys.stderr)

    return 1


if __name__ == '__main__':
    raise SystemExit(main())
