# Branches: where the latest code lives

| Branch | What it is | Update rule |
|---|---|---|
| `main` | Latest stable CapitUp: v2 UI + side-by-side demo setup + all backend | Only fast-forward from `develop` after a device test |
| `develop` | Day-to-day work | Branch features from here, merge back here |
| `release/v2-modern` | Frozen v2 (modern illustrated UI) | Bug fixes only |
| `release/v1-coversure` | Frozen v1 (CoverSure-style UI) | Bug fixes only |
| `claude/*` | Claude session working branches | Disposable |

Android: debug builds of v2 install as `com.insureiq.insureiq.v2` ("CapitUp v2"), so they sit next to the v1 app.

Update flow: `git checkout develop && git pull` -> work on `feature/<name>` -> merge into `develop` -> test on the phone -> fast-forward `main`.
Tags are blocked from the cloud session, so the `release/*` branches stand in for version tags. Create real tags from your PC: `git tag v0.3-coversure release/v1-coversure && git push origin --tags`.
