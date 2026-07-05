## 1. Namespace + Kustomize-base

- [ ] 1.1 `namespace: agents` als Kustomize-base (expliciet, geen Helm)
- [ ] 1.2 `kustomization.yaml` die alle onderdelen van deze change bundelt

## 2. Egress-proxy (Squid)

- [ ] 2.1 Squid-deployment + service (poort 3128) in `agents`
- [ ] 2.2 Statische domein-allowlist: `.anthropic.com`, github-HTTPS, `.pypi.org`, `.pythonhosted.org`, `.npmjs.org`
- [ ] 2.3 Access-log aan (egress-audit); config als ConfigMap, diffbaar

## 3. NetworkPolicy

- [ ] 3.1 Default-deny egress voor pods in `agents`
- [ ] 3.2 Allow egress naar CoreDNS (53) via namespace+pod-selector (niet ClusterIP)
- [ ] 3.3 Allow egress naar de proxy-pod (3128); niets anders
- [ ] 3.4 Egress-test: allowlist-domein bereikbaar, direct extern adres geweigerd, DNS werkt

## 4. RBAC

- [ ] 4.1 ServiceAccount per rol (builder/reviewer/security), minimaal
- [ ] 4.2 Role/RoleBinding: rol-SA mag alleen API-key-secret + eigen node-PAT-secret referencen
- [ ] 4.3 Orchestrator-SA: Jobs CRUD in `agents` + logs lezen, verder niets
- [ ] 4.4 RBAC-test: orchestrator-SA kan geen vreemd secret / andere namespace

## 5. SOPS+age

- [ ] 5.1 `.sops.yaml` met creation-rules (encrypt alleen `data`/`stringData`)
- [ ] 5.2 Secret-templates: `anthropic-api-key`, `pat-node-<n>` (versleuteld)
- [ ] 5.3 Documenteer decrypt-at-apply-stap (`sops -d | kubectl apply -f -`), age-key alleen op orchestrator-host
- [ ] 5.4 Secret-mounts: node-PAT read-only mode 0400; `ANTHROPIC_API_KEY` via `secretKeyRef`

## 6. Verificatie (DoD)

- [ ] 6.1 `kubectl apply -k` zet namespace + proxy + policies foutloos
- [ ] 6.2 Egress-test slaagt (allowlist ja, rest nee, DNS ja)
- [ ] 6.3 RBAC-test slaagt (orchestrator-SA strak begrensd)
