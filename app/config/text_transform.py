# Base percentage
DEFAULT_PERCENTAGE = 100  # Base percentage (100%)

# Expansion constraints (above 100%)
MIN_LENGTH_EXPANSION = 110      # Minimum expansion (110%)
MAX_LENGTH_EXPANSION = 300      # Maximum expansion (300%)
DEFAULT_LENGTH_EXPANSION = 150  # Default expansion target

# Compression constraints (retention percentages, below 100%)
MAX_LENGTH_COMPRESSION = 90       # Keep up to 90% of original
DEFAULT_LENGTH_COMPRESSION = 50   # Default: keep 50% of original
MIN_LENGTH_COMPRESSION = 10       # Keep at least 10% of original

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
    },
    "compress": {
        "fixed": "Fixed length compression (percentage to retain)",
        "staggered": "Progressive compression in steps",
        "custom": "Custom compression lengths"
    }
}
