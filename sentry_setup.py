import sentry_sdk
import os

# Get environment settings (set your environment as an environment variable)
environment = os.getenv('SENTRY_ENVIRONMENT', 'development')

# Set your Sentry DSN from environment variables for security
sentry_dsn = os.getenv('SENTRY_DSN', 'YOUR_SENTRY_DSN')

sentry_sdk.init(
    dsn=sentry_dsn,
    traces_sample_rate=0.1 if environment == 'production' else 1.0,  # Lower trace rate in production
    send_default_pii=True,  # Send Personally Identifiable Information (PII) for user tracking
    environment=environment,  # Track the environment (production, staging, development)
    release="your-app-name@1.0.0",  # Add the release version of your app
    debug=environment != 'production',  # Enable debug mode in non-production environments
    timeout=2.0,  # Add a timeout for network requests to Sentry
    max_breadcrumbs=100,  # Limit the number of breadcrumbs stored for better performance
    max_queue_size=50,  # Control how many events are queued to send
    attach_stacktrace=True,  # Attach stack trace for better debugging
    retries=5  # Retry sending the event up to 5 times in case of failure
)
