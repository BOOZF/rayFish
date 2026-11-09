# Hosting: Vercel frontend, Fly.io backend

Vercel can't run the backend, because simulations are long-running processes that need a permanent disk.
This setup is sized for viewing reports and chatting with the Report Agent. It is **not** sized for running simulations: the last 72-round run used 31–41 GB of memory.

## 1. Backend on Fly.io

Set a unique `app` name in `fly.toml`, then run from the repo root:

```sh
fly auth login
fly apps create <your-app-name>
fly volumes create mirofish_uploads --region sin --size 3 --app <your-app-name>
```

Set secrets. Use a strong password and a random `SECRET_KEY`, because this app can spend your LLM and Zep credits:

```sh
fly secrets set --stage \
  LLM_API_KEY=... LLM_BASE_URL=... LLM_MODEL_NAME=... ZEP_API_KEY=... \
  ADMIN_USERNAME=admin ADMIN_PASSWORD=... \
  SECRET_KEY="$(openssl rand -hex 32)" \
  CORS_ORIGINS=https://<your-vercel-domain>
fly deploy
```

## 2. Copy existing runs to the server (optional)

`backend/uploads/` is gitignored, so runs and reports don't come from GitHub.

```sh
tar -czf /tmp/uploads.tgz -C backend uploads
fly ssh sftp shell    # then: put /tmp/uploads.tgz /tmp/uploads.tgz
fly ssh console -C "tar -xzf /tmp/uploads.tgz -C /app/backend"
fly machine restart
```

## 3. Frontend on Vercel

1. Import the GitHub repo and leave the root directory as the repo root. `vercel.json` sets up the build.
2. Add the environment variable `VITE_API_BASE_URL=https://<your-app-name>.fly.dev`.
3. Deploy. If the Vercel domain differs from `CORS_ORIGINS`, update that secret.

## Limits

- Persona chat only works while a simulation is still running on the server.
- Login attempts aren't rate limited, so the password must be strong.
