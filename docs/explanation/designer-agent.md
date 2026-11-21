---
status: draft
last_reviewed: 2026-11-21
---

# A designer agent: what exists, what we use, and why

Mark, 2026-11-21: *"Zelf een ontwerper agent maken. Research is ok. Zal vast
goede agents beschikbaar zijn. Die in habitat brengen."* The first client is
Bazibo's brand redo (`docs/design/brand-brief.md` in MWest2020/bazibo). This
page records the research (2026-11-21) and the recommendation. The role itself
is in [designer](../reference/designer.md).

## Constraints

From the brief and from how habitat runs:

- **Headless, in the cage.** A Kubernetes Job, no GUI, egress only to Anthropic,
  GitHub, npm and PyPI. Nothing may need a login, a design SaaS or an upload of
  Mark's assets.
- **Ownable output.** Bazibo needs full rights (CC0 or MIT-compatible). No stock,
  no work of others, and no AI image models for the logo: their output may echo
  marks they were trained on and its rights are unclear. SVG drawn in code, or
  other deterministic vector work, is the way.
- **Fonts SIL OFL only**, shipped with the app; text in logos as paths.
- **Checkable.** Habitat gates on structured output and on facts, not on prose:
  contrast, sizes, safe zones and licences must be machine-checked.

## What exists

| Candidate | What it is | Licence | Headless, no account | Verdict |
|---|---|---|---|---|
| [kaankiziltug/logo-design-skill](https://github.com/kaankiziltug/logo-design-skill) | Agent Skill: brief, concepts, optical corrections, testing, delivery; dependency-free Python tools (SVG audit, 16 px test sheets, variant and icon export) | MIT (code); its `assets/library/` of 1,432 real logos is **not** MIT ([TRADEMARKS.md](https://github.com/kaankiziltug/logo-design-skill/blob/main/TRADEMARKS.md)) | yes; renders via cairosvg, rsvg-convert, Inkscape or Chrome | **use**, pinned, without the library |
| [neonwatty/logo-designer-skill](https://github.com/neonwatty/logo-designer-skill) | Skill: interview, 3-5 SVG concepts, refine, PNG export | MIT | yes | good, smaller; interview-driven, which a headless run cannot do |
| [luongnv89/skills `logo-designer`](https://github.com/luongnv89/skills) | Skill: identity from project context, 7 SVG variants, HTML showcase | MIT | yes | overlaps; less method |
| [anthropics/skills `canvas-design`](https://github.com/anthropics/skills/tree/main/skills/canvas-design) | Skill: a "design philosophy" then a poster-like PNG/PDF | Apache-2.0 | yes | art, not identity systems; already in the image via skill-forge |
| Subagent files such as Jeremy Longshore's `form` ([listing](https://vibehackers.io/claude-code/agents/form-jeremylongshore)) | A prompt for brand identity and SVG logos | per repo | yes | a prompt only; no tools, no gates |
| Colour MCP servers: [color-mcp-server](https://pypi.org/project/color-mcp-server), [color-engine-mcp](https://socket.dev/npm/package/color-engine-mcp), [@standardbeagle/color](https://socket.dev/npm/package/@standardbeagle/color) | contrast, palettes, colour-blindness simulation | MIT | mostly; color-mcp-server calls TheColorAPI for some tools | not needed: WCAG contrast is ten lines of standard library, and an MCP server adds a process and a supply chain to the cage |
| SVG-generating MCP servers: [svgmaker-mcp](https://app.unpkg.com/@genwave/svgmaker-mcp@0.2.4/files/docs/development-plan.md), [svg-generator-mcp](https://lobehub.com/mcp/aloshy-ai-svg-generator-mcp) | a hosted API, or a local diffusion model (MFLUX) | MIT | no (account), or an image model | **ruled out**: account/upload, or unclear rights |
| Figma, Canva, Recraft and similar via MCP or API | design SaaS | proprietary | no: accounts, uploads | **ruled out** |

Renderers and libraries, all headless:
[resvg](https://github.com/linebender/resvg) (Apache-2.0 OR MIT since the
[Linebender move](https://linebender.org/blog/tmix-10/)),
librsvg's `rsvg-convert` (LGPL-2.1+, a Debian package),
[fontTools](https://github.com/fonttools/fonttools) (MIT, glyph outlines to SVG
paths), Pillow (MIT-CMU), [coloraide](https://github.com/facelessuser/coloraide)
(MIT), [picosvg](https://github.com/googlefonts/picosvg) (Apache-2.0). Fonts:
[google/fonts](https://github.com/google/fonts) `ofl/` (SIL OFL 1.1).

Platform facts the gates use:
[Play icon spec](https://developer.android.com/distribute/google-play/resources/icon-design-specifications)
(512x512, 32-bit PNG, full square; Play masks with a radius of 30 % of the icon;
logos go on the keyline grid, and legacy icons are scaled to 75 %, 384 px),
[adaptive icons](https://developer.android.com/guide/practices/ui_guidelines/icon_design_adaptive)
(108 dp layers, 66 dp safe circle, a monochrome layer),
[WCAG 2.2](https://www.w3.org/TR/WCAG22/) 1.4.3 (text 4.5:1) and 1.4.11
(graphics 3:1).

## Recommendation

**Build our own role around one good method and our own gates.** No existing
agent does what habitat needs: they are skills or prompts that stop and ask,
and none checks its own delivery. The parts are there and they are open:

1. **Method:** the logo-design skill (MIT), vendored at a pinned commit, without
   its trademark library. It is the most complete open method (optical
   corrections, small-size tests, delivery) and its tools run on rsvg-convert.
2. **Tools:** `rsvg-convert` from Debian for rendering (boring, packaged,
   deterministic for a pinned image), fontTools for text to paths, the brief's
   OFL fonts baked in. resvg would render the same with fewer dependencies, but
   it is a downloaded binary where Debian already packages librsvg.
3. **Gates in habitat, not in the prompt:** `design-check`, standard library
   only, run as a Stop hook and again by the entrypoint. A delivery that fails
   a gate cannot pass, whatever the agent says.
4. **Rights by construction:** SVG written by the agent, OFL fonts, no image
   model, no network in the run, `LICENSES.md` checked.

The clever pitfall: an image model would give prettier first sketches. It would
also give a logo nobody can prove is clean, for a children's app whose promise
is trust.

## What the gates check, and what they cannot

`design-check design/brand` (`worker/design/check.py`):

| Gate | Check |
|---|---|
| layout | every required file of the delivery exists |
| directions | 2-3 `## Direction <id>` sections plus `## Recommendation`, each with `directions/<id>/mark.svg`, `tokens.json`, `preview.png` |
| contrast | per palette: ink, ink-soft on base and on-brand on brand 4.5:1; each group accent 3:1 on base; group text 4.5:1 on its tint; fonts from the OFL set; type scale 16 px or more |
| svg | well-formed, `viewBox`, no DOCTYPE/entities, no `<image>`, `<script>`, `<foreignObject>`, `<text>`, `<style>`, `style=`, external `href`, `@import`, `@font-face`; ids unique across `logo/` and `adaptive/` |
| png-sizes | exact sizes; Play icon 32-bit RGBA; App Store icon, feature graphic and screenshot frames without alpha |
| safe-zone | adaptive foreground and monochrome inside the 66/108 circle, background opaque, monochrome one colour; Play icon opaque with its key shape on the 75 % keyline with a 30 % corner radius |
| legibility-24px | the 96 px mark loses under 10 % of its ink to a 3 px morphological opening (no detail thinner than about 0.75 px at 24 px), and the 24 px render is not empty |
| licences | every font in the tokens named in `LICENSES.md` with the OFL; a licence (CC0-1.0 or MIT) for the artwork |

They cannot judge taste, originality or whether a mark resembles another one.
That is the reason for 2-3 directions, a written rationale, a draft PR, and
Mark's choice. The legibility gate is a heuristic: it catches hairlines, not a
mark that is merely confusing at 24 px; the role must look at its own renders.

## Open points

- The skill's look-alike check depends on its trademark library, which stays
  out. Including it would be nominative reference use, but it would put 1,432
  third-party marks in the image; out by default.
- The skill is vendored directly, not through skill-forge. Moving it into
  skill-forge (and the handbook register) is a follow-up if other roles need it.
- The screenshot frame holds a placeholder; putting real screenshots in is
  integration work for a builder change in the app repository.
