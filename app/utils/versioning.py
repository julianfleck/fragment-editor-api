from typing import Dict, Optional
from datetime import datetime
from app.config import Config

# Convert semver to API version format (e.g. "1.0.0" -> "v1")
API_VERSION = f"v{Config.API_VERSION.split('.')[0]}"
LATEST_VERSION = API_VERSION
SUPPORTED_VERSIONS = [API_VERSION]
DEPRECATED_VERSIONS: Dict[str, datetime] = {}  # version -> end of life date


def get_version_headers(requested_version: Optional[str] = None) -> Dict[str, str]:
    """Generate version-related response headers."""
    headers = {
        "X-API-Version": API_VERSION,
        "X-API-Latest-Version": LATEST_VERSION,
        "X-API-Supported-Versions": ",".join(SUPPORTED_VERSIONS)
    }

    # Add deprecation warning if applicable
    if requested_version in DEPRECATED_VERSIONS:
        eol_date = DEPRECATED_VERSIONS[requested_version]
        headers["X-API-Deprecation-Date"] = eol_date.isoformat()
        headers["X-API-Upgrade-To"] = LATEST_VERSION

    return headers


def validate_version(version: str) -> bool:
    """Check if requested API version is supported."""
    return version in SUPPORTED_VERSIONS
