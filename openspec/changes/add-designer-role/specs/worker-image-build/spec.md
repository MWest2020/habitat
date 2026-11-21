## ADDED Requirements

### Requirement: Design tools for the designer

The worker image SHALL contain `rsvg-convert`, a pinned Python venv with Pillow
and fontTools, `design-kit`, `design-check` and `logo-tool`, the SIL OFL fonts
Nunito, Fredoka, Baloo 2, Lexend and Andika from google/fonts at a pinned
commit, and the logo-design skill at a pinned commit without its
`assets/library/` of third-party logos. None of it SHALL need network access
at run time.

#### Scenario: Render and check in the cage

- **WHEN** the designer runs `design-kit render mark.svg mark-96.png --width 96 --height 96` and `design-check design/brand`
- **THEN** a 96x96 RGBA PNG appears and the checker prints one line per gate and a JSON summary
