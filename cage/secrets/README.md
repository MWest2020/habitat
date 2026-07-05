# Kooi-secrets (SOPS + age)

Secrets gaan **versleuteld** in git (`*.enc.yaml`) en worden pas op de
orchestrator-host gedecrypt bij het uitrollen. De age-privékey verlaat die host
nooit. De `.example.yaml`-bestanden hier zijn templates zonder echte waarden.

## Bootstrap (eenmalig, door Mark op de orchestrator-host)

```bash
# 1. Genereer de cluster-age-key (privé blijft hier staan)
age-keygen -o ~/.config/sops/age/habitat.txt
#    kopieer de "public key: age1..." regel in cage/secrets/.sops.yaml (age:)

# 2. Claude-auth (sub-first): maak claude-credentials uit je subscription-credentials
kubectl -n agents create secret generic claude-credentials \
  --from-file=credentials.json="$HOME/.claude/.credentials.json" \
  --dry-run=client -o yaml > claude-credentials.enc.yaml
sops -e -i claude-credentials.enc.yaml     # versleutelt alleen data/stringData

# 3. Per node een PAT-secret (pat-node-01.enc.yaml, pat-node-02.enc.yaml, ...)
```

## Uitrollen (decrypt-at-apply, geen in-cluster decryptie)

```bash
export SOPS_AGE_KEY_FILE=~/.config/sops/age/habitat.txt
sops -d claude-credentials.enc.yaml | kubectl apply -f -
sops -d pat-node-01.enc.yaml        | kubectl apply -f -
```

## Regels

- Commit **nooit** een onversleutelde `*.enc.yaml` of een `.env` met echte waarden.
  De `.gitignore` blokkeert `*.dec.yaml`/`*-decrypted.yaml`; de `.example.yaml`'s
  bevatten alleen placeholders en mogen wel mee.
- Node intrekken = PAT intrekken op GitHub + het bijbehorende `pat-node-<n>` secret
  verwijderen (`kubectl -n agents delete secret pat-node-<n>`).
