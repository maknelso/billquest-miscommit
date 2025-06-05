import os

# Get environment from environment variable, default to 'dev'
ENV = os.environ.get("ENVIRONMENT", "dev")

# Define CORS configurations for different environments
CORS_CONFIG = {
    "dev": {
        "allowed_origins": ["http://localhost:5173"],
        "allowed_methods": ["GET", "POST", "OPTIONS"],
        "allowed_headers": [
            "Content-Type",
            "X-Amz-Date",
            "Authorization",
            "X-Api-Key",
            "X-Amz-Security-Token",
        ],
    },
    "prod": {
        "allowed_origins": ["https://your-production-domain.com"],
        "allowed_methods": ["GET", "POST", "OPTIONS"],
        "allowed_headers": [
            "Content-Type",
            "X-Amz-Date",
            "Authorization",
            "X-Api-Key",
            "X-Amz-Security-Token",
        ],
    },
}


def get_cors_headers():
    """
    Get CORS headers based on the current environment

    Returns:
        dict: CORS headers for the current environment
    """
    config = CORS_CONFIG.get(ENV, CORS_CONFIG["dev"])

    # For development, you might want to allow all origins
    if ENV == "dev" and os.environ.get("ALLOW_ALL_ORIGINS", "false").lower() == "true":
        return {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": ",".join(config["allowed_methods"]),
            "Access-Control-Allow-Headers": ",".join(config["allowed_headers"]),
        }

    # For production or restricted development
    return {
        "Access-Control-Allow-Origin": ",".join(config["allowed_origins"]),
        "Access-Control-Allow-Methods": ",".join(config["allowed_methods"]),
        "Access-Control-Allow-Headers": ",".join(config["allowed_headers"]),
    }
