import uuid

CDN_ENDPOINT = 'http://c808c3b88c2c6bfd2a2d-c9b35a8d613c565e1fa28656cc718020.r88.cf5.rackcdn.com'

PASTE_DIR = '/tmp/pasted'

RATE_LIMIT_DBM_FILE = '/tmp/pasted/pasted.ratelimit.dbm'

# String value of the CDN provider. Options: ["openstack"]
CDN_PROVIDER = 'openstack'
CDN_CONTAINER_NAME = 'pasted'

GOOGLE_ANALYTICS = 'UA-128874436-1'

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
OS_INSECURE = True
OS_INTERFACE = 'internal'


# System options
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE='Lax'
