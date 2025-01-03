"""Sentry initialization module for Epic Events CRM.

This module sets up Sentry for error monitoring and performance tracking.
It configures environment variables, initializes Sentry with a custom transport,
and handles exceptions during the initialization process.
"""

import os
import sentry_sdk
from sentry_sdk.transport import HttpTransport
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print(f"SENTRY_DSN: {os.getenv('SENTRY_DSN')}")


class CustomHttpTransport(HttpTransport):
    """Custom HTTP transport for Sentry with an adjusted timeout."""

    def __init__(self, options):
        """Initialize the custom HTTP transport with a specific timeout.

        Args:
            options (dict): Transport options.
        """
        super().__init__(options)
        # Set the timeout through options that HttpTransport expects
        self.options["timeout"] = 5  # Default timeout of 5 seconds


# Get environment settings
environment = os.getenv("SENTRY_ENVIRONMENT", "development")
sentry_dsn = os.getenv("SENTRY_DSN")  # Ensure SENTRY_DSN is set

# Optionally, set the release version dynamically
release_version = os.getenv("RELEASE_VERSION", "your-app-name@1.0.0")

try:
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            release=release_version,
            send_default_pii=True,
            debug=environment != "production",
            max_breadcrumbs=100,
            attach_stacktrace=True,
            traces_sample_rate=0.1 if environment == "production" else 1.0,
            shutdown_timeout=2,
            transport=CustomHttpTransport,
        )
        print("Sentry initialized successfully.")
    else:
        print(
            "Sentry DSN not provided. Please set the SENTRY_DSN environment variable."
        )
except Exception as e:
    print(f"Error initializing Sentry: {e}")
    print("Continuing without Sentry.")
