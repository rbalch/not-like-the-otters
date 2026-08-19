# M2 — Ingesting a Claude Design

**Status:** not started. A spike — the deliverable is a decision plus the smallest real
proof, not a finished port.

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

### The app icon — `assets/brand/otter-icon.png`

A simplified mark, 1024×1024 RGBA, 31 KB. Format is exactly what `tauri icon` wants
(squared, transparent, ≥1024). Measured composition:

| | |
|---|---|
| fully transparent | 73.7% |
| fully opaque | 25.7% |
| mean colour of every opaque pixel | `rgb(255,255,255)` |

**It is a pure white silhouette on transparency, and that cannot ship as-is.** White on
transparent is invisible against a light dock, a white taskbar, or Finder. Roughly half of
the places an app icon appears are light.

`tauri icon` cannot fix this. Its only background option is `--ios-color` / the manifest's
`bg_color`, and the help is explicit that it applies to the iOS icon. There is no desktop
equivalent — `.ico`, `.icns` and the Linux PNGs are generated straight from the source
alpha, so a white-on-transparent input produces white-on-transparent output.

So the plate has to be composited **before** `tauri icon` runs, producing an opaque
1024×1024 source. Classical supplies the colour:

- `#201f1d` — the ink. White reads cleanly on it, and it matches the otters' black hoodie
  and dark code rain. **Preferred.**
- `#b68235` — the gold accent. Also legible, louder, less consistent with the pair.

Keep the bare white-on-transparent original. It is the correct asset for monochrome
contexts — the manifest's `android_monochrome` slot, or a macOS template icon — where a
flat silhouette is exactly what is wanted. Two files, two jobs:

```
assets/brand/otter-icon.png          white on transparent — monochrome source, keep
assets/brand/otter-icon-plate.png    composited on #201f1d — what tauri icon consumes
```

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
