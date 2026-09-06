## 1. Image

- [x] 1.1 Skill-bodies gepind op commit in de Containerfile (`ARG SKILLS_REF`).
- [x] 1.2 Image lokaal gebouwd (exit 0) en gecontroleerd via docker create+cp: 47 skill-mappen in /opt/habitat/skills, 5,8 MB.

## 2. Runtime

- [x] 2.1 Entrypoint materialiseert alleen de skills uit `skills:` van het rolbestand.
- [x] 2.2 Slug-filter tegen padtekens; onbekende skill = melding, geen fout.
- [x] 2.3 `model:` uit het rolbestand als `--model`; zonder veld ongewijzigd gedrag.
- [x] 2.4 Getest met een rolbestand met drie namen: geldig geladen, `../../etc`
      geweigerd met melding, onbekende gemeld — en niets buiten de skills-map gekopieerd.

## 3. Spec + gate

- [x] 3.1 Spec-delta `worker-image-build`.
- [x] 3.2 `openspec validate` + CI groen.
