# Deployment and publishing

## Current verification boundary

Local Python execution, SQLite persistence, React production assets and a live public GitHub review
are tested. Docker, PostgreSQL, live LLM/private-repository access and production hosting require the
services below. Configuration files alone are not a verified deployment.

## Local Docker Compose

1. Install/start Docker Desktop (Linux containers).
2. Copy root `.env.example` to `.env`; set a URL-safe random `POSTGRES_PASSWORD`.
3. Run `docker compose config` then `docker compose up --build`.
4. Open `http://localhost:5173` and verify `http://localhost:8000/api/health`.

Compose starts PostgreSQL, the backend and the frontend. It does not mount the Docker socket or enable
repository execution. The database volume persists history. Deleting that volume deletes review data.

## Opt-in local repository tests

```sh
docker build -t review-sandbox:local -f backend/Dockerfile.sandbox backend
```

Run the backend directly on the host with `ENABLE_SANDBOX=true`; the Docker CLI must be on PATH.
Keep `SANDBOX_IMAGE=review-sandbox:local`. Verify the good and failing synthetic repositories:

```sh
python scripts/review.py https://github.com/synthetic/python_good --fixture python_good
python scripts/review.py https://github.com/synthetic/python_failing_tests --fixture python_failing_tests
```

Only code inside the restricted container runs. Missing third-party dependencies produce honest test
failures. Do not install dependencies from untrusted requirements on the host or grant the container networking.

## Database: Supabase or PostgreSQL

Create a project/database, then set `DATABASE_URL` to the provider's SQLAlchemy-compatible connection
URL (use `postgresql+psycopg://...`, percent-encode password characters, and `sslmode=require` where needed).
Use a dedicated database/schema credential. The initial tables are created by SQLAlchemy at startup.
Do not use the Supabase public client key as a database password. This app connects directly with psycopg.
No browser database credentials are needed. Plan migrations/backups before maintaining a production service.

## Backend: Render

1. Push this repository to your GitHub account.
2. Create a Render Blueprint using `render.yaml`, or a Docker web service with Dockerfile
   `backend/Dockerfile` and build context `backend`.
3. Supply `DATABASE_URL`, an exact production `CORS_ORIGINS`, and optional `OPENAI_API_KEY` / `GITHUB_TOKEN`.
   The blueprint generates `API_TOKEN`; keep it private. Set `LLM_MODEL` if your account needs another model.
4. Keep `ENABLE_SANDBOX=false`. Use one instance/process with the current in-process queue.
5. Wait for successful build/start and check `https://<backend-host>/api/health` returns HTTP 200
   with `{"status":"healthy"}`. Submit a review and inspect its report before calling deployment verified.

Render does not provide a Docker daemon for arbitrary nested test containers. An external isolated worker
is a future enhancement, not a capability this deployment claims to provide.

## Frontend: Vercel

1. Import the same GitHub repository, choosing `frontend` as the root directory.
2. Select Vite, Node 22, install `pnpm install --frozen-lockfile`, build `pnpm build`, output `dist`.
3. Set `VITE_API_URL=https://<backend-host>`. Never put API/LLM/database secrets in build variables.
4. Deploy. Update backend `CORS_ORIGINS` to this exact frontend origin and restart the backend.
5. Enter the backend bearer token in the dashboard's API connection settings. Verify a review reaches
   a report, reload its `?review=<id>` link, and confirm history and JSON export work.

Use TLS and an authenticated gateway if sharing widely. A shared bearer token is not multi-user authorization.

## GitHub publishing when authentication is unavailable

For this delivery, a Windows-user credential was found, but automatic approval review blocked the upload
until explicit approval of the destination. No GitHub repository has been created by this run. The commands
below are manual alternatives; they have not been executed successfully here.

The requested repository name is `agentic-github-code-reviewer`. From this project root, after installing
the GitHub CLI and Git on PATH:

```sh
gh auth login --hostname github.com --git-protocol https --web
gh repo create agentic-github-code-reviewer --private --source=. --remote=origin --push
git remote -v
git status
```

These commands create a private repository to avoid publishing the take-home before review. Share it
with your interviewer or change visibility explicitly. If you create an empty repository through the web UI:

```sh
git remote add origin https://github.com/YOUR_USERNAME/agentic-github-code-reviewer.git
git push -u origin main
```

Do not overwrite an existing remote or force-push. If `origin` already exists, inspect it first. No GitHub
URL is presented as a created repository until a successful push is verified.

On this Windows workspace, Git was initialized by the sandbox account. If your own terminal reports
`dubious ownership`, trust only this exact directory before using the manual commands:

```powershell
git config --global --add safe.directory 'C:/Users/vaibh/Desktop/github analyse agent'
```
