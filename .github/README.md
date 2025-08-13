# GitHub Actions Security Guidelines

## 🔒 SHA-Pinning Requirements

**CRITICAL SECURITY REQUIREMENT**: All GitHub Actions in this repository MUST use SHA-pinned versions to prevent supply chain attacks.

### Why SHA-Pinning?

GitHub Actions referenced by tags (like `@v4` or `@main`) are **mutable** - maintainers can move these tags to different commits at any time. This creates a security vulnerability where:
1. A compromised maintainer account could inject malicious code
2. The malicious code would automatically run in your CI/CD pipeline 
3. This could leak secrets, modify code, or compromise deployments

### ✅ Correct Usage (SHA-Pinned)

```yaml
- uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4.1.1
- uses: actions/setup-python@0a5c61591373683505ea898e09a3ea4f39ef2b9c  # v5.0.0
- uses: actions/cache@0400d5f644dc74513175e3cd8d07132dd4860809  # v4.2.4
```

### ❌ Incorrect Usage (Vulnerable)

```yaml
- uses: actions/checkout@v4            # Mutable tag - security risk!
- uses: actions/setup-python@main      # Branch reference - security risk!
- uses: actions/cache@latest           # Tag reference - security risk!
```

## Finding the Correct SHA

### Method 1: GitHub Releases Page
1. Navigate to the action's repository (e.g., https://github.com/actions/checkout)
2. Click on "Releases"
3. Find the release you want (e.g., v4.1.1)
4. The release notes will show the full commit SHA

### Method 2: GitHub API
```bash
# Get SHA for a specific tag
gh api repos/actions/checkout/git/refs/tags/v4.1.1 --jq '.object.sha'

# Verify a SHA is valid
gh api repos/actions/checkout/commits/b4ffde65f46336ab88eb53be808477a3936bae11
```

### Method 3: Git Commands
```bash
# Clone the action repository
git clone https://github.com/actions/checkout.git
cd checkout

# Get SHA for a tag
git rev-list -n 1 v4.1.1
```

## Important Notes

### Always Add Version Comments
For maintainability, always add a comment with the version number:
```yaml
uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4.1.1
```

### Handling Deprecation Warnings
GitHub will automatically fail workflows that use deprecated action versions. When you see:
```
This request has been automatically failed because it uses a deprecated version of `actions/cache`
```

You must:
1. Find the latest stable version of the action
2. Get its SHA using the methods above
3. Update the workflow file with the new SHA

### Common Actions Reference

| Action | Latest Stable | SHA |
|--------|--------------|-----|
| actions/checkout | v4.1.1 | b4ffde65f46336ab88eb53be808477a3936bae11 |
| actions/setup-python | v5.0.0 | 0a5c61591373683505ea898e09a3ea4f39ef2b9c |
| actions/cache | v4.2.4 | 0400d5f644dc74513175e3cd8d07132dd4860809 |
| actions/upload-artifact | v4.3.1 | 5d5d22a31266ced268874388b861e4b58bb5c2f3 |

**Note**: Always verify these SHAs are current before using them.

## Automated Checking

To verify all workflows use SHA-pinning:
```bash
# Check for non-SHA references in workflow files
grep -n "uses:.*@[^a-f0-9]" .github/workflows/*.yml

# If this returns any results, those lines need to be fixed
```

## CI/CD Security Best Practices

1. **Principle of Least Privilege**: Only grant workflows the minimum permissions needed
2. **Secret Scanning**: Never hardcode secrets in workflow files
3. **Third-Party Actions**: Carefully review any third-party actions before using them
4. **Regular Updates**: Periodically update action SHAs to get security patches
5. **Dependabot**: Consider enabling Dependabot for automated action updates

## For AI Assistants (Claude, Copilot, etc.)

When creating or modifying GitHub Actions workflows:
1. **ALWAYS** use SHA-pinned versions, never tags
2. **ALWAYS** add version comments for human readability
3. **ALWAYS** verify SHAs are valid before committing
4. **NEVER** use `@main`, `@v4`, `@latest` or any other mutable reference
5. **CHECK** for deprecation warnings in CI logs and update accordingly

## Questions or Issues?

If you encounter issues with SHA-pinning or need help updating workflows, please:
1. Check the action's official repository for the latest releases
2. Verify you're using a stable release (not a pre-release)
3. Test the workflow in a feature branch before merging to main