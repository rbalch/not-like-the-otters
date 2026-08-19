# M2 — Ingesting a Claude Design

**Status:** in progress. A spike — the deliverable is a decision plus the smallest real
proof, not a finished port.

| item | state |
|---|---|
| M2.1 tier 1 — tokens, vendored fonts, window on Classical | **done** (`4c8942a`, `ac2505c`) |
| M2.2 adherence enforcement — DEC-1 + fitness control | **done** (`762566e`…`10d2f0e`) |
| M2.3 port one component (`table` → `.tsx`) with a test | **done** (`bd2a3df`…`6d24cac`) |
| M2.4 otters into the app, green one as brand mark | **done** (`73302a9`…`5863aa4`) |
| M2.5 app icon — crop, plate, `tauri icon` | not started |
| M2.6 re-sync procedure and the tier-3 fork point | not started |

## Goal

Work out how a design system authored at claude.ai/design becomes the app's UI, and
prove the cheapest tier of it end to end. The question is not "can we copy some CSS" —
it is **which parts stay synced, which parts fork on first contact, and what the gate
does about drift.**

## The subject

Project **"Classical"** (`4e7f38e1-0016-4587-8a27-3aab041b2cca`), readable through the
`DesignSync` tool. A warm light serif system: Cormorant Garamond headings, Lora body,
gold accent on stone. Outline buttons, hairline dividers, radius 4.

```
foundations/   color, type, layout, icons, image      HTML previews
components/    buttons, cards, dialog, forms,         HTML previews
               navigation, table
templates/     deck, landing                          not relevant to a desktop app
styles.css     the actual cascade
theme.json     palette, fonts, density, radius
_adherence.oxlintrc.json   a lint config that enforces the system
```

No file needs downloading by hand. The read methods (`list_projects`, `list_files`,
`get_file`) pull from source, which is also the only version that stays current.

## Three tiers, and they are not equally cheap

Ranked by cost, and the ordering is the point:

1. **Tokens and base CSS — mechanical.** `styles.css` plus 48 CSS custom properties.
   They are already CSS; nothing needs translating. This tier is re-syncable forever.
2. **Adherence lint — nearly free, and the most interesting.** See below.
3. **Components — a one-way port.** `components/*.html` are HTML *previews*, not React.
   Every one is hand-ported to a `.tsx`. Incremental, one component at a time, and each
   port needs a Vitest test like any other component.

**Say the quiet part out loud: "sync" only describes tier 1.** Tokens can be re-pulled
and diffed forever. The moment a component is ported to React it forks, and the HTML
preview stops being its source of truth. Any design that promises ongoing two-way sync
of components is lying, and the milestone should not pretend otherwise.

## The adherence config is why this belongs in *this* repo

`_adherence.oxlintrc.json` fails a build on:

- a raw hex colour — use a token via `var()`
- a raw `px` value — use a spacing token
- a font outside Cormorant Garamond / Lora

This repo already runs `oxlint` inside `make lint`. So design drift can become a gate
failure by exactly the same mechanism as governance drift, which is the thesis of the
whole project pointed at a new target.

**The trap, and it is the same one M0 kept finding.** Every rule in that file is
`"warn"`. `make lint` runs plain `oxlint`, and a warning is not a failure — adopting the
config as shipped produces the *appearance* of enforcement with none of the substance.
That is a false success, and this milestone does not land until a deliberate raw hex in
a `.tsx` turns `make check` red. Promote the rules to `error`, or keep them at `warn`
and say plainly in the doc that nothing is enforced. Do not leave it ambiguous.

> **Measured, 2026-08-18 — it is worse than the above, and the fix is elsewhere.**
> The paragraph was right about the direction and wrong about how far it goes. All three
> real rules in `_adherence.oxlintrc.json` are expressed as `no-restricted-syntax` with
> regex AST selectors, and **oxlint 1.78 does not implement that rule at all.** The config
> does not under-enforce; it does not load:
>
> ```
> $ oxlint -c _adherence.oxlintrc.json probe.tsx
> Failed to parse oxlint configuration file.
>   x Rule 'no-restricted-syntax' not found in plugin 'eslint'
> ```
>
> The remaining two rules (`react/forbid-elements`, `no-restricted-imports`) do parse, but
> ship with empty `forbid: []` / `patterns: []` — no-ops by construction. So promoting
> everything to `"error"` would have changed nothing. See ledger finding **F-9**.
>
> Note also that **Classical's own `styles.css` would fail Classical's own rules** — it is
> full of raw `px` (`h1 { font-size: 42px }`). A no-raw-px rule applied to CSS would fire
> on the design system itself.
>
> **Enforcement is therefore rerouted to a fitness control** (`controls/fitness/`) with its
> own decision and pragma, which is this repo's native mechanism and, as the section title
> says, the actual thesis of the project pointed at a new target. It is scoped to `.tsx`
> and leaves CSS to the token file — which is both the only self-consistent scoping and
> exactly what "Done when" already asked for. `_adherence.oxlintrc.json` is kept as a
> vendored reference artifact, not wired into the gate.

## Constraints that are already known

- **Fonts must be vendored.** Cormorant Garamond and Lora have to ship as local files.
  A desktop webview has no CDN guarantee, and the app's own CSP would block a remote
  font anyway. A design that renders only with a network connection is not ingested.
- **The seam holds.** Design assets are frontend-only. Nothing crosses into `src-tauri/`
  and nothing goes near the harness. Fonts and images are app assets like any other.
- **Everything ingested is gate surface.** Prettier, oxlint and `tsc -b` will cover
  every file that lands in `app/`. That is wanted, but it means a bulk dump of unported
  HTML would sit in the tree failing checks. Bring in what is used.
- **This is a desktop app, not a landing page.** `templates/` almost certainly does not
  come across. Judge each foundation on whether the decisions window actually needs it.

## The otter, which is not from the design system

`assets/brand/otter-green.png` and `otter-red.png` — 1254×1254 pixel-art portraits of an
otter in glasses and a hoodie, against Matrix code rain. Green is calm; red has red rain,
red eyes and a furrowed brow. They are the ledger's status light: **red means something
reached three sightings and needs a human.**

Different provenance from Classical, and the distinction matters. Classical defines the
visual language and stays re-syncable; these are brand assets, permanent, never re-pulled.
A future re-sync must not think it owns them.

**They stay opaque, and this is not an oversight.** The obvious instinct is to key out the
background for an icon. Do not — the code rain is most of the pixel area and carries most
of the signal. Cut it and green and red become two nearly identical brown otters. A square
framed portrait is what this is, and Classical's `plate` image treatment is built for
exactly that.

**Scale with nearest-neighbour, at integer factors only.** It is pixel art. Any smooth
resampling turns the blocks to mush and destroys the entire look. The visible block size
suggests a native grid near 209×209, so 1254 is likely a 6× upscale — if the smaller
original still exists it is the better source.

> **Measured, 2026-08-18 — the premise is wrong, and the constraint can be dropped.**
> `otter-green.png` carries ~47,000 unique colours across 1254×1254, and mean intra-block
> deviation *rises monotonically* with every candidate factor (f=2: 2.94, f=3: 4.04,
> f=6: 7.48, f=33: 19.46). A genuine 6× nearest-neighbour upscale would read ~0.00 at
> f=6. There is **no block grid at any factor**: these are continuous-tone renders that
> *depict* pixel art, not pixel art. Mean horizontal run length is 1.15 px.
>
> So there is no native grid to preserve and no smaller original to recover, and smooth
> resampling is the *correct* filter here rather than the forbidden one. The 50% copies in
> `assets/brand/resized/` (1254→627) are clean and are the right source for the app.
> See ledger finding **F-12**.

3.6 MB across the pair is far more than a 128–256 px display needs, and git keeps every
version forever. Downscale before the first commit.

**M2 brings both in and renders the green one** as a static brand mark on the decisions
window. M1 later makes it conditional. The split is deliberate: M2 owns the asset
pipeline, M1 owns the state that switches it.

Shipping the red one unused is a knowing, narrow exception to F-8 — it is the pair that
makes sense, not the single image, and the alternative is proving the scaling and framing
work twice. If M1 slips far enough that this starts to feel like dead weight, delete it and
re-add it with M1.

The portrait is not the app icon: a detailed pixel-art face at 32 px is brown mush.

### The app icon

**This section was rewritten 2026-08-18.** Everything below the rule is measured from the
files actually on disk. The original text described a 1024×1024 RGBA white-on-transparent
silhouette needing a dark `#201f1d` plate composited under it. **No such file exists.** It
was an honest measurement of an asset that was later replaced, and acting on it would have
produced a plate under an image whose actual problem is framing. See ledger finding
**F-12**, and note the general lesson: measure the asset at the point of use.

---

Two candidate sources exist, and neither is ready as-is:

| file | measured |
|---|---|
| `otter-icon.png` | 992×1068, **RGB, no alpha channel**, 628 KB |
| `otter-icon-1024.png` | 1024×1024 RGBA, but **93% opaque** |

Both are the same artwork: a black otter mark on a white rounded plate, sitting inside a
grey mockup surround (`rgb(78,78,75)`). They are screenshots *of* an icon, not icon
assets. `otter-icon-1024.png` is square and RGBA as `tauri icon` requires, but its
transparency is only thin letterbox strips at the left and right edges — the grey mockup
frame is baked in as opaque pixels.

**The real defect is framing, not colour.** The otter mark occupies just **481×554** of the
1024×1024 frame; the rest is grey border and white plate margin. Rendered at true size and
magnified back up, the difference is decisive:

- **as-is at 32 px** — the grey frame eats the outer ring and the otter collapses to a
  featureless crescent. At 16 px it is unusable.
- **cropped tight to the mark** — head, eye, whiskers and body curl all read at 32 px. At
  16 px detail is gone but it stays a distinctive silhouette, which is normal for 16.

So no re-export is needed. The fix is a crop, and the measured numbers are:

```
source  assets/brand/otter-icon-1024.png
crop    620×620 at offset (218, 178)      # mark bbox 288..768 × 212..765, +12% margin
scale   to 1024×1024
plate   #f3f2f2  (Classical --color-bg)
```

**The plate colour inverts from the original plan.** That plan specified `#201f1d`
because it assumed a *white* mark. This mark is black, so it needs a light ground. Classical's
`--color-bg` `#f3f2f2` is the default; `#b68235` gold is the louder alternative.

Only then does `tauri icon` run, on the composited opaque 1024×1024 result. Its only
background option is `--ios-color` / the manifest `bg_color`, which applies to the iOS icon
only — `.ico`, `.icns` and the Linux PNGs come straight from the source, so any plate has
to exist in the input.

Verify at real size, not at 1024. The check is whether the mark still reads at 32 px and
16 px, which is the size that actually decides whether an icon works.

## Scope

- Pull tier 1 into `app/`: `styles.css` and the token set, wired so the existing
  decisions window uses them.
- Vendor the two fonts locally and prove the window renders with the network off.
- Adopt the adherence config, decide `warn` versus `error` explicitly, and demonstrate
  the gate going red on a deliberate violation.
- Port **exactly one** component — whichever the decisions window actually needs — as a
  worked example of the tier-3 path, with a test.
- Bring both otters into `app/src/assets/` downscaled with nearest-neighbour, keep the
  masters in `assets/brand/`, and render the green one as the window's brand mark.
- Composite `otter-icon.png` onto `#201f1d`, run `tauri icon` on the result, and replace
  the default Tauri logo set in `src-tauri/icons/`. Check it at 16 and 32 px.
- Write down the re-sync procedure for tier 1 and the fork point for tier 3.

## Done when

The decisions window renders in Classical with locally-vendored fonts and the green otter
as its brand mark, the app ships its own icon instead of the Tauri default and that icon is
legible at 32 px, a raw hex value in a `.tsx` turns `make check` red, and the doc says
which tier re-syncs and which does not.

## Notes

The temptation is to port all six components because they are sitting right there. That
is a week of work for an app with one screen. One component, proven, teaches the same
lesson and leaves the rest to be pulled when something needs them.

`/design-sync` is not installed in this container. The `DesignSync` tool's own docs
describe driving it with that skill. Everything above is reachable through the raw read
methods, but confirm whether the skill is wanted before assuming the manual path.

**Rechecked 2026-08-18: still not installed.** The available skills are `design` (canvas
authoring — a different thing) plus this repo's own three. The `DesignSync` *tool* works:
`list_projects` returns Classical, `list_files` returns 36 paths, `get_file` reads them.
The manual read-method path is the path, and it was enough for M2.1.

One practical consequence worth recording, because it shapes every remaining work item:
**the `builder` agent has no `DesignSync` tool** — its tools are Read, Write, Edit, Grep,
Glob and Bash. The orchestrator must fetch design files and stage them on disk before
dispatching. Stage them **outside the repo** (the session scratchpad), not in a dot-dir
under `app/`, or they land in the tree and become gate surface themselves.

## Manual QA — M2.1 (tier 1: tokens and vendored fonts)

Run from `/app`. Every command below was run and passed at `ac2505c`.

```sh
make check ; echo "EXIT=$?"                       # expect EXIT=0
```

**The fonts are local and the app never phones home.** This is the acceptance criterion,
so check it rather than trusting the build log:

```sh
npm run build --prefix app
grep -rniE 'fonts\.(googleapis|gstatic)\.com' app/dist ; echo "EXIT=$?"
```
Expect **EXIT=1** — grep found nothing. Any other result means a remote font reference
survived into the bundle and the app needs a network to render correctly.

```sh
ls -la app/src/assets/fonts/                      # four .woff2, ~21-23 KB each
md5sum app/src/assets/fonts/*.woff2 | awk '{print $1}' | sort -u | wc -l
```
Expect **4**. Fewer means duplicate weights got vendored — see finding F-10, the failure
that passes every check while rendering headings at the wrong weight.

**What to look at with your own eyes.** Launch the app:

```sh
npm run tauri dev
```

The decisions window should be unmistakably Classical, not the old purple scaffold:

- warm off-white ground (`#f3f2f2`), near-black text (`#201f1d`) — no white background,
  no purple anywhere
- the "Governance decisions" heading in **Cormorant Garamond semibold** — a high-contrast
  serif with fine hairlines. If it looks like your OS UI font, the `@font-face` family
  string failed to match and it fell back to `system-ui` silently.
- table body text in **Lora** — a softer, sturdier serif, clearly different from the
  heading face
- hairline dividers under the table rows, and the window content centred in a column

Two cheap negative checks:

```sh
# 1. break the token file's link and the window should lose all Classical styling
mv app/src/classical.css /tmp/ && npm run build --prefix app ; echo "EXIT=$?"
# expect a NON-zero exit: the import in main.tsx now resolves to nothing
mv /tmp/classical.css app/src/                    # put it back

# 2. confirm the vendored CSS is unformatted — Prettier is deliberately ignoring it, and
#    if that exemption ever lapses the file gets reflowed and the re-sync diff is lost
grep -c "^\.plate{filter:sepia" app/src/classical.css   # expect 1
```

That `grep` is the real check: `.plate{filter:sepia(...)` is a compact one-liner straight
from upstream, and Prettier would explode it across several lines. Expect **1**. A **0**
means the file got reformatted and byte-identity with source is gone.

**Do not check this with `prettier --check` instead.** Pointed at an ignored file it prints

```
$ npx prettier --check src/classical.css
Checking formatting...
All matched files use Prettier code style!
```

which is Prettier reporting success over an empty file set — it matched nothing, because
`.prettierignore` excludes it. Exactly the shape of ledger finding F-5, where
`tsc --noEmit` exits 0 having type-checked zero files. A command that says "all fine"
while examining nothing is the failure mode this milestone is about.

The stronger fidelity check needs the upstream source, which means re-fetching
`styles.css` from Classical through `DesignSync` and diffing it from `:root {` onward
against `app/src/classical.css`. That is the tier-1 re-sync procedure itself, and M2.6
writes it down properly. Verified once at `ac2505c`: zero differences below the font
block.

**Human-only gates left:** none for M2.1. The window rendering must be seen on a machine
with a display — the container has no compositor — but `npm run tauri dev` on the host is
the whole check.

## Manual QA — M2.2 (design adherence enforcement, DEC-1)

Run from `/app`. Every command was run and passed at `10d2f0e`.

```sh
make check ; echo "EXIT=$?"                                   # expect EXIT=0
uv run pytest tests/test_design_adherence.py -q               # expect 81 passed
uv run python controls/fitness/design_adherence.py ; echo "EXIT=$?"
# expect: ok [DEC-1] no hardcoded design values under app/src/.   EXIT=0
```

**The acceptance criterion — a raw hex in a `.tsx` turns the gate red.** This is the whole
point of the milestone, so run it rather than trusting it:

```sh
sed -i "s|const \[state, setState\]|const _x = '#ff00aa'; const [state, setState]|" app/src/App.tsx
make check ; echo "EXIT=$?"
```
Expect **non-zero**, failing at the `controls` stage with
`FAIL [DEC-1] app/src/App.tsx:<n> '#ff00aa' -> use var(--token)`. Then:

```sh
git checkout -- app/src/App.tsx && make check ; echo "EXIT=$?"    # expect EXIT=0
```

**Three cheap negative checks, each guarding a real failure this control shipped with.**
Write the file, run the control, delete the file:

```sh
# 1. fails closed on unparseable CSS rather than reporting clean
printf '.broken { color: #ff0000\n@@@ {{{\n' > app/src/__t.css
uv run python controls/fitness/design_adherence.py ; echo "EXIT=$?"
# expect EXIT=1 and "cannot parse CSS — refusing to report clean"

# 2. fails closed on an unreadable file
printf '.a { color: #ff0000; }\n\xff\xfe\n' > app/src/__t.css
uv run python controls/fitness/design_adherence.py ; echo "EXIT=$?"
# expect EXIT=1 and "cannot read file (invalid UTF-8) — refusing to report clean"

# 3. does NOT fire on correct code — a hex-shaped id selector is not a colour
printf '@media (max-width: 600px) { #fff123 { padding: 4px; } }\n' > app/src/__t.css
uv run python controls/fitness/design_adherence.py ; echo "EXIT=$?"
# expect EXIT=0, ok

rm -f app/src/__t.css
```

Check 3 matters most. A control that fires on correct code is worse than the drift it
catches, because it teaches everyone to route around the gate.

**What to look at with your own eyes.** Nothing visual changed — `--color-danger` keeps
the exact `#b3261e` the raw hex had, so this was pure tokenisation. Launch the app and
confirm the error state still renders the same red if you want reassurance:

```sh
npm run tauri dev
```

**Two token files, and the difference is the point:**

| file | whose | on re-sync |
|---|---|---|
| `app/src/classical.css` | upstream Classical's | **overwritten** — never hand-edit |
| `app/src/tokens-local.css` | ours | **never touched** — app-specific tokens live here |

When Classical does not define something the app needs, it goes in `tokens-local.css`.
That is the tier-1/tier-3 boundary made physical.

**Human-only gates left:** none.

**Known accepted gaps**, all documented in the control's docstring and none present in the
tree today: `href="#eee"` in a `.tsx` string would misfire as a colour; a regex literal
immediately after a `}` closing a block statement could confuse the TS lexer; `@supports`
preludes are deliberately unscanned, because a hex in a feature query is not a design
value. Raw `px` is deliberately not enforced — see DEC-1.

## Manual QA — M2.3 (port one component: table → `.tsx`)

Run from `/app`. Every command was run and passed at `bd2a3df` and, after a polish
round adding per-row correspondence and header-role tests, at the commit on top of it
(see below).

```sh
make check ; echo "EXIT=$?"                                       # expect EXIT=0
npm run test --prefix app                                         # expect 2 files, 14 tests passed
uv run python controls/fitness/design_adherence.py ; echo "EXIT=$?"
# expect: ok [DEC-1] no hardcoded design values under app/src/.   EXIT=0
```

**The tests-first evidence.** `DecisionTable.test.tsx` was written and run against a
component that did not yet exist:

```
$ npx --no-install vitest run src/components/DecisionTable.test.tsx   # (from app/)
 FAIL  src/components/DecisionTable.test.tsx [ src/components/DecisionTable.test.tsx ]
Error: Failed to resolve import "./DecisionTable" from
  "src/components/DecisionTable.test.tsx". Does the file exist?
```

Then `DecisionTable.tsx` was implemented and the same run went to 10 passed. A later
polish round added two more cases — column-header roles/text/order, and per-row cell
correspondence across a multi-decision render — bringing the suite to 12 cases (14 total
with `App.test.tsx`). The per-row case was verified against a deliberately transposed
`DecisionTable.tsx` (each row rendering the *next* decision's title/status/superseded-by)
and failed there before being run, unmodified, against the real component.

**What to look at with your own eyes.** Launch the app:

```sh
npm run tauri dev
```

The decisions table should look identical to before this change — small-caps grey
headers, hairline row dividers, a faint hover tint — plus one new detail: the **status**
column now renders as a pill/tag (gold-outline for anything not `accepted` or
`superseded`, filled for those two), instead of plain text.

**The fallback is the point — force an unknown status and confirm it still shows:**

```sh
sed -i "s/status: 'accepted'/status: 'proposed'/" app/src/components/DecisionTable.test.tsx
npx vitest run --root app src/components/DecisionTable.test.tsx 2>&1 | tail -5
git checkout -- app/src/components/DecisionTable.test.tsx
```

The "renders 'accepted' status..." case fails once its own fixture status no longer
matches its own assertion (`tag-accent`) — a cheap self-check that the test actually
exercises the switch rather than passing vacuously. Restore the file afterward.

**Human-only gates left:** none. `App.test.tsx` was not modified and still passes,
confirming the DOM contract (`<main id="decisions">`, `role="status"`, `role="alert"`,
a real `<table>`) held across the port.

**What forked, concretely — the tier-3 point this work item exists to demonstrate:**

- The HTML preview's `<td class="text-muted">Today</td>` is a plain "Updated" column
  with a hardcoded string. The ported cell means something specific to this app
  (superseded-by) and its content is computed: `null` → empty string, a decision ID →
  `superseded by DEC-«n»`. The preview has no such branching; the `.tsx` owns a rule the
  markup never expressed.
- The preview's `status` column is a **freeform label** (`Live`, `In review`, `Draft`)
  with tag class chosen by hand, per row, in the HTML. The `.tsx` collapses that to a
  three-way `tagClassFor(status: string)` function with an explicit fallback branch —
  the preview has nothing playing that role because it never has to render a status it
  wasn't told about in advance. This is the fork the brief called out as the most
  important line in the work item, and it has no analogue in Classical at all: an HTML
  preview is never handed an *unknown* value, only the ones its author chose to type in.
- The preview's demo chrome (`.demo`, `.demo-head`, `.note` — a caption block with
  layout guidance) is preview-only scaffolding and did not come across; only the
  `<table class="table">` subtree ported.
- `#decisions table { margin-top: var(--space-4) }` stayed in `App.css` — it is this
  app's placement of the table under its own `<h1>`, not a restatement of anything
  `.table` defines. Everything `.table`/`.tag`/`.text-muted` already styled (width,
  border-collapse, padding, dividers, hover tint) was deleted from `App.css` once
  `DecisionTable` adopted those classes.

## Manual QA — M2.4 (the otters as the window's brand mark)

Run from `/app`. Every command was run as written and passed at `5863aa4`.

```sh
make check ; echo "EXIT=$?"                    # expect EXIT=0
npm run test --prefix app                      # expect 17 passed, 3 files
```

**What to look at with your own eyes.** Launch the app:

```sh
npm run tauri dev
```

The green otter sits above "Governance decisions", 128 px, centred, in a `--color-surface`
mat with a hairline `--color-divider` outline. **The green code rain must read as green,
not brown** — see the `.plate` note below. Everything else is M2.1–M2.3's window.

**The masters are not in git.** Only `assets/brand/otter-icon-1024.png` is tracked, because
`tauri icon` needs it in M2.5. Everything else under `assets/` is ignored by `/assets/*` in
`.gitignore` and lives only on this machine. **A fresh clone cannot regenerate the app
assets** — it gets the committed 256 px derivatives and nothing else. That is a deliberate
call (git keeps every version forever, and the pair is ~5 MB), and it means the command
below is the only written record of how the committed PNGs were produced:

```sh
uv run --with pillow python -c "
from PIL import Image
for n in ('green','red'):
    im = Image.open(f'assets/brand/otter-{n}.png').convert('RGB')
    im.resize((256,256), Image.LANCZOS).save(f'app/src/assets/otter-{n}.png', optimize=True)
"
```

Inputs are the untracked 1254×1254 masters. Outputs: 96,502 B and 100,022 B. 256 px is 2×
the 128 px display size, for HiDPI. **Lanczos, not nearest-neighbour** — see the measured
correction in the otter section above; these are continuous-tone renders, not pixel art.

Three cheap checks:

```sh
# 1. both otters reach the bundle — the red one is unreferenced by any view until M1,
#    so this is what stops it silently vanishing (ledger F-8)
npm run build --prefix app && ls app/dist/assets/otter-*.png    # expect two files

# 2. the ignore pattern is anchored — a bare `assets/` would match at ANY depth and
#    silently swallow app/src/assets/. Note --no-index: plain check-ignore skips
#    TRACKED files and reports them not-ignored regardless of the pattern.
git check-ignore -q --no-index app/src/assets/otter-green.png ; echo "EXIT=$? (expect 1)"
git check-ignore -q --no-index assets/brand/otter-red.png     ; echo "EXIT=$? (expect 0)"
git ls-files assets/                                          # expect exactly one path

# 3. alt text cannot drift from the image it describes (ledger F-17)
grep -c "^    alt:" app/src/assets/otters.ts   # expect 2 — one per otter, beside its src
```

(The indent in check 3 is load-bearing: a bare `grep -c "alt:"` returns **3**, because the
`OtterVariant` interface declares an `alt` field too. Counting that as an otter would make
the check pass for the wrong reason — which is finding **F-16** in miniature, caught while
writing this section.)

Check 2 matters most and is the one a human should actually run: a wrong ignore pattern
fails **silently and only on someone else's clone**, which is the worst shape available.

### On `.plate`, and a number that was wrong

`theme.json` sets `imageTreatment: "plate"`, and Classical's `.plate` applies
`sepia(0.22) saturate(0.82) contrast(1.05)` plus a border and outline. The brand mark
takes **only the framing**, via a local `.brand-mark` class in `App.css` — the filter is
skipped.

The first justification recorded for this was **wrong**, and the correction is the more
useful artifact. It claimed the filter compressed the green/red hue separation by ~37%,
measured over "non-background" pixels. But the code rain *is* the background, and it is the
only place the two images differ — the face and hoodie are the same brown in both. So that
measurement compared two near-identical things and found their hues collapsing, which is
close to tautological. Measured where the signal actually lives:

| region | before | after | collapse |
|---|---|---|---|
| body / fur (as originally sampled) | — | — | 37–66% |
| whole image | 29.7° | 26.1° | 12% |
| **code rain** | **91.5°** | **84.2°** | **~8%** |

Three independent implementations agree on ~8%. **84° of separation survives — the filter
never endangered the status light.** See ledger finding **F-16**, which records this as the
fourth instance of one pattern: a precise, correct-looking measurement whose *subject* was
wrong.

The filter is still skipped, on two reasons that survive the correction:

1. A status light should read as true green and true red, not tinted toward the system's
   warm anchor. That is a brand judgement, not a technical constraint — applying `.plate`
   as-is is defensible on the evidence and is a one-line change.
2. Composing (`class="plate brand-mark"` with `filter: none`) would couple the mark to
   `classical.css`, which a tier-1 re-sync overwrites — a future upstream change to the
   plate's border would silently move the brand mark. Duplicating two declarations is
   cheaper than that coupling.

**This is the tier-3 fork point M2.6 documents**: not "the design system was wrong", but
"here is exactly where it did not fit, here is the number, and here is what we kept."

**Human-only gates left:** none. The window must be seen on a machine with a display — the
container has no compositor — but `npm run tauri dev` on the host is the whole check.
