# Kooi-secrets (SOPS + age)

Secrets gaan **versleuteld** in git (`*.enc.yaml`) en worden pas op de
orchestrator-host gedecrypt bij het uitrollen. De age-privékey verlaat die host
nooit. De `.example.yaml`-bestanden hier zijn templates zonder echte waarden.

## Bootstrap (eenmalig, door Mark op de orchestrator-host)

```bash
# 1. Genereer de cluster-age-key (privé blijft hier staan)
age-keygen -o ~/.config/sops/age/habitat.txt
#    kopieer de "public key: age1..." regel in cage/secrets/.sops.yaml (age:)

# 2. Per node een PAT-secret (pat-node-01.enc.yaml, pat-node-02.enc.yaml, ...)
```

**Uitzondering — `claude-credentials`**: dat secret gaat níet via SOPS in git.
De subscription-token verloopt na ~8u; `dispatch/dispatch.sh` synct het secret
bij elke dispatch vanaf `~/.claude/.credentials.json` op de orchestrator-host
(zie add-dispatch, taak 4.2). SOPS-in-git is voor at-rest-secrets zoals PAT's.

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
