# SDLC Pipeline - Stage-Based Development

**Purpose:** Enforced development lifecycle met role-based access control
**Last Updated:** 2026-05-10
**Status:** Architecture defined, implementation pending

---

## Overview

Alle projecten doorlopen 4 stages met dedicated agents en enforced permissions:

```
┌─────────────┐
│ dev-agent   │ → /opt/projects/{project}  (development)
│             │   • Code, unit tests, prototypes
│             │   • Git commits, branches
└──────┬──────┘   • NO backend access (via :65000 only)
       │
       │ handoff: git tag + approval
       ↓
┌─────────────┐
│ test-agent  │ → /opt/accept/{project}  (acceptance)
│             │   • Integration tests, QA
│             │   • Load tests, security scans
└──────┬──────┘   • NO backend access (via :65000 only)
       │
       │ handoff: test report + approval
       ↓
┌─────────────┐
│deploy-agent │ → /opt/tools/ or /opt/products/  (production)
│             │   • Systemd service restarts
│             │   • Rollback on failure
└──────┬──────┘   • NO backend access (via :65000 only)
       │
       │ monitoring
       ↓
┌─────────────┐
│ prod-agent  │ → /opt/tools/ (read-only monitoring)
│             │   • Health checks, metrics
│             │   • Log analysis, alerts
└─────────────┘   • Emergency hotfix approval
```

---

## Stage Definitions

### Stage 1: Development (dev-agent)

**Location:** `/opt/projects/{project}/`

**Responsibilities:**
- Write code, add features, fix bugs
- Run unit tests (pytest, jest, etc.)
- Create git commits and branches
- Update documentation (README, API.md, etc.)
- **Handoff:** Create git tag `stage/test-ready` + update PIPELINE_STATUS.md

**Permissions:**
- **Read:** /opt/projects/, /opt/bootstrap/, /opt/tools/.env (secrets)
- **Write:** /opt/projects/{assigned projects only}
- **Execute:** git, pytest, npm test, linters
- **Systemctl:** ❌ None
- **Backend access:** ❌ Only via spi-manager :65000

**Firewall:** Blocked from direct backend ports (65400, 65401, 61620, 655xx)

**Testing Requirements:**
- All unit tests pass (`pytest tests/`)
- Code linters pass (ruff, mypy, eslint)
- No secrets in code (check with grep)
- Documentation updated

---

### Stage 2: Testing (test-agent)

**Location:** `/opt/accept/{project}/`

**Responsibilities:**
- Copy code from /opt/projects/ (rsync, respecting .gitignore)
- Run acceptance tests against deployed test instance
- Integration tests with other services
- Load testing, security scanning
- **Handoff:** Create test report + git tag `stage/deploy-approved`

**Permissions:**
- **Read:** /opt/projects/ (source), /opt/accept/, /opt/bootstrap/
- **Write:** /opt/accept/{assigned projects}
- **Execute:** pytest, integration test scripts, security tools
- **Systemctl:** ✅ Restart test services (spi-*-test.service)
- **Backend access:** ❌ Only via spi-manager :65000

**Firewall:** Blocked from direct backend ports

**Testing Requirements:**
- All integration tests pass
- No regressions (compare with baseline)
- Security scan clean (no critical vulnerabilities)
- Performance within SLA (response time, throughput)
- Test report generated in `/opt/accept/{project}/TEST_REPORT.md`

---

### Stage 3: Deployment (deploy-agent)

**Location:** `/opt/tools/{project}/` or `/opt/products/{project}/`

**Responsibilities:**
- Copy from /opt/accept/ to production location
- Exclude .md files (except user-facing docs)
- Restart systemd services
- Verify health checks
- **Rollback** on failure (restore from /opt/backups/)

**Permissions:**
- **Read:** /opt/accept/, /opt/tools/, /opt/products/, /opt/backups/
- **Write:** /opt/tools/{assigned projects}, /opt/products/{assigned projects}
- **Execute:** rsync, systemctl, backup scripts
- **Systemctl:** ✅ Restart production services (spi-*.service)
- **Backend access:** ❌ Only via spi-manager :65000

**Firewall:** Blocked from direct backend ports

**Deployment Checklist:**
- [ ] Backup current production state (`/opt/scripts/backup_snapshot.sh`)
- [ ] Rsync with exclusions (`--exclude '*.md' --exclude '.git'`)
- [ ] Systemd daemon-reload if service files changed
- [ ] Restart service (`systemctl restart spi-{service}.service`)
- [ ] Wait 10s, check health (`curl /health` or systemctl status)
- [ ] If unhealthy: rollback from backup
- [ ] Update DEPLOY_LOG.md with timestamp, version, deployer

---

### Stage 4: Production Monitoring (prod-agent)

**Location:** `/opt/tools/` and `/opt/products/` (read-only)

**Responsibilities:**
- Monitor service health (systemctl status, /health endpoints)
- Analyze logs for errors (/var/log/, journalctl)
- Track metrics (VRAM usage, job queue, response times)
- Alert on anomalies (via ntfy, Telegram)
- **Emergency:** Approve hotfix deployments (bypass test stage)

**Permissions:**
- **Read:** /opt/tools/, /opt/products/, /var/log/, systemd journals
- **Write:** ❌ None (read-only, except approved hotfixes)
- **Execute:** journalctl, systemctl status, monitoring tools
- **Systemctl:** ✅ Restart services (emergency only, requires justification)
- **Backend access:** ❌ Only via spi-manager :65000

**Firewall:** Blocked from direct backend ports

**Monitoring Checklist:**
- [ ] All services active (`systemctl list-units 'spi-*'`)
- [ ] VRAM usage within limits (`/gpu/status`)
- [ ] Job queue healthy (`/v2/jobs/timeline/vram`)
- [ ] No error spikes in logs (journalctl -u spi-manager -p err)
- [ ] Response times within SLA

**Hotfix Approval:**
- Critical bug in production (service down, data loss, security)
- User approval required (Niek or designated approver)
- deploy-agent executes with tag `hotfix/{issue-id}`
- Post-mortem required after hotfix

---

## User Setup

### Create Agent Users

```bash
#!/bin/bash
# /opt/scripts/setup_sdlc_users.sh

# Create system users with home directories
sudo useradd -m -s /bin/bash -G uniek dev-agent
sudo useradd -m -s /bin/bash -G uniek test-agent
sudo useradd -m -s /bin/bash -G uniek deploy-agent
sudo useradd -m -s /bin/bash -G uniek prod-agent

# Set passwords (or use SSH keys)
echo "dev-agent:$(openssl rand -base64 32)" | sudo chpasswd
echo "test-agent:$(openssl rand -base64 32)" | sudo chpasswd
echo "deploy-agent:$(openssl rand -base64 32)" | sudo chpasswd
echo "prod-agent:$(openssl rand -base64 32)" | sudo chpasswd

# SSH key setup (recommended)
for user in dev-agent test-agent deploy-agent prod-agent; do
    sudo -u $user ssh-keygen -t ed25519 -f /home/$user/.ssh/id_ed25519 -N ""
done

echo "Users created. Configure SSH keys or passwords as needed."
```

### File Permissions

```bash
#!/bin/bash
# /opt/scripts/setup_sdlc_permissions.sh

# /opt/projects - dev-agent write access
sudo chown -R uniek:uniek /opt/projects
sudo chmod -R 775 /opt/projects
sudo setfacl -R -m u:dev-agent:rwx /opt/projects
sudo setfacl -R -d -m u:dev-agent:rwx /opt/projects

# /opt/accept - test-agent write access
sudo chown -R uniek:uniek /opt/accept
sudo chmod -R 775 /opt/accept
sudo setfacl -R -m u:test-agent:rwx /opt/accept
sudo setfacl -R -d -m u:test-agent:rwx /opt/accept

# /opt/tools and /opt/products - deploy-agent write, prod-agent read-only
sudo chown -R uniek:uniek /opt/tools /opt/products
sudo chmod -R 755 /opt/tools /opt/products
sudo setfacl -R -m u:deploy-agent:rwx /opt/tools
sudo setfacl -R -m u:deploy-agent:rwx /opt/products
sudo setfacl -R -m u:prod-agent:r-x /opt/tools
sudo setfacl -R -m u:prod-agent:r-x /opt/products

# /opt/bootstrap - all agents read-only
sudo chmod -R 755 /opt/bootstrap

echo "Permissions configured with ACLs."
```

### Firewall Rules (Backend Enforcement)

```bash
#!/bin/bash
# /opt/scripts/setup_sdlc_firewall.sh

# Backend ports to block
BACKEND_PORTS=(65400 65401 61620)
BACKEND_RANGE="65500:65599"
AGENT_USERS=(dev-agent test-agent deploy-agent prod-agent)

# Block agent users from direct backend access
for user in "${AGENT_USERS[@]}"; do
    for port in "${BACKEND_PORTS[@]}"; do
        sudo iptables -A OUTPUT -p tcp --dport $port -m owner --uid-owner $user -j REJECT --reject-with tcp-reset
    done
    sudo iptables -A OUTPUT -p tcp --dport $BACKEND_RANGE -m owner --uid-owner $user -j REJECT --reject-with tcp-reset
done

# Save rules (Debian/Ubuntu)
sudo apt-get install -y iptables-persistent
sudo iptables-save | sudo tee /etc/iptables/rules.v4

echo "Firewall rules applied. Agents must use spi-manager :65000."
```

**Verification:**
```bash
# As dev-agent
sudo -u dev-agent curl http://localhost:65400/health
# Expected: Connection refused (blocked by firewall)

sudo -u dev-agent curl http://localhost:65000/v2/voice/synthesize -X POST -d '{"text":"test"}'
# Expected: Success (via spi-manager)
```

### Sudoers Configuration

```bash
# /etc/sudoers.d/sdlc_agents

# dev-agent: run tests, no systemctl
dev-agent ALL=(uniek) NOPASSWD: /usr/bin/pytest /opt/projects/*
dev-agent ALL=(uniek) NOPASSWD: /usr/bin/git -C /opt/projects/*

# test-agent: restart test services, run integration tests
test-agent ALL=(uniek) NOPASSWD: /usr/bin/systemctl restart spi-*-test.service
test-agent ALL=(uniek) NOPASSWD: /usr/bin/pytest /opt/accept/*

# deploy-agent: full systemctl for production, backup scripts
deploy-agent ALL=(uniek) NOPASSWD: /usr/bin/systemctl daemon-reload
deploy-agent ALL=(uniek) NOPASSWD: /usr/bin/systemctl restart spi-*.service
deploy-agent ALL=(uniek) NOPASSWD: /opt/scripts/backup_snapshot.sh *
deploy-agent ALL=(uniek) NOPASSWD: /usr/bin/rsync *

# prod-agent: read-only systemctl, emergency restart (logged)
prod-agent ALL=(uniek) NOPASSWD: /usr/bin/systemctl status *
prod-agent ALL=(uniek) NOPASSWD: /usr/bin/journalctl *
prod-agent ALL=(uniek) NOPASSWD: /usr/bin/systemctl restart spi-*.service
```

---

## Handoff Mechanism

### PIPELINE_STATUS.md (per project)

Location: `/opt/projects/{project}/PIPELINE_STATUS.md`

```markdown
# Pipeline Status - {project}

## Current Stage: TEST
**Last Updated:** 2026-05-10 15:30 CET
**Assigned Agent:** test-agent

---

## Stage History

### Development → Testing
- **Date:** 2026-05-10 14:00
- **Agent:** dev-agent
- **Git Tag:** stage/test-ready
- **Commit:** abc1234
- **Unit Tests:** ✅ All passed (42/42)
- **Approval:** auto (all tests green)

### Testing → Deployment
- **Date:** 2026-05-10 15:30
- **Agent:** test-agent
- **Git Tag:** stage/deploy-approved
- **Test Report:** /opt/accept/{project}/TEST_REPORT.md
- **Integration Tests:** ✅ All passed (18/18)
- **Approval:** Pending (manual review required)

### Deployment → Production
- **Date:** (not yet deployed)
- **Agent:** (pending)
- **Backup:** (not yet created)
- **Rollback Plan:** /opt/accept/{project}/DEPLOY.md

---

## Blockers

None

---

## Notes

Test suite expanded with load testing (500 req/s sustained).
Performance within SLA: p95 < 200ms.
```

### Git Tags

```bash
# dev-agent creates tag when ready for testing
git tag -a stage/test-ready -m "Unit tests pass, ready for acceptance"
git push --tags

# test-agent creates tag when ready for deployment
git tag -a stage/deploy-approved -m "Integration tests pass, ready for prod"
git push --tags

# deploy-agent creates tag after successful deployment
git tag -a stage/deployed-$(date +%Y%m%d-%H%M) -m "Deployed to production"
git push --tags
```

### Approval Gates

**Automatic Approval (green tests → next stage):**
- dev → test: If all unit tests pass
- test → deploy: If all integration tests pass AND no critical vulnerabilities

**Manual Approval Required:**
- deploy → prod: Human approval (Niek or designated)
- Hotfixes: Always manual approval + justification

**Approval Tracking:**
```bash
# /opt/projects/{project}/APPROVALS.md
## Deployment Approval - {project} v1.2.3
- **Date:** 2026-05-10 15:45
- **Approver:** Niek (uniek)
- **Stage:** test → deploy
- **Justification:** Security patch for CVE-2024-XXXX
- **Rollback Plan:** Tested in acceptance, backup created
- **Approved:** ✅ YES
```

---

## Coding Script Integration

### Extended coding.sh

```bash
#!/bin/bash
# /opt/tools/coding.sh - Extended with SDLC stages

STAGE=${1:-dev}  # dev, test, deploy, prod
PROJECT=${2:-spi-manager}

case $STAGE in
    dev)
        echo "Starting development session as dev-agent..."
        sudo -u dev-agent tmux new -s claude_${PROJECT}_dev \
            "cd /opt/projects/${PROJECT} && bash"
        ;;
    test)
        echo "Starting testing session as test-agent..."
        sudo -u test-agent tmux new -s claude_${PROJECT}_test \
            "cd /opt/accept/${PROJECT} && bash"
        ;;
    deploy)
        echo "Starting deployment session as deploy-agent..."
        sudo -u deploy-agent tmux new -s claude_${PROJECT}_deploy \
            "cd /opt/tools/${PROJECT} && bash"
        ;;
    prod)
        echo "Starting monitoring session as prod-agent..."
        sudo -u prod-agent tmux new -s claude_${PROJECT}_prod \
            "journalctl -u spi-${PROJECT} -f"
        ;;
    *)
        echo "Usage: coding.sh [dev|test|deploy|prod] [project-name]"
        exit 1
        ;;
esac
```

**Usage:**
```bash
# Start development session
/opt/tools/coding.sh dev spi-manager

# Handoff to testing
/opt/tools/coding.sh test spi-manager

# Deploy to production
/opt/tools/coding.sh deploy spi-manager

# Monitor production
/opt/tools/coding.sh prod spi-manager
```

### Handoff Commands (within sessions)

```bash
# In dev session: handoff to test
handoff-test() {
    local project=$(basename $PWD)

    # Verify unit tests pass
    pytest tests/ || { echo "Tests failed, fix before handoff"; return 1; }

    # Commit and tag
    git add .
    git commit -m "feat: ready for acceptance testing"
    git tag -a stage/test-ready -m "Unit tests pass"
    git push --tags

    # Update pipeline status
    echo "Stage: TEST" >> PIPELINE_STATUS.md
    echo "Date: $(date -Iseconds)" >> PIPELINE_STATUS.md

    # Notify test-agent (via ntfy or file watch)
    curl -d "Project ${project} ready for testing" ntfy.sh/spi-pipeline

    echo "✅ Handoff complete. test-agent can start acceptance testing."
}

# In test session: handoff to deploy
handoff-deploy() {
    # Similar pattern: run tests, create tag, notify deploy-agent
}
```

---

## Endpoint Development Strategy

### Problem: Backward Compatibility + Innovation

**Challenge:** Hoe ontwikkel je nieuwe/betere endpoints zonder production te breken?

### Solution: Versioned Endpoints + Feature Flags

#### 1. Version Namespaces

```
/v2/image/generate  → stable (production)
/v3/image/generate  → new (testing in acceptance)
/v4/image/generate  → future (development only)
```

**Rules:**
- **v2** = stable, backward compatible, production
- **v3** = beta, opt-in, acceptance testing
- **v4** = experimental, development only

#### 2. Feature Flags (per endpoint)

```python
# app/feature_flags.py
FEATURES = {
    "v3_async_by_default": {
        "enabled": False,  # dev/test only
        "rollout_percentage": 0,  # gradual rollout
        "allowed_agents": ["dev-agent", "test-agent"],
    },
    "v3_enhanced_eta": {
        "enabled": True,
        "rollout_percentage": 100,
    },
}

def is_feature_enabled(feature_name, agent_id=None):
    feature = FEATURES.get(feature_name, {})
    if not feature.get("enabled"):
        return False
    if agent_id and feature.get("allowed_agents"):
        return agent_id in feature["allowed_agents"]
    # Rollout percentage check
    return random.randint(1, 100) <= feature.get("rollout_percentage", 0)
```

**Usage:**
```python
@router.post("/v3/image/generate")
async def generate_image(request: Request):
    if is_feature_enabled("v3_async_by_default", request.state.agent_id):
        return await async_implementation()
    else:
        return await legacy_sync_implementation()
```

#### 3. Canary Deployments

**Gradual rollout:**
1. Deploy v3 endpoint to acceptance (test-agent validates)
2. Deploy to production with `rollout_percentage: 5` (5% of traffic)
3. Monitor metrics (error rate, latency, user feedback)
4. Increase rollout: 5% → 25% → 50% → 100%
5. Deprecate v2 after 3 months stable v3

#### 4. Parallel Run (Shadow Testing)

```python
# Run both v2 and v3, compare results, log differences
@router.post("/v2/image/generate")
async def generate_image_v2(request: Request):
    result_v2 = await v2_implementation(request)

    # Shadow test v3 (async, don't block v2 response)
    if is_feature_enabled("shadow_test_v3"):
        asyncio.create_task(shadow_test_v3(request, result_v2))

    return result_v2

async def shadow_test_v3(request, expected_result):
    result_v3 = await v3_implementation(request)
    if result_v3 != expected_result:
        log_difference(request, expected_result, result_v3)
```

#### 5. Deprecation Policy

```
v2 released       → v3 development starts
v3 beta released  → v2 stable (no new features)
v3 stable         → v2 deprecated (3 month notice)
v2 sunset         → v2 returns 410 Gone (redirect to v3 docs)
```

**In /info endpoint:**
```json
{
  "versioning": {
    "current": "v3",
    "supported": ["v2", "v3"],
    "deprecated": ["v2"],
    "sunset": {
      "v2": "2027-01-01",
      "reason": "Replaced by v3 async-first API"
    }
  }
}
```

---

## Rollback Procedures

### Automatic Rollback Triggers

```bash
# In deployment script
deploy() {
    # Deploy new version
    sudo rsync -av /opt/accept/${PROJECT}/ /opt/tools/${PROJECT}/
    sudo systemctl restart spi-${PROJECT}

    # Wait for health check
    sleep 10

    # Check health
    if ! curl -f http://localhost:65000/health; then
        echo "Health check failed, rolling back..."
        rollback
        return 1
    fi

    # Check error rate (last 60s)
    error_rate=$(journalctl -u spi-${PROJECT} -S "60 seconds ago" -p err | wc -l)
    if [ $error_rate -gt 5 ]; then
        echo "Error rate too high ($error_rate), rolling back..."
        rollback
        return 1
    fi

    echo "Deployment successful"
}

rollback() {
    echo "Rolling back to previous version..."
    latest_backup=$(ls -t /opt/backups/${PROJECT}_* | head -1)
    sudo rsync -av $latest_backup/ /opt/tools/${PROJECT}/
    sudo systemctl restart spi-${PROJECT}

    # Notify
    curl -d "ROLLBACK: ${PROJECT} rolled back to ${latest_backup}" ntfy.sh/spi-alerts
}
```

### Manual Rollback

```bash
# List available backups
ls -lh /opt/backups/ | grep spi-manager

# Restore specific backup
sudo rsync -av /opt/backups/spi-manager_2026-05-10T14-30/ /opt/tools/spi-manager/
sudo systemctl restart spi-manager

# Verify
curl http://localhost:65000/health
```

---

## Testing the Pipeline

### Pilot Project: spi-manager AIID endpoints

```bash
# 1. dev-agent: develop AIID endpoints
sudo -u dev-agent bash
cd /opt/projects/spi-manager
# ... code AIID endpoints ...
pytest tests/test_aiid_emotion_api.py
git commit -m "feat: AIID emotion engine endpoints"
git tag stage/test-ready
git push --tags

# 2. test-agent: acceptance testing
sudo -u test-agent bash
rsync -av --exclude='.git' /opt/projects/spi-manager/ /opt/accept/spi-manager/
cd /opt/accept/spi-manager
pytest tests/integration/  # Integration tests
# Generate TEST_REPORT.md
git tag stage/deploy-approved
git push --tags

# 3. deploy-agent: deploy to production
sudo -u deploy-agent bash
/opt/scripts/backup_snapshot.sh /opt/tools/spi-manager
rsync -av --exclude='*.md' --exclude='.git' /opt/accept/spi-manager/ /opt/tools/spi-manager/
sudo systemctl restart spi-manager
sleep 10
curl http://localhost:65000/aiid/health  # Verify
# Update DEPLOY_LOG.md

# 4. prod-agent: monitor
sudo -u prod-agent bash
journalctl -u spi-manager -f  # Watch logs
curl http://localhost:65000/gpu/status  # Check VRAM
# Alert if anomalies
```

---

## Migration Path

### Phase 1: Setup (Week 1)
- [ ] Create agent users (dev, test, deploy, prod)
- [ ] Configure file permissions (ACLs)
- [ ] Setup firewall rules (iptables)
- [ ] Configure sudoers
- [ ] Test enforcement (agents blocked from backends)

### Phase 2: Tooling (Week 2)
- [ ] Extend coding.sh with stage support
- [ ] Create handoff commands (handoff-test, handoff-deploy)
- [ ] Setup PIPELINE_STATUS.md template
- [ ] Create deployment scripts with rollback
- [ ] Setup monitoring dashboards

### Phase 3: Pilot (Week 3)
- [ ] Run spi-manager through full pipeline
- [ ] Document pain points and improvements
- [ ] Refine handoff mechanism
- [ ] Create runbooks for each stage

### Phase 4: Rollout (Week 4+)
- [ ] Migrate all projects to pipeline
- [ ] Train team on new workflow
- [ ] Setup alerts and notifications
- [ ] Document lessons learned

---

## Related Documentation

- **Architecture:** `/opt/projects/spi-manager/ARCHITECTURE.md` (central resource principle)
- **Resource specs:** `/opt/projects/spi-manager/RESOURCE_SPECS.md` (VRAM/RAM/CPU per endpoint)
- **Coding rules:** `/opt/bootstrap/CODING_RULES.md` (development standards)
- **Deployment:** `/opt/bootstrap/DEPLOY.md` (deployment patterns)
- **Bootstrap index:** `/opt/bootstrap/START.md` (all documentation)

---

## Open Questions

**Decisions needed before implementation:**

1. **prod-agent role:** Monitoring only or also hotfix execution?
   - Current draft: monitoring + emergency restart (with approval)

2. **Approval gates:** Fully automated or manual review required?
   - Current draft: auto (dev→test), manual (test→deploy)

3. **Feature flags storage:** In-code or database?
   - Current draft: in-code (simpler, no DB dependency)

4. **Rollback SLA:** How fast must rollback complete?
   - Current draft: <5 minutes (rsync + restart)

5. **Pipeline tracking:** PIPELINE_STATUS.md or database?
   - Current draft: markdown file (simple, git-tracked)

**Discuss with Niek before proceeding to implementation.**
