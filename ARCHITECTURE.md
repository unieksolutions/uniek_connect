<!--
ts: 2026-01-27T13:00:00Z | git: <to-be-filled> | path: /opt/bootstrap
-->

# ARCHITECTURE

System design and technical decisions. See previous full content.

---

## Feature Flags (MANDATORY for /opt/products)

**All production services MUST implement feature flags for automated testing.**

### Why Feature Flags?

Feature flags enable:
- **A/B testing** - Test new features with subset of users
- **Gradual rollouts** - Deploy features incrementally
- **Emergency killswitch** - Disable broken features instantly
- **Automated testing** - Test environments can enable/disable features
- **Continuous deployment** - Deploy code without exposing features

### Implementation Requirements

**1. Configuration File**

Each service MUST have a feature flags configuration file:

```yaml
# config/feature_flags.yaml
features:
  new_ui:
    enabled: false
    description: "New responsive UI design"
    environments:
      dev: true
      accept: true
      prod: false

  api_v2:
    enabled: false
    description: "API v2 endpoints"
    rollout_percentage: 0  # 0-100
    environments:
      dev: true
      accept: false
      prod: false

  experimental_cache:
    enabled: false
    description: "Redis caching layer"
    requires: ["redis_available"]
```

**2. Feature Flag Library**

```python
# utils/feature_flags.py
import os
import yaml
from typing import Dict, Optional

class FeatureFlags:
    def __init__(self, config_path: str = "config/feature_flags.yaml"):
        self.env = os.getenv("ENVIRONMENT", "dev")
        self.config = self._load_config(config_path)

    def _load_config(self, path: str) -> Dict:
        with open(path) as f:
            return yaml.safe_load(f)

    def is_enabled(self, feature: str, user_id: Optional[str] = None) -> bool:
        """Check if feature is enabled"""
        if feature not in self.config["features"]:
            return False

        flag = self.config["features"][feature]

        # Check environment-specific setting
        if "environments" in flag:
            if self.env in flag["environments"]:
                if not flag["environments"][self.env]:
                    return False

        # Check global enabled
        if not flag.get("enabled", False):
            return False

        # Check rollout percentage
        if "rollout_percentage" in flag and user_id:
            hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
            if (hash_val % 100) >= flag["rollout_percentage"]:
                return False

        return True

# Usage in code:
flags = FeatureFlags()

if flags.is_enabled("new_ui"):
    return render_new_ui()
else:
    return render_old_ui()
```

**3. Environment Variables**

Override via environment variables:
```bash
FEATURE_NEW_UI=true
FEATURE_API_V2=false
```

**4. Admin API Endpoints**

Production services MUST expose feature flag API:
```
GET  /api/admin/features          # List all flags
POST /api/admin/features/:name    # Toggle flag
GET  /api/admin/features/:name    # Get flag status
```

### Testing Integration

**Automated tests can enable/disable features:**

```python
# tests/test_new_feature.py
def test_new_ui_enabled():
    with override_feature("new_ui", enabled=True):
        response = client.get("/")
        assert "new-ui-class" in response.text

def test_new_ui_disabled():
    with override_feature("new_ui", enabled=False):
        response = client.get("/")
        assert "old-ui-class" in response.text
```

### Deployment Checklist

Before deploying to production:
- [ ] Feature flags implemented
- [ ] Tests use feature flag overrides
- [ ] config/feature_flags.yaml exists
- [ ] Admin API endpoints work
- [ ] Documentation updated

### Feature Flag Lifecycle

1. **Development** - Flag created, enabled in dev
2. **Acceptance Testing** - Enabled in accept
3. **Production Canary** - Enabled for 5% users
4. **Production Rollout** - Increase to 100%
5. **Flag Removal** - After feature stable for 30 days, remove flag and cleanup code

