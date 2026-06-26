# Packaging

Distribution recipes for Pcreative Studio. CI (GitHub Actions) builds
AppImage / .deb / .rpm / .app automatically on tag pushes. The
files here are for **manual** distribution channels that CI can't
or shouldn't drive directly.

## AUR (Arch User Repository)

Two PKGBUILDs — pick one when uploading to AUR:

| Package | Source | Audience |
|---|---|---|
| [`aur/themeforge`](aur/themeforge/PKGBUILD) | Tagged release tarball | Most users — installs the latest stable version |
| [`aur/themeforge-git`](aur/themeforge-git/PKGBUILD) | Git tip | Bleeding edge — installs whatever's on `main` |

### Publishing to AUR

Prerequisites:

- AUR account at <https://aur.archlinux.org/> with your SSH key
  registered.
- A local clone of the AUR repo: `git clone ssh://aur@aur.archlinux.org/themeforge.git`
  (or `themeforge-git`).

Steps (stable version, after tagging `v0.1.0`):

```bash
# 1. Update version + hash
cd packaging/aur/themeforge
# Edit PKGBUILD: bump pkgver to match the git tag
updpkgsums              # recomputes sha256sums from the source

# 2. Test locally
makepkg -si

# 3. Copy into your AUR clone and push
cp PKGBUILD ~/aur-clones/themeforge/
cd ~/aur-clones/themeforge/
makepkg --printsrcinfo > .SRCINFO
git add PKGBUILD .SRCINFO
git commit -m "0.1.0-1"
git push
```

For the `-git` flavour, the version is auto-computed at build
time so the PKGBUILD itself only needs commits when you change
metadata (deps, build steps).

### Local install without publishing

If you just want to install on your own machine:

```bash
cd packaging/aur/themeforge-git
makepkg -si
```

## Future formats (ROADMAP)

- **Flatpak** — sandboxed, distro-agnostic. Higher cost than AppImage
  (FlatHub review + manifests). Worth doing once we have telemetry
  showing demand.
- **Snap** — Canonical's format. Lower priority since most desktop
  Linux users are off Ubuntu these days, and snap auto-updates are
  contentious.
- **Nix flake** — for the NixOS minority. PR-friendly low effort.
