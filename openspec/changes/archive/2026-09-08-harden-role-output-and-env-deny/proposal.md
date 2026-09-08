# Change: harden-role-output-and-env-deny

## Why

Twee gaten die op 2026-09-04/05 in een echte keten zichtbaar werden
(MWest2020/internetnl-cli, changes `polish-supporter-mail` en
`facade-followups`).

1. **Een rol kan leeg rapporteren en toch als PASS tellen.** De reviewer
   op `facade-followups` draaide 55 beurten, kostte $1,32 en leverde
   `{"verdict":"PASS","summary":"test","findings":[]}`. Dat is
   schema-geldig, dus habitat rekende de run als geslaagd en de keten liep
   door. Er zat geen review in. Dat is erger dan een FAIL: het ziet eruit
   als dekking die er niet is, en niets in de keten merkt het op. De run
   moest handmatig worden overgedaan ($1,3) voordat er een echte
   beoordeling lag.

2. **De `.env`-deny blokkeert ook `.env.example`.** De builder op
   `polish-supporter-mail` kon één taak niet uitvoeren — een regel
   toevoegen aan `deploy/.env.example` — omdat `Read(**/.env.*)` ook dat
   pad vangt. Hij meldde het netjes als deviation en zette zichzelf op
   FAIL, precies zoals bedoeld, maar de taak bleef liggen en moest met de
   hand af. `.env.example` is een gecommit sjabloon zónder geheimen; élke
   repo heeft er een, en een builder moet hem kunnen bijwerken. De regel
   kost hier werk zonder iets te beschermen: de worker kloont vers van
   GitHub, dus alles wat op `.env*` matcht staat al in de repo die de rol
   sowieso mag lezen.

## What Changes

**A. Een ondergrens op `summary` in alle vier de rol-schema's.**
`summary` krijgt `"minLength": 200`. Dat is ongeveer twee zinnen: genoeg
om te dwingen dat een rol zegt wát hij bekeken heeft, en laag genoeg dat
een terechte "niets gevonden"-uitkomst er nog onder past. Het schema gaat
als `--json-schema` mee naar de agent, dus dit is geen controle achteraf
maar een eis waaraan de gestructureerde uitvoer moet voldoen.

Dit maakt vacuüm rapporteren niet onmogelijk — 200 tekens vulling kan
altijd — maar het haalt de goedkoopste variant weg en maakt een lege
review zichtbaar in plaats van onopvallend.

**B. De `.env`-deny versmald.** `Read(./.env.*)` en `Read(**/.env.*)`
verdwijnen uit alle vier de rol-settings en worden vervangen door de
concrete bestanden die daadwerkelijk geheimen dragen: `.env.local`,
`.env.*.local`, `.env.development`, `.env.dev`, `.env.production`,
`.env.prod`, `.env.staging`, `.env.test`, `.env.secret`, `.env.secrets`.
`Read(./.env)` en `Read(**/.env)` blijven ongewijzigd staan.

Daarmee blijven `.env.example`, `.env.sample`, `.env.template` en
`.env.dist` leesbaar en bewerkbaar, en blijft alles wat conventioneel een
echt ingevuld env-bestand is geblokkeerd.

## Non-goals

- **Geen versoepeling van de overige deny-paden.** `**/secrets/**`,
  `*.pem`, `id_rsa*`, `.credentials.json`, `//home/**/.claude/**`,
  `//var/run/claude/**`, `Bash(env)` en `Bash(printenv *)` blijven exact
  zoals ze zijn.
- **Geen inhoudelijke beoordeling van rol-uitvoer door habitat.** Een
  lengte-ondergrens is een vormeis, geen kwaliteitsoordeel. Of een review
  deugt blijft mensenwerk; dit maakt alleen de meest evidente
  niet-review zichtbaar.
- **Geen wijziging aan de verdict-logica.** PASS/FAIL blijft komen uit het
  `verdict`-veld, en een FAIL stopt de keten zoals nu.

## Impact

- `worker/schemas/{architect,builder,reviewer,security}.json`: één
  `minLength` per bestand.
- `worker/settings/{architect,builder,reviewer,security}.json`: twee
  deny-patronen vervangen door tien concretere.
- `docs/reference/roles.md`: de deny-beschrijving en de uitvoereis
  bijgewerkt.
- **Vereist een nieuwe worker-image-build.** Settings en schema's leven in
  het image (`/opt/habitat/…`), dus een merge naar `main` heeft pas effect
  op runs die het nieuwe image gebruiken.
