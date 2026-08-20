"""Tests for controls/fitness/design_adherence.py (DEC-1).

Gate-enforced: this file runs under `uv run pytest` / `make test` / `make check`,
so a future round that reintroduces one of these defects fails the build, not just
a manual repro someone has to remember to run.

Each case is driven straight through `find_hex_violations_css`,
`find_font_violations_css`, and `find_hex_violations_ts` — the same functions
`scan_file` calls — rather than round-tripping through real files on disk, so a
case is one string literal, not a fixture file to keep track of.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from design_adherence import (
    find_font_violations_css,
    find_hex_violations_css,
    find_hex_violations_ts,
    find_parse_failure,
    scan_file,
)

CSS_PATH = Path('app/src/example.css')
TSX_PATH = Path('app/src/example.tsx')


def hex_css(text: str) -> list[str]:
    return [v.text for v in find_hex_violations_css(CSS_PATH, text)]


def font_css(text: str) -> list[str]:
    return [v.text for v in find_font_violations_css(CSS_PATH, text)]


def hex_ts(text: str) -> list[str]:
    return [v.text for v in find_hex_violations_ts(TSX_PATH, text)]


# --- must FAIL: hex colours in CSS -------------------------------------------


@pytest.mark.parametrize(
    ('css', 'expected'),
    [
        ('.x { color: #abcdef; }', ['#abcdef']),
        ('.x { border: 1px solid #ff0000; }', ['#ff0000']),  # round 1's gap
        ('.x { box-shadow: 0 1px 2px #00ff00; }', ['#00ff00']),
        ('.x { outline: 2px dashed #fedcba; }', ['#fedcba']),
        (
            '.x { background: linear-gradient(to right, #0000ff, #123456); }',
            ['#0000ff', '#123456'],
        ),
    ],
)
def test_hex_css_violations_caught(css: str, expected: list[str]) -> None:
    assert hex_css(css) == expected


def test_hex_css_survives_quoted_brace_before_it() -> None:
    """Defect 1: a `}` inside a string must not desync brace-depth tracking and
    hide a real violation that follows it."""
    css = """
    .icon::before {
      content: "}";
      color: #123abc;
    }
    """
    assert hex_css(css) == ['#123abc']


def test_hex_css_inside_media_block_declaration() -> None:
    css = """
    @media (max-width: 600px) {
      .x { color: #abc123; }
    }
    """
    assert hex_css(css) == ['#abc123']


# --- must FAIL: font-family / font shorthand ---------------------------------


def test_font_shorthand_family_caught() -> None:
    """Defect 3: the `font` shorthand's trailing family component is not
    exempt just because the property isn't spelled `font-family`."""
    css = ".fancy { font: italic bold 12px/1.5 'Comic Sans MS', fantasy; }"
    assert font_css(css) == ['Comic Sans MS']


def test_font_family_disallowed_caught() -> None:
    css = ".fancy { font-family: 'Comic Sans MS'; }"
    assert font_css(css) == ['Comic Sans MS']


# --- must FAIL: TS/TSX hex colours --------------------------------------------


@pytest.mark.parametrize(
    ('src', 'expected'),
    [
        ("const c = ['#ff0000', '#00ff00'];", ['#ff0000', '#00ff00']),
        ("function f() { return '#123abc'; }", ['#123abc']),
        ('const c = `#dddddd`;', ['#dddddd']),
        ('const c = "#eeeeee";', ['#eeeeee']),
    ],
)
def test_hex_ts_violations_caught(src: str, expected: list[str]) -> None:
    assert hex_ts(src) == expected


# --- must FAIL: TS/TSX comment-awareness (round 3 blocker 1) -----------------
#
# The string-literal scanner must not be desynced by an apostrophe inside a `//`
# or `/* */` comment, a `//` inside an ordinary string, an escaped quote inside a
# string, or an unrecognised regex literal — any of these treating a non-string
# character as a string delimiter corrupts quote parity for the rest of the file,
# hiding every real violation that follows.


def test_hex_ts_survives_apostrophe_in_line_comment() -> None:
    src = "// don't do this\nconst z = '#123456'\n"
    assert hex_ts(src) == ['#123456']


def test_hex_ts_survives_apostrophe_in_block_comment() -> None:
    src = "/* it's fine */\nconst z = '#123456'\n"
    assert hex_ts(src) == ['#123456']


def test_hex_ts_survives_comment_before_template_literal() -> None:
    src = "// don't do this\nconst z = `#123456`\n"
    assert hex_ts(src) == ['#123456']


def test_hex_ts_survives_slashes_inside_a_string() -> None:
    """A `//` inside an ordinary string (a URL) must not be read as opening a
    line comment that swallows the rest of the file."""
    src = "const u = 'https://x.com'\nconst z = '#123456'\n"
    assert hex_ts(src) == ['#123456']


def test_hex_ts_survives_escaped_quote_inside_a_string() -> None:
    src = "const s = 'it\\'s'\nconst z = '#123456'\n"
    assert hex_ts(src) == ['#123456']


def test_hex_ts_survives_regex_literal_after_assignment() -> None:
    """A `/regex/` literal containing a quote character must not be read as
    opening a string — the regex-vs-divide heuristic must recognise `/` as a
    regex start after `=`."""
    src = "const r = /it's/\nconst z = '#123456'\n"
    assert hex_ts(src) == ['#123456']


def test_hex_ts_survives_regex_literal_after_return() -> None:
    src = "function f() { return /it's/ }\nconst z = '#123456'\n"
    assert hex_ts(src) == ['#123456']


def test_hex_ts_hex_inside_template_interpolation() -> None:
    """A string literal nested inside a template literal's `${ ... }`
    interpolation is still ordinary code and must still be scanned."""
    src = "const z = `prefix ${ '#123456' } suffix`\n"
    assert hex_ts(src) == ['#123456']


def test_hex_ts_comment_inside_interpolation_does_not_desync() -> None:
    src = "const z = `${ /* it's ok */ '#123456' }`\n"
    assert hex_ts(src) == ['#123456']


def test_hex_ts_comment_only_is_not_flagged() -> None:
    """A hex-shaped string sitting inside commentary, not code, is not a
    design-value violation — matching how the CSS side treats comments."""
    assert hex_ts('// #123456 is our brand colour, do not hardcode it\n') == []


def test_hex_ts_block_comment_only_is_not_flagged() -> None:
    assert hex_ts('/* #123456 */\n') == []


# --- must FAIL: CSS font property names are case-insensitive (round 3 blocker 2)


@pytest.mark.parametrize(
    'css',
    [
        '.a { FONT-FAMILY: Arial; }',
        '.a { Font-Family: Arial; }',
        '.a { FONT: italic bold 12px/1.5 Arial; }',
    ],
)
def test_font_property_name_case_insensitive(css: str) -> None:
    assert font_css(css) == ['Arial']


# --- must FAIL: font family inside a var() fallback (round 4 blocker) --------
#
# `var(--font-heading, Arial)` genuinely renders Arial whenever the token is
# undefined -- that is a real non-Classical font reaching the cascade, not
# commentary about one, so it must be caught exactly like a hex colour inside
# a `var()` fallback already is (`color: var(--x, #123456)` -> FAIL). The old
# code bailed out of the *entire declaration* the moment any `var()` appeared
# anywhere in it, which is the asymmetry: the hex path recurses into a
# function's arguments looking for a HashToken; the font path did not do the
# equivalent walk looking for a family name.


@pytest.mark.parametrize(
    'css',
    [
        '.a { font-family: var(--font-heading, Arial); }',
        '.b { font-family: var(--font-body), Arial; }',
        '.c { font: var(--font-body, 16px Arial); }',
        '.d { font-family: Arial, var(--font-body); }',
        '.e { font-family: var(--a, var(--b, Arial)); }',  # nested var() fallback
    ],
)
def test_font_family_inside_var_fallback_caught(css: str) -> None:
    assert font_css(css) == ['Arial']


def test_font_family_lone_var_reference_stays_clean() -> None:
    """The honest case: a bare `var(--font-heading)` reference with no
    fallback at all must not be flagged -- there is no literal family name
    anywhere in the declaration to check."""
    assert font_css('.a { font-family: var(--font-heading); }') == []


def test_font_family_var_fallback_of_allowed_family_stays_clean() -> None:
    assert font_css(".a { font-family: var(--font-heading, 'Cormorant Garamond'); }") == []


# --- shared structural battery: both rule-halves against the same shapes -----
#
# Every defect found since round 3 was a structural shape one half of this
# control (hex, font) handled and the other did not. The two halves are
# intended to walk CSS value structure identically -- recurse into every
# function's arguments and nested blocks, ignore comments and at-rule
# preludes, treat a `var()` fallback as real value content -- so divergence
# between them on the same shape is a bug, never a design choice. This battery
# runs one CSS snippet exercising a structural shape through *both*
# `find_hex_violations_css` and `find_font_violations_css` and asserts both
# outcomes, even for a shape that is only "interesting" for one half, so an
# asymmetric regression shows up here instead of shipping unnoticed again.
_STRUCTURAL_BATTERY = [
    (
        'plain_declaration',
        '.x { color: #123456; font-family: Arial; }',
        ['#123456'],
        ['Arial'],
    ),
    (
        'var_with_fallback',
        '.x { color: var(--c, #123456); font-family: var(--f, Arial); }',
        ['#123456'],
        ['Arial'],
    ),
    (
        'var_no_fallback',
        '.x { color: var(--c); font-family: var(--f); }',
        [],
        [],
    ),
    (
        'var_in_comma_list',
        '.x { background: var(--c), #123456; font-family: var(--f), Arial; }',
        ['#123456'],
        ['Arial'],
    ),
    (
        'nested_var_fallback',
        '.x { color: var(--c, var(--d, #123456)); font-family: var(--f, var(--g, Arial)); }',
        ['#123456'],
        ['Arial'],
    ),
    (
        'function_nesting',
        '.x { background: linear-gradient(to right, #0000ff, #123456); font-family: Arial; }',
        ['#0000ff', '#123456'],
        ['Arial'],
    ),
    (
        'important',
        '.x { color: #123456 !important; font-family: Arial !important; }',
        ['#123456'],
        ['Arial'],
    ),
    (
        'uppercase_property',
        '.x { COLOR: #123456; FONT-FAMILY: Arial; }',
        ['#123456'],
        ['Arial'],
    ),
    (
        'at_rule_nesting',
        '@media (max-width: 600px) {\n  .x { color: #123456; font-family: Arial; }\n}',
        ['#123456'],
        ['Arial'],
    ),
    (
        'comment_interference',
        '/* #dead00 Arial */\n.x { color: #123456; font-family: Arial; }',
        ['#123456'],
        ['Arial'],
    ),
    (
        'allowed_values_only',
        ".x { color: var(--color-danger); font-family: 'Cormorant Garamond'; }",
        [],
        [],
    ),
]


@pytest.mark.parametrize(
    ('name', 'css', 'expected_hex', 'expected_font'), _STRUCTURAL_BATTERY, ids=[b[0] for b in _STRUCTURAL_BATTERY]
)
def test_structural_battery_both_halves_agree(
    name: str, css: str, expected_hex: list[str], expected_font: list[str]
) -> None:
    assert hex_css(css) == expected_hex, f'{name}: hex half diverged'
    assert font_css(css) == expected_font, f'{name}: font half diverged'


def test_structural_battery_malformed_input_suppresses_both_halves() -> None:
    """A parse-error result must be uniform across both design-value types in
    the same file -- neither a hex nor a font violation is reported
    individually once the file is unparseable; the whole file refuses to
    answer once, not each half separately."""
    css = '.broken { color: #123456; font-family: Arial\n@@@ unparseable {{{\n'
    assert scan_file_violations(css, suffix='.css') == ['cannot parse CSS — refusing to report clean']


# --- must PASS: correct code, never flagged -----------------------------------


@pytest.mark.parametrize(
    'css',
    [
        '#decisions { max-width: 720px; }',
        '#decisions th,\n#decisions td { text-align: left; }',
        'a:hover, #root { color: red; }',
        '@media (max-width: 600px) {\n  #fff123 {\n    padding: 4px;\n  }\n}',  # defect 2
        '/* a hex value like #dead00 belongs in a comment sometimes */\n.x { color: red; }',
        ':root {\n  @media (max-width: 600px) {\n    font-size: 15px;\n  }\n}',
        '.x { color: var(--color-danger); }',
    ],
)
def test_hex_css_survives_correct_code(css: str) -> None:
    assert hex_css(css) == []


def test_font_family_allowed_values_pass() -> None:
    css = (
        ".a { font-family: 'Cormorant Garamond'; }\n"
        ".b { font-family: 'Lora'; }\n"
        '.c { font-family: var(--font-heading); }\n'
        '.d { font: 16px/145% var(--font-body); }\n'
        '.e { font: inherit; }\n'
    )
    assert font_css(css) == []


def test_media_selector_not_treated_as_declaration() -> None:
    """Defect 2, isolated: a hex-shaped selector nested inside an at-rule must
    never be scanned — its prelude is never declaration territory, at any
    nesting depth."""
    css = '@media (max-width: 600px) {\n  #fff123 {\n    padding: 4px;\n  }\n}'
    assert hex_css(css) == []


@pytest.mark.parametrize(
    'relative_path',
    [
        'app/src/App.css',
        'app/src/App.tsx',
        'app/src/App.test.tsx',
        'app/src/index.css',
        'app/src/main.tsx',
        'app/src/lib/decisions.ts',
    ],
)
def test_real_files_are_clean(relative_path: str) -> None:
    """Every real (non-exempt) file currently under app/src/ must pass both
    checks — the control proving itself against the actual tree, not just
    against hand-picked snippets."""
    repo_root = Path(__file__).resolve().parents[1]
    path = repo_root / relative_path
    text = path.read_text(encoding='utf-8')
    if path.suffix == '.css':
        assert find_hex_violations_css(path, text) == []
        assert find_font_violations_css(path, text) == []
    else:
        assert find_hex_violations_ts(path, text) == []


# --- must FAIL: unparseable CSS is a failure, never a silent pass ------------
#
# tinycss2 does not surface "a block was never closed before EOF" as an error —
# the CSS Syntax spec calls that a parse error but doesn't require reporting one,
# and tinycss2 follows the spec's silent recovery. A governance control cannot
# accept that: ambiguity must fail closed, not report a partial scan as if it
# were a complete one.


def test_unclosed_block_with_a_real_violation_inside_still_fails() -> None:
    """A hex colour sitting inside the malformed region must not be silently
    dropped just because the file around it doesn't parse — the file fails as
    a whole, distinctly from an adherence violation."""
    css = '.broken { color: #ff0000\n@@@ unparseable {{{\n'
    failure = find_parse_failure(CSS_PATH, css)
    assert failure is not None
    assert failure.kind == 'parse-error'
    assert hex_css(css) == []  # the raw scanner alone would miss it — this is why
    # scan_file must check find_parse_failure first, not rely on the scanner to
    # notice its own confusion.
    assert scan_file_violations(css, suffix='.css') == ['cannot parse CSS — refusing to report clean']


def test_unclosed_block_with_no_violations_still_fails() -> None:
    """Unparseable is unparseable regardless of whether the visible part of the
    file happens to contain a design-value violation — the file is refused
    either way, because the control cannot tell what it isn't seeing."""
    css = '.broken { color: red\n@@@ unparseable {{{\n'
    failure = find_parse_failure(CSS_PATH, css)
    assert failure is not None
    assert failure.kind == 'parse-error'


def test_violation_before_the_broken_region_is_not_silently_dropped() -> None:
    """A real violation earlier in the same file, followed by a malformed
    region, must not produce a clean scan that quietly omits it — the whole
    file fails instead of returning a partial, misleadingly-complete answer."""
    css = '.a { color: #ff0000; }\n.broken { color: red\n@@@ unparseable {{{\n'
    assert find_parse_failure(CSS_PATH, css) is not None
    assert scan_file_violations(css, suffix='.css') == ['cannot parse CSS — refusing to report clean']


@pytest.mark.parametrize(
    'relative_path',
    [
        'app/src/App.css',
        'app/src/index.css',
        'app/src/tokens-local.css',
        'app/src/classical.css',
    ],
)
def test_real_css_files_parse_cleanly(relative_path: str) -> None:
    """The fail-closed check must never fire on the current tree — every real
    `.css` file, including the exempt token files, is well-formed CSS."""
    repo_root = Path(__file__).resolve().parents[1]
    path = repo_root / relative_path
    text = path.read_text(encoding='utf-8')
    assert find_parse_failure(path, text) is None


# --- must FAIL: unreadable/undecodable files fail closed, never silently -----
#
# `UnicodeDecodeError` / `OSError` from `read_text` used to make `scan_file`
# return `[]` -- indistinguishable from "this file is fine". Treated exactly
# like unparseable CSS already is (see above): refuse to answer with a
# distinct `kind='parse-error'` violation rather than report clean.


def test_undecodable_css_with_a_violation_still_fails(tmp_path: Path) -> None:
    path = tmp_path / 'broken.css'
    path.write_bytes(b'.a { color: #ff0000; }\n\xff\xfe invalid utf8\n')
    violations = scan_file(path)
    assert len(violations) == 1
    assert violations[0].kind == 'parse-error'
    assert 'cannot read file' in violations[0].text


def test_undecodable_css_with_no_violation_still_fails(tmp_path: Path) -> None:
    path = tmp_path / 'broken.css'
    path.write_bytes(b'.a { color: red; }\n\xff\xfe invalid utf8\n')
    violations = scan_file(path)
    assert len(violations) == 1
    assert violations[0].kind == 'parse-error'


def test_undecodable_tsx_with_a_violation_still_fails(tmp_path: Path) -> None:
    path = tmp_path / 'broken.tsx'
    path.write_bytes(b"const z = '#ff0000'\n\xff\xfe invalid utf8\n")
    violations = scan_file(path)
    assert len(violations) == 1
    assert violations[0].kind == 'parse-error'


def test_undecodable_tsx_with_no_violation_still_fails(tmp_path: Path) -> None:
    path = tmp_path / 'broken.tsx'
    path.write_bytes(b"const z = 'hello'\n\xff\xfe invalid utf8\n")
    violations = scan_file(path)
    assert len(violations) == 1
    assert violations[0].kind == 'parse-error'


def test_unreadable_missing_file_fails_closed(tmp_path: Path) -> None:
    """A file that vanished (or was never readable) between listing and
    reading must not be silently treated as clean -- the `OSError` branch of
    the same guard, not just the `UnicodeDecodeError` one."""
    path = tmp_path / 'does-not-exist.css'
    violations = scan_file(path)
    assert len(violations) == 1
    assert violations[0].kind == 'parse-error'


@pytest.mark.parametrize(
    'relative_path',
    [
        'app/src/App.css',
        'app/src/App.tsx',
        'app/src/App.test.tsx',
        'app/src/index.css',
        'app/src/main.tsx',
        'app/src/lib/decisions.ts',
        'app/src/classical.css',
        'app/src/tokens-local.css',
    ],
)
def test_real_files_read_cleanly(relative_path: str) -> None:
    """The read-failure guard must never fire on the current tree -- every
    real file, including the two exempt token files (scanned here without
    the exemption `scan()` applies, since only the read step is under test),
    reads and decodes without tripping it."""
    repo_root = Path(__file__).resolve().parents[1]
    path = repo_root / relative_path
    violations = scan_file(path)
    assert all(v.kind != 'parse-error' for v in violations)


def scan_file_violations(text: str, *, suffix: str) -> list[str]:
    """Round-trip a snippet through `scan_file` itself (not the lower-level
    finders) via a real temp file, so the parse-failure short-circuit in
    `scan_file` is exercised the same way the control's own `main()` uses it.
    """
    with tempfile.NamedTemporaryFile('w', suffix=suffix, delete=False) as handle:
        handle.write(text)
        path = Path(handle.name)
    try:
        return [v.text for v in scan_file(path)]
    finally:
        path.unlink()
