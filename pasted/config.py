import uuid

# Public CDN endpoint
CDN_ENDPOINT = None

# Local temp directory
PASTE_DIR = '/tmp/pasted'

# String value of the CDN provider. Options: ["openstack"]
CDN_PROVIDER = 'openstack'
CDN_CONTAINER_NAME = 'pasted'

# Web analytics
GOOGLE_ANALYTICS = None

# if you don't override the secret key, one will be chosen for you
SECRET_KEY = uuid.uuid4().hex

# Options for OpenStack. Not all of these are required.
OS_USERNAME = None
OS_PASSWORD = None
OS_PROJECT_NAME = None
OS_PROJECT_DOMAIN_NAME = None
OS_TENANT_NAME = None
OS_USER_DOMAIN_NAME = None
OS_AUTH_URL = None
OS_REGION_NAME = None
OS_INSECURE = True  # Typically True when running with an 'internal' interface
OS_INTERFACE = 'internal'  # This is normally 'internal' or 'public'

# System options
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE='Lax'
