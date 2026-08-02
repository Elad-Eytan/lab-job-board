- How many CRITICAL CVEs did you find in total across all images?

26 from lab-job-board-applications-service
39 from postgres:16-alpine
0 from lab-job-board-frontend
13 from lab-job-board-jobs-service
0 from lab-job-board-nginx

in total: 78 CVEs Found across all images
- Which image has the most vulnerabilities?

postgres:16-alpine with 39 CVEs

- Pick **one** CRITICAL CVE and explain: (a) what it is, (b) which package it affects, (c) what the fix/mitigation is.

in the lab-job-board-applications-service image there is 1 critical exploit found:

in  tar (package.json)  CVE-2026-59873  CRITICAL │ 6.2.1 7.5.19  tar: node-tar: Denial of Service via crafted gzip bomb https://avd.aquasec.com/nvd/cve-2026-59873

it is an exploit that will allow a Denial of Service via crafted gzip bomb, it means that it is vulnerable to zip bomb that are also known as a decompression bomb or zip of death, it is a malicious archive file designed to crash, freeze, or disable the system or application that attempts to unpack it.

it affects the tar function.

---

Before and After:

Before:

REPOSITORY                                          TAG                                                                           SIZE
lab-job-board-jobs-service                          latest                                                                        274MB
lab-job-board-nginx                                 latest                                                                        97.7MB
lab-job-board-frontend                              latest                                                                        98MB
lab-job-board-applications-service                  latest                                                                        223MB

After:

REPOSITORY                                          TAG                                                                           SIZE
lab-job-board-jobs-service                          latest                                                                        274MB
lab-job-board-nginx                                 latest                                                                        97.7MB
lab-job-board-frontend                              latest                                                                        98MB
lab-job-board-applications-service                  latest                                                                        223MB

Nothing really changed since most of the optimizations were implemented in the original repo.


---

# explain why committing `.env` to git is a security risk and what tools exist to prevent it (e.g., `git-secrets`, `truffleHog`, GitHub secret scanning).

Committing a .env file to a Git repository will leak the credential, it is a very problematic thing since Git remembers everything.
Also, there are automated bot harvesting that constantly monitore public repositories.
Even in private repositories, committing credentials grants access to every developer, contractor, or CI/CD integration with read permissions to the repo. This violates the Principle of Least Privilege.

Tools to Prevent & Detect Secret Leaks:

| Stage | Tool | How It Works | Primary Use Case |
| :--- | :--- | :--- | :--- |
| **Local / Pre-Commit** | **`.gitignore`** | Native Git feature that prevents untracked `.env` files from being staged. | Baseline defense for every repository. |
| **Local / Pre-Commit** | **`git-secrets`** | AWS-maintained tool that scans commits, staged files, and messages to block commits matching defined regex patterns. | Catching AWS access keys and custom patterns locally. |
| **Local / Pre-Commit** | **`detect-secrets`** | Yelp-maintained tool using enterprise heuristics and high-entropy detection to flag potential secrets in code diffs. | Catching secrets locally before `git commit` succeeds. |
| **CI / Repository** | **`TruffleHog`** | Deep scanner that searches commit history, branches, and file systems using detectors and entropy checks; actively verifies if detected secrets are live. | CI pipeline enforcement, historical repo audits, live credential validation. |
| **CI / Repository** | **`Gitleaks`** | Fast, lightweight SAST tool designed to detect and prevent unencrypted secrets in git repositories and developer workflows. | Fast CI pipeline gates and automated workflow checks. |
| **Platform Level** | **GitHub Secret Scanning & Push Protection** | Server-side scanner that inspects code pushes for known partner secret formats and blocks the push if a credential is detected. | Automated defense on public and enterprise GitHub repositories. |


---


#### 2.3 – Service restart policy and dependency ordering

Draw the dependency graph as ASCII art:

                         ┌─────────────────┐
                         │     Browser     │
                         └────────┬────────┘
                                  │ HTTP :80
                                  ▼
                         ┌─────────────────┐
                         │  nginx-proxy    │
                         │ Reverse proxy   │
                         └───┬─────────┬───┘
                             │         │
               /             │         │ /api/*
               ▼             │         ▼
      ┌─────────────────┐    │  ┌────────────────────────┐
      │    frontend     │    │  │                        │
      │ React + Nginx   │    │  │                        │
      └─────────────────┘    │  │                        │
                             │  │                        │
                /api/jobs/*  │  │ /api/applications/*
                             ▼  ▼
                   ┌───────────────┐
                   │ jobs-service  │
                   │   FastAPI     │
                   │    :8000      │
                   └───────┬───────┘
                           │
                           │ DATABASE_URL
                           ▼
                    ┌─────────────┐
                    │ PostgreSQL  │
                    │    :5432    │
                    └─────────────┘
                           ▲
                           │ DATABASE_URL
                           │
              ┌────────────┴────────────┐
              │ applications-service    │
              │ Node.js + Express :3001 │
              └─────────────────────────┘

Explain what `condition: service_healthy` does vs `condition: service_started`

condition: service_started: Means that the container booted up successfully, the app still has not been started
condition: service_healthy: Means that the container started the app and is now functional

What happens if postgres crashes after the other services are running? Verify with: `docker compose stop postgres`

The entire app crashed, everything relies on the DB being up

Explain the difference between `docker compose down`, `docker compose down -v`, and `docker compose stop`. When would you use each?

The diffrence in between docker compose down, docker compose down -v, and docker compose stop is that compose stop will only stop the running container and will not delete them.
docker compose down will stop and remove the containers and networks but will keep the volumes.
docker compose down -v will also delete the volumes.


- Where on the host machine is the data actually stored?

I use Windows, and the volumes are stored in an emulated path that exists on my PC in this location:
\\wsl.localhost\docker-desktop\mnt\docker-desktop-disk\data\docker\volumes\jobboard-postgres-data

in the emulated space it is stored here:
/var/lib/docker/volumes/jobboard-postgres-data/_data

- What is the difference between a **named volume** (`postgres-data:`) and a **bind mount** (`./data:/var/lib/postgresql/data`)?

Named volumes are managed by Docker and can be called by their name, they are also stored in Docker's private folders. 
A bind mount is basically mounting a folder in your host OS and having full control of where it is stored.

- When would you prefer each approach in production?

It is a trick question, it really depends on your needs. If you need other programs to access the same folder, you should use a bind mount since it is easier to track and know where it is mounted, for example you can use it for Configuration files.

If you need the flexibility of using a named volume, you should use that, it is recommended for use in storing DB since it is a continer spesific data that will only be seen by it.


**Restore procedure**

docker compose up postgres
docker cp "C:\Users\Elad Eytan Feldman\Desktop\K8S project\lab-job-board\backup_20260802_183125.sql" jobboard-db:/var/lib/postgresql/data
docker exec -it jobboard-db psql -U postgres -d backup_20260802_183125.sql

TEST