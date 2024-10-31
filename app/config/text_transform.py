# Base percentage
DEFAULT_PERCENTAGE = 100  # Base percentage (100%)

# Length constraints
MIN_LENGTH = 110      # Minimum expansion (110%)
MAX_LENGTH = 300      # Maximum expansion (300%)
DEFAULT_LENGTH = 150  # Default expansion target

# Step constraints
DEFAULT_STEP_SIZE = 25   # Default step between lengths
MIN_STEP_SIZE = 10      # Minimum step size
MAX_STEP_SIZE = 50      # Maximum step size

# Version constraints
MAX_VERSIONS = 5        # Maximum versions per length
DEFAULT_VERSIONS = 1    # Default number of versions per length

# Operation modes
MODES = {
    "expand": {
        "fixed": "Fixed length expansion",
        "staggered": "Progressive expansion in steps",
        "custom": "Custom expansion lengths"
    }
}
