# Release Guide

This guide explains how to release new versions of ALMA to PyPI and GitHub.

## Automated Release Process

ALMA uses GitHub Actions to automate package building, testing, and publishing.

### What Gets Automated

1. **Package Building**: Wheels and source distributions for all platforms
2. **PyPI Publishing**: Automatic upload to PyPI on release
3. **Documentation Deployment**: Auto-deploy to GitHub Pages on docs changes
4. **Release Assets**: Packages attached to GitHub releases with checksums

## Creating a New Release

### 1. Prepare the Release

**Update version in `pyproject.toml`**:

```toml
[project]
name = "alma"
version = "0.2.0"  # Update this
```

**Update CHANGELOG.md**:

```markdown
## [0.2.0] - 2025-11-20

### Added
- API key authentication
- OAuth2 support
- New template: microservices-k8s

### Fixed
- Blueprint validation bug
- Rate limiting edge case

### Changed
- Improved LLM response streaming
- Updated documentation
```

**Commit changes**:

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "chore: prepare release v0.2.0"
git push origin main
```

### 2. Create Git Tag

```bash
# Create annotated tag
git tag -a v0.2.0 -m "Release v0.2.0: API Authentication"

# Push tag to GitHub
git push origin v0.2.0
```

### 3. Create GitHub Release

**Option A: Via GitHub Web UI**

1. Go to https://github.com/fabriziosalmi/alma/releases/new
2. Choose tag: `v0.2.0`
3. Release title: `v0.2.0 - API Authentication`
4. Description:
   ```markdown
   ## What's New
   
   - API key authentication
   - OAuth2 support
   - 3 new infrastructure templates
   
   ## Installation
   
   ```bash
   pip install --upgrade alma
   ```
   
   ## Full Changelog
   
   See [CHANGELOG.md](CHANGELOG.md)
   ```
5. Click "Publish release"

**Option B: Via GitHub CLI**

```bash
gh release create v0.2.0 \
  --title "v0.2.0 - API Authentication" \
  --notes-file RELEASE_NOTES.md
```

### 4. Automated Workflows Trigger

Once you publish the release, these workflows run automatically:

**Build Packages** (`build-packages.yml`):
- Builds wheels for Linux, macOS, Windows
- Builds source distribution
- Tests installation on Python 3.10, 3.11, 3.12
- Uploads packages to GitHub release
- Creates SHA256 checksums

**Publish to PyPI** (`publish.yml`):
- Downloads built packages
- Signs packages with Sigstore
- Publishes to PyPI
- Updates GitHub release with signed artifacts

**Deploy Documentation** (`deploy-docs.yml`):
- Builds VitePress documentation
- Deploys to https://fabriziosalmi.github.io/alma/

### 5. Verify Release

**Check PyPI**:
```bash
# Search PyPI
pip search alma

# Install from PyPI
pip install alma==0.2.0

# Verify version
python -c "import alma; print(alma.__version__)"
```

**Check GitHub Release**:
- Visit https://github.com/fabriziosalmi/alma/releases
- Verify packages are attached
- Verify checksums file exists
- Verify Sigstore signatures

**Check Documentation**:
- Visit https://fabriziosalmi.github.io/alma/
- Verify version number updated
- Verify new features documented

## Manual Release (If Automated Fails)

### Build Packages Locally

```bash
# Install build tools
pip install build twine

# Clean old builds
rm -rf dist/ build/ *.egg-info

# Build packages
python -m build

# Check package
twine check dist/*

# List built files
ls -lh dist/
```

### Upload to TestPyPI (Optional)

```bash
# Upload to TestPyPI first
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ alma==0.2.0
```

### Upload to PyPI

```bash
# Upload to PyPI
twine upload dist/*

# Enter credentials or use API token:
# Username: __token__
# Password: pypi-AgEIcHlwaS5vcmc...
```

### Create GitHub Release Manually

```bash
# Create release with packages
gh release create v0.2.0 \
  --title "v0.2.0 - API Authentication" \
  --notes-file RELEASE_NOTES.md \
  dist/*.whl \
  dist/*.tar.gz
```

## Setting Up PyPI Credentials

### Get PyPI API Token

1. Go to https://pypi.org/manage/account/token/
2. Create new API token
3. Scope: Entire account or specific project (alma)
4. Copy the token (starts with `pypi-`)

### Configure GitHub Secrets

1. Go to https://github.com/fabriziosalmi/alma/settings/secrets/actions
2. Click "New repository secret"
3. Name: `PYPI_API_TOKEN`
4. Value: Your PyPI token
5. Click "Add secret"

**For TestPyPI** (optional):
- Secret name: `TEST_PYPI_API_TOKEN`
- Get token from: https://test.pypi.org/manage/account/token/

## Workflow Triggers

### `build-packages.yml`
**Triggers**:
- Git tag push (e.g., `v0.2.0`)
- Pull requests to main (build only, no upload)
- Manual workflow dispatch

**What it does**:
- Builds wheels for Linux, macOS, Windows
- Builds source distribution
- Tests installation across Python versions
- Uploads packages to GitHub release (on tag push)

### `publish.yml`
**Triggers**:
- GitHub release published
- Manual workflow dispatch (with version input)

**What it does**:
- Publishes to PyPI (on release)
- Publishes to TestPyPI (on manual dispatch)
- Signs packages with Sigstore
- Updates GitHub release with signatures

### `deploy-docs.yml`
**Triggers**:
- Push to main branch with docs changes
- Manual workflow dispatch

**What it does**:
- Builds VitePress documentation
- Deploys to GitHub Pages

## Pre-Release Testing

### Test on TestPyPI

```bash
# 1. Update version to pre-release
# pyproject.toml: version = "0.2.0rc1"

# 2. Build and upload to TestPyPI
python -m build
twine upload --repository testpypi dist/*

# 3. Test installation
pip install --index-url https://test.pypi.org/simple/ alma==0.2.0rc1

# 4. Run tests
pytest tests/

# 5. If successful, proceed with real release
```

### Release Candidates

```bash
# Tag as release candidate
git tag -a v0.2.0-rc1 -m "Release candidate 0.2.0-rc1"
git push origin v0.2.0-rc1

# Create pre-release on GitHub
gh release create v0.2.0-rc1 \
  --title "v0.2.0-rc1 (Release Candidate)" \
  --notes "Testing release candidate" \
  --prerelease
```

## Versioning Scheme

ALMA follows [Semantic Versioning](https://semver.org/):

**Format**: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes (e.g., 1.0.0 → 2.0.0)
- **MINOR**: New features, backward compatible (e.g., 0.1.0 → 0.2.0)
- **PATCH**: Bug fixes, backward compatible (e.g., 0.1.0 → 0.1.1)

**Pre-release versions**:
- `0.2.0-alpha.1` - Alpha release
- `0.2.0-beta.1` - Beta release
- `0.2.0-rc.1` - Release candidate

## Post-Release Checklist

After releasing:

- [ ] Verify package on PyPI: https://pypi.org/project/alma/
- [ ] Verify GitHub release: https://github.com/fabriziosalmi/alma/releases
- [ ] Verify documentation deployed: https://fabriziosalmi.github.io/alma/
- [ ] Test installation: `pip install --upgrade alma`
- [ ] Update project README if needed
- [ ] Announce on:
  - [ ] GitHub Discussions
  - [ ] Twitter/Social media
  - [ ] Community channels
- [ ] Monitor issue tracker for bug reports
- [ ] Prepare hotfix branch if critical bugs found

## Hotfix Releases

For critical bugs in production:

```bash
# 1. Create hotfix branch from tag
git checkout -b hotfix/0.2.1 v0.2.0

# 2. Fix the bug
# ... make changes ...

# 3. Update version
# pyproject.toml: version = "0.2.1"

# 4. Commit and tag
git commit -am "fix: critical bug in rate limiter"
git tag -a v0.2.1 -m "Hotfix: Rate limiter bug"

# 5. Merge back
git checkout main
git merge hotfix/0.2.1
git push origin main
git push origin v0.2.1

# 6. Create GitHub release
gh release create v0.2.1 --title "v0.2.1 (Hotfix)" --notes "Critical bug fix"
```

## Troubleshooting

### Build fails on GitHub Actions

**Check workflow logs**:
```bash
gh run list --workflow=publish.yml
gh run view <run-id>
```

**Common issues**:
- Missing dependencies in `pyproject.toml`
- Test failures
- Linting errors

### PyPI upload fails

**Authentication error**:
- Verify `PYPI_API_TOKEN` secret is set correctly
- Check token hasn't expired
- Ensure token has correct scope

**Version conflict**:
- Version already exists on PyPI
- Bump version number
- Cannot re-upload same version

### Documentation not deploying

**Check GitHub Pages settings**:
1. Go to Settings → Pages
2. Source should be "GitHub Actions"
3. Check workflow runs: `gh run list --workflow=deploy-docs.yml`

## Resources

- **PyPI Package**: https://pypi.org/project/alma/
- **GitHub Releases**: https://github.com/fabriziosalmi/alma/releases
- **Documentation**: https://fabriziosalmi.github.io/alma/
- **Packaging Guide**: https://packaging.python.org/
- **Semantic Versioning**: https://semver.org/
