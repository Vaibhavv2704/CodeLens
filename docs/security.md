# Security model

Repository content, objectives, manifests, model responses and test output are untrusted.

## Boundaries

1. **Acquisition:** only exact HTTPS GitHub owner/repository URLs. No credentials in URLs, ports,
   query strings, branch paths, arbitrary hosts, shell, git hooks or submodules. The default-branch
   commit is resolved first. Archives are pinned to its SHA. Authorization is sent only to
   `api.github.com`; the only accepted archive redirect is HTTPS `codeload.github.com`.
2. **Extraction:** compressed limit 20 MB, expanded limit 50 MB, 3,000 archive entries, 300 KB per
   file. Traversal, absolute paths, Windows reserved names, alternate data streams, duplicate paths,
   links and special entries are rejected. `tar.extractall` is never used. Snapshots are temporary
   and removed after each review. Large legitimate repositories may be rejected; that is deliberate.
3. **Source:** UTF-8 text only, no binary files, credential-like files excluded, no imports or
   repository subprocesses. Source analysis has a 5 MB budget and 200-finding ceiling. Verification
   re-reads the file/line; a matching quote alone does not prove exploitability. Context-sensitive
   patterns remain potential findings. This is not a comprehensive vulnerability scanner.
4. **Execution:** disabled by default. The only test command is a fixed `python -m pytest` argument
   array. When explicitly enabled it runs inside Docker with no network, read-only root and repository,
   non-root UID, no added capabilities, no-new-privileges, 1 CPU, 256 MB memory, 64 PIDs, 64 MB temporary
   filesystem and 45-second timeout. Output capture is capped at 32 KB. Containers are forcibly removed
   after attempts. No automatic package installation, secret environment variables or Docker socket
   mounts in repository containers. Tests can fail because dependencies are unavailable or writes
   outside `/tmp` are prohibited; those failures are reported.
5. **Model:** optional. Receives only the goal and up to 20 existing evidence-backed findings, not
   the whole repository. Structured outputs can supply explanations/fixes for known issue indexes.
   They cannot supply commands, tools, severity, execution status or test counts. Repository text
   cannot grant permissions. Explanations are displayed as AI analysis. Recognizable token formats
   are redacted before model submission and persistence; redaction is best effort, not a guarantee
   against arbitrary secrets. Do not review confidential repositories with a third-party LLM unless
   your organization permits that data transfer. Private review findings themselves are sensitive.
6. **API:** bounded worker count and pending capacity; optional shared bearer token protects all
   review endpoints. Render generates that token. Configure explicit CORS origins. The health check
   is public. The frontend holds the token in memory only and sends it in headers, including SSE.
   Never set an API token or LLM key in a `VITE_*` variable: those are public build-time values.

## Deployment assumptions

This is a **single-user assessment deployment**, not a multi-tenant SaaS. The shared token grants
access to every stored review. Put it behind TLS and an authenticated gateway, with request-size
and request-rate limits. Do not deploy publicly with an empty token. Restrict database access,
rotate credentials and implement a retention policy for private source excerpts.

Docker is a defense layer, not a perfect hostile-code isolation boundary. Use a dedicated worker VM,
gVisor or a microVM before exposing arbitrary execution to the public. Standard Render deployment and
Compose intentionally keep test execution disabled. Do not enable it by mounting the host Docker socket
into the API container. For an opt-in local demonstration, run the API on the host with Docker available,
build the trusted sandbox image, and set `ENABLE_SANDBOX=true`.

The daemon must use a current patched Docker engine. Logs do not retain raw pytest stdout or HTTP
exception headers. Review objectives and excerpt data may still contain unrecognized secrets; no
automatic redaction system can guarantee otherwise. Configure provider credentials only in environment
variables or ignored `.env` files. No real credentials are included in this repository.
