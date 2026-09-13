# Kubernetes deployment

The Helm chart in `helm/` is the single source of truth. It targets the
**shaolin-temple** home lab (k3s v1.24 on `k8s-a`, Traefik 2.6, cert-manager
1.9), and is deployed at <https://flashcards.jetli.kicks-ass.net>.

```
                          flashcards.jetli.kicks-ass.net
                                       |
                                  Traefik (TLS)
                        /              |               \
              PathPrefix(/api)   PathPrefix(/admin)   PathPrefix(/)
              /static /media            |                  |
                        \               |                 SPA
                         \              |             (nginx, static)
                          +---- backend (gunicorn) ----+
                                       |
                                  MySQL 8.0.28
                              (StatefulSet + PVC)
```

One hostname serves both the SPA and the API. That is deliberate: same origin
means the session and CSRF cookies are same-site, so there is no cross-origin
cookie configuration to get wrong.

## Deploy

```sh
# 1. Build and push. API_BASE_URL is compiled into the frontend bundle, so it
#    must be supplied at build time -- it cannot be changed later by an env var.
REG=repo.jetli.kicks-ass.net
TAG=1.0.0
docker build -t $REG/yoga-flashcards-backend:$TAG ./backend
docker build -f frontend/Dockerfile.prod \
  --build-arg API_BASE_URL=https://flashcards.jetli.kicks-ass.net \
  -t $REG/yoga-flashcards-frontend:$TAG ./frontend
docker push $REG/yoga-flashcards-backend:$TAG
docker push $REG/yoga-flashcards-frontend:$TAG

# 2. Install or upgrade.
helm upgrade --install yoga-flashcards ./k8s/helm \
  --namespace yoga-flashcards --create-namespace --wait --timeout 8m
```

Bump `image.tag` (or `--set image.tag=`) for a new release; it defaults to the
chart's `appVersion`.

## Plain manifests

The lab mostly uses `kubectl apply -f` rather than Helm. To get a flat set of
manifests out of the chart without a second copy to keep in sync:

```sh
./k8s/render-manifests.sh            # writes k8s/manifests/ (gitignored)
kubectl apply -f k8s/manifests/
```

The rendered output contains a generated Secret, which is why it is not
committed. Keeping the chart as the only source avoids the drift that comes with
maintaining parallel copies.

## What the chart creates

| Resource | Notes |
|---|---|
| `Secret` | `DJANGO_SECRET_KEY`, `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD`, generated once and preserved across upgrades |
| `ConfigMap` | Non-secret Django settings, including the CSRF/host configuration |
| `StatefulSet` + PVC | MySQL, 8Gi on `local-path` |
| `Deployment` (backend) | gunicorn, with a `migrate` init container |
| PVC (media) | Uploaded card images, 2Gi, `helm.sh/resource-policy: keep` |
| `Deployment` (frontend) | nginx serving the built SPA |
| 2x `Ingress` | Port 80 redirects to HTTPS; port 443 path-routes to backend/frontend |
| `Middleware` | `redirectScheme`, on the legacy `traefik.containo.us` API group |
| `Issuer` | Per-namespace cert-manager Issuer (there is no ClusterIssuer here) |
| `Job` | Seeds 19 starter flashcards, **post-install only** |

## Cluster-specific choices

These are not portable defaults -- they are what this cluster requires.

- **`kubernetes.io/ingress.class: traefik`**, not `spec.ingressClassName`. No
  `IngressClass` resources exist on this k3s v1.24 node.
- **`traefik.containo.us/v1alpha1`** for the Middleware. The post-rename
  `traefik.io/v1alpha1` group does not resolve on Traefik 2.6.
- **`cert-manager.io/issuer`** (singular) pointing at a namespaced `Issuer`.
  Every namespace here carries its own; there is no ClusterIssuer to borrow.
- **`mysql:8.0.28`.** MySQL 8.0.3x images moved to an Oracle Linux 9 base whose
  glibc needs the x86-64-v2 CPU baseline. `k8s-a` does not meet it and newer
  images die immediately with `Fatal glibc error: CPU does not support
  x86-64-v2`.
- **`Recreate` strategy on the backend.** The media PVC is ReadWriteOnce on
  node-local storage, so a rolling update would deadlock waiting for a volume
  the outgoing pod still holds.
- **An explicit `Host` header on the backend probes.** kubelet addresses the pod
  IP, which is not in `ALLOWED_HOSTS`; without this every probe gets Django's
  `DisallowedHost` 400 and the pod never goes Ready.
- **`USE_X_FORWARDED_PROTO`.** Traefik terminates TLS and forwards plain HTTP.
  Without it Django builds `http://` URLs and the CSRF origin check compares the
  wrong scheme.

## Card image bot

`manage.py generate_card_images` runs on a schedule as the
`RELEASE-image-bot` CronJob: it queues an image for any card that has never had
one, then generates up to `imageBot.limit` of them.

**The CronJob is only created when an OpenRouter key is reachable.** Without one
the chart skips it, rather than scheduling a job that fails every ten minutes.

Set the key once, and upgrades keep it:

```sh
kubectl -n yoga-flashcards patch secret yoga-flashcards-secrets \
  -p '{"stringData":{"OPENROUTER_API_KEY":"sk-or-..."}}'
helm upgrade yoga-flashcards ./k8s/helm -n yoga-flashcards   # creates the CronJob
```

Or pass it at install time with `--set openrouter.apiKey=sk-or-...`, or point at
a Secret you manage with `--set openrouter.existingSecret=my-secret`.

Only the bot pod gets the key. The web pods never call OpenRouter -- the API
queues work, it does not generate inline -- so they have no reason to hold it.

```sh
# Watch it
kubectl -n yoga-flashcards get cronjob,jobs
kubectl -n yoga-flashcards logs -l app.kubernetes.io/component=image-bot --tail=50

# Run one now without waiting for the schedule
kubectl -n yoga-flashcards create job --from=cronjob/yoga-flashcards-image-bot bot-manual

# Pause it
helm upgrade yoga-flashcards ./k8s/helm -n yoga-flashcards --set imageBot.enabled=false
```

**This spends money.** Every generation is billed by OpenRouter (roughly
$0.03/MP on FLUX.2 Pro). `imageBot.limit` is the throttle, `concurrencyPolicy:
Forbid` stops a slow run overlapping the next tick, and the app caps attempts
per image. Start with a low limit and a wide schedule.

The bot mounts the same media PVC as the backend so generated images land where
`/media/` is served from. That volume is ReadWriteOnce on node-local storage,
which is fine here because the cluster is a single node -- on a multi-node
cluster the bot and the backend would need to be pinned together, or the volume
moved to ReadWriteMany.

## Seed data

The post-install Job loads the 19 starter flashcards and the test accounts. It
**never runs on upgrade**: `seed_initial_data` deletes every flashcard and tag
before importing, so running it against a populated database would destroy
content. To re-run it deliberately:

```sh
kubectl -n yoga-flashcards create job --from=job/yoga-flashcards-seed seed-rerun
```

Disable it entirely with `--set seed.enabled=false`.

**Change the seeded `admin@example.com` password immediately after a real
install.**

## Operating

```sh
kubectl -n yoga-flashcards get pods,svc,ingress,certificate
kubectl -n yoga-flashcards logs deploy/yoga-flashcards-backend -c backend --tail=50
kubectl -n yoga-flashcards logs deploy/yoga-flashcards-backend -c migrate    # migrations
kubectl -n yoga-flashcards exec -it deploy/yoga-flashcards-backend -c backend -- python manage.py shell

# Verify without relying on the NAT hairpin
curl -s --resolve flashcards.jetli.kicks-ass.net:443:10.10.55.222 \
  https://flashcards.jetli.kicks-ass.net/api/health/
```

Back up the generated Secret -- `helm uninstall` deletes it, and losing
`MYSQL_PASSWORD` locks the app out of its own database:

```sh
kubectl -n yoga-flashcards get secret yoga-flashcards-secrets -o yaml > secret-backup.yaml
```

The media PVC is annotated `helm.sh/resource-policy: keep`, so uploaded images
survive an uninstall. The MySQL PVC comes from a `volumeClaimTemplate` and also
outlives the release.
