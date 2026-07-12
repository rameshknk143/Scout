# Dependency & Supply-Chain Review

Source: `web/package-lock.json` (lockfileVersion 3, exact) and `api/requirements.txt` (floors).

## Web (exact, from lockfile)
| Package | Version | Note |
|---|---|---|
| next | 16.2.10 | current; no known advisories at audit date |
| react / react-dom | 19.2.4 | current |
| @react-three/fiber | 9.6.1 | current |
| @react-three/drei | 10.7.7 | current |
| three | 0.185.1 | current |
| framer-motion | 12.42.2 | current |
| recharts | 3.9.2 | current |
| clsx | 2.1.1 | trivial |
| gsap | 3.15.0 | current |

- Lockfile is committed → web builds are **reproducible**. ✅
- No obviously abandoned/typosquat packages in the direct set. Transitive tree not individually audited (no `npm audit` run here; recommend running it in CI — see remediation).

## API (floors only — `>=`, from requirements.txt)
| Package | Pin | Risk |
|---|---|---|
| fastapi | >=0.115.0 | unpinned upper |
| uvicorn | >=0.30.6 | unpinned upper |
| psycopg2-binary | >=2.9.9 | unpinned upper |
| pandas | >=2.2.2 | unpinned upper |
| pydantic | >=2.9.2 | unpinned upper |
| requests | >=2.32.5 | unpinned upper (≥2.32 already includes the CVE-2024-35195 fix) |

- **No lockfile / hash pinning for Python** → a fresh Render build can pull newer releases than tested → **non-reproducible builds + supply-chain drift** window. Finding **SEC-07**.
- No known-vulnerable pinned version identified; the risk is *future* drift, not a current CVE.

## Recommendation
- Add `npm audit --production` (web) and `pip-audit` (api) to CI; pin the Python deps with a `requirements.lock`/hashes or `uv`/`pip-tools`. See remediation-plan.md.
