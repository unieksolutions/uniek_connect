<!--
ts: 2025-12-31T13:20:05Z | git: <to-be-filled> | path: <relative-path>
-->
# VERSIONS

Multi-environment version tracking and deployment status.

**Source of Truth:** /opt/projects/<project-name>

## Environments

### Development
- **Location:** /opt/projects/<project-name>
- **Git Branch:** main
- **Git Commit:** <commit-sha>
- **Last Updated:** <timestamp>
- **Status:** Active development
- **API Endpoint:** http://localhost:<port>
- **Database:** <connection-string>
- **Credentials:** /opt/projects/<project-name>/.env (see SECRETS.md)
- **Access:** Direct filesystem
- **Deployment:** See DEPLOY.md - Development section
- **Components:**
  - <component>: <version>

### Staging
- **Location:** /opt/products/<project-name> OR <remote-server>
- **Git Branch:** staging
- **Git Commit:** <commit-sha>
- **Deployed:** <timestamp>
- **Deployed By:** <user>
- **Status:** Testing
- **API Endpoint:** <staging-url>
- **Database:** <connection-string>
- **Credentials:** /opt/products/<project-name>/.env.staging (see SECRETS.md)
- **SSH Access:** ssh <project>-staging (key: ~/.ssh/<project>_staging)
- **Deployment:** See DEPLOY.md - Staging section
- **Components:**
  - <component>: <version>

### Production
- **Location:** <remote-server>
- **Git Tag:** v<major>.<minor>.<patch>
- **Git Commit:** <commit-sha>
- **Deployed:** <timestamp>
- **Deployed By:** <user>
- **Status:** Live
- **API Endpoint:** <production-url>
- **Database:** <connection-string>
- **Credentials:** Vault secret/<project>/production (see SECRETS.md)
- **SSH Access:** Via bastion only (2FA required)
- **Deployment:** See DEPLOY.md - Production section
- **Components:**
  - <component>: <version>

## Version History

| Version | Date | Environment | Commit | Notes |
|---------|------|-------------|--------|-------|
| v0.1.0  | YYYY-MM-DD | dev | abc123 | Initial setup |

## Dependencies

Key library/framework versions used across environments:

| Dependency | Dev | Staging | Production |
|------------|-----|---------|------------|
| <library>  | <ver> | <ver> | <ver> |

## Notes

- This file tracks what is deployed where
- Update after each deployment
- Source of truth is always /opt/projects/<project-name>
- For component lock files see: package.json, requirements.txt, etc.
