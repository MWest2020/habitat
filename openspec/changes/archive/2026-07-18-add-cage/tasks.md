## 1. Namespace + Kustomize-base

- [x] 1.1 `namespace: agents` als Kustomize-base (expliciet, geen Helm)
- [x] 1.2 `kustomization.yaml` die alle onderdelen van deze change bundelt

## 2. Egress-policy (Cilium toFQDNs)

- [x] 2.1 Namespace-brede default-deny egress (k8s NetworkPolicy, `podSelector: {}`)
- [x] 2.2 CiliumNetworkPolicy `worker-egress`: DNS naar kube-dns + `toFQDNs`-allowlist (anthropic, github, pypi, npm) over 443
- [x] 2.3 Egress-audit via Hubble (draait al in het cluster; geen extra component)
- [x] 2.4 Egress-test: allowlist-domein 200/404, geblokkeerd domein time-out (curl-exit 28), DNS werkt

## 3. RBAC

- [x] 3.1 ServiceAccount per rol (builder/reviewer/security), `automountServiceAccountToken: false`
- [x] 3.2 Orchestrator-SA + Role/RoleBinding: Jobs CRUD in `agents` + pods/log lezen, verder niets
- [x] 3.3 RBAC-test (`auth can-i` als orchestrator-SA): jobs/logs ja; secrets/kube-system/andere-ns/cluster nee

## 4. SOPS+age (bootstrap door Mark)

- [x] 4.1 `.sops.yaml` met creation-rules (encrypt alleen `data`/`stringData`)
- [x] 4.2 Secret-templates: `anthropic-api-key`, `pat-node-<n>` (`.example.yaml`)
- [x] 4.3 Bootstrap-README: age-key genereren, `.enc.yaml` maken, decrypt-at-apply
- [x] 4.4 Age-key + SOPS-secrets aangemaakt en uitgerold (2026-07-18): keypair gegenereerd op de
      orchestrator-host (nu ubuntu@cp-01, `~/.config/sops/age/habitat.txt`, mode 600; privé-key
      heeft die host nooit verlaten), publieke key in `.sops.yaml`, bestaande `pat-node-01`
      versleuteld naar `pat-node-01.enc.yaml` (op cp-01 zelf; plaintext nooit buiten die host),
      decrypt-at-apply live bewezen (`sops -d | kubectl apply` → configured, label erbij).
      Rest-punten: nieuwe PAT's (node-02/03) zijn GitHub-UI-only — pas nodig zodra die nodes
      workers draaien; `claude-credentials` bewust niet in SOPS (sync-at-dispatch, zie add-dispatch 4.2).

## 5. Verificatie (DoD)

- [x] 5.1 `kubectl apply -k cage/` zet namespace + policies + RBAC foutloos (live)
- [x] 5.2 Egress-test slaagt (allowlist ja, rest nee, DNS ja)
- [x] 5.3 RBAC-test slaagt (orchestrator-SA strak begrensd)
