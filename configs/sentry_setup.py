import os
import sentry_sdk
from sentry_sdk.transport import HttpTransport
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

print(f"SENTRY_DSN: {os.getenv('SENTRY_DSN')}")

# Custom transport to set timeout
class CustomHttpTransport(HttpTransport):
    def __init__(self, options):
        super().__init__(options)
        self._timeout = 5  # Default timeout of 5 seconds

    def _send_request(self, url, *args, **kwargs):
        kwargs["timeout"] = self._timeout
        return super()._send_request(url, *args, **kwargs)


# Get environment settings (set your environment as an environment variable)
environment = os.getenv("SENTRY_ENVIRONMENT", "development")

# Set your Sentry DSN from environment variables for security
sentry_dsn = os.getenv("SENTRY_DSN")  # Ensure SENTRY_DSN is set as an environment variable

# Optionally, set the release version dynamically
release_version = os.getenv("RELEASE_VERSION", "your-app-name@1.0.0")

try:
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,  # Track the environment (production, staging, development)
            release=release_version,  # Add the release version of your app
            send_default_pii=True,  # Send Personally Identifiable Information (PII) for user tracking
            debug=environment != "production",  # Enable debug mode in non-production environments
            max_breadcrumbs=100,  # Limit the number of breadcrumbs stored for better performance
            attach_stacktrace=True,  # Attach stack trace for better debugging
            traces_sample_rate=0.1 if environment == "production" else 1.0,  # Lower trace rate in production
            shutdown_timeout=2,  # Wait up to 2 seconds to send events before shutdown
            transport=CustomHttpTransport,  # Use the custom transport without additional options
        )
        print("Sentry initialized successfully.")
    else:
        print("Sentry DSN not provided. Please set the SENTRY_DSN environment variable.")
except Exception as e:
    print(f"Error initializing Sentry: {e}")
    print("Continuing without Sentry.")
