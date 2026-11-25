# Deployment

- `bootstrap/`: applied once by hand; filled-in copies are git-ignored
- `argocd/`: the Argo CD project and application, synced by the root app
- `app/`: the IMODAR manifests, synced by Argo CD

A push to `main` builds the changed image, pushes it to GHCR, and commits its tag to `app/kustomization.yaml`. Argo CD then deploys it.

## Bootstrap

Needs a default StorageClass, an ingress controller, and a network plugin that enforces NetworkPolicies. Check `kubectl config current-context` first. Run from the repository root.

1. Argo CD (skip if the cluster has it):

   ```bash
   kubectl apply --server-side -k k8s/bootstrap/argocd
   kubectl -n argocd rollout status deploy/argocd-server
   ```

2. Namespace, secrets and ingress:

   ```bash
   cp k8s/bootstrap/secrets.example.yaml k8s/bootstrap/secrets.yaml    # fill in
   cp k8s/bootstrap/ingress.example.yaml k8s/bootstrap/ingress.yaml    # fill in
   kubectl apply -f k8s/bootstrap/secrets.yaml -f k8s/bootstrap/ingress.yaml
   ```

3. Run the Backend CD and Frontend CD workflows once. GHCR packages start private: make both public, or add a pull secret with a `read:packages` token:

   ```bash
   read -rs GHCR_TOKEN
   kubectl -n imodar create secret docker-registry ghcr-pull --docker-server=ghcr.io \
     --docker-username=<user> --docker-password="$GHCR_TOKEN"
   ```

4. Argo CD root app (the repository must be reachable by Argo CD, which it is while public):

   ```bash
   kubectl apply -f k8s/bootstrap/root-app.yaml
   ```

## Load data

Warehouse (again after every rebuild):

```bash
kubectl apply -f k8s/bootstrap/warehouse-loader.yaml
kubectl -n imodar wait --for=condition=Ready pod/warehouse-loader
kubectl -n imodar cp <path>/imodar.duckdb warehouse-loader:/warehouse/imodar.duckdb.new
kubectl -n imodar exec warehouse-loader -- mv /warehouse/imodar.duckdb.new /warehouse/imodar.duckdb
kubectl -n imodar delete pod warehouse-loader
kubectl -n imodar rollout restart deploy/backend
```

Terminology, from a Qdrant snapshot of `omop_concepts`:

```bash
kubectl -n imodar port-forward svc/qdrant 6340:6333 &
curl -fX POST 'http://localhost:6340/collections/omop_concepts/snapshots/upload?priority=snapshot' \
  -F 'snapshot=@<file>.snapshot'
```

Ollama runs outside this deployment; the cluster must reach `OLLAMA_URL`, with the planner and `bge-m3` models pulled.

## First admin

```bash
kubectl -n imodar exec -it deploy/backend -c backend -- sh -c '
  printf "Email: "; read -r ADMIN_EMAIL; printf "Name: "; read -r ADMIN_NAME
  printf "Password: "; stty -echo; read -r ADMIN_PASSWORD; stty echo; echo
  export ADMIN_EMAIL ADMIN_NAME ADMIN_PASSWORD; python -m imodar.auth.seed_admin'
```

## Roll back

Revert the `deploy:` commit on `main`. Migrations are not reverted.
