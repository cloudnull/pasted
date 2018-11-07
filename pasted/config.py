import uuid

CDN_ENDPOINT = 'http://pasted.tech'

PASTE_DIR = '/tmp/pasted'
RATE_LIMIT_DBM_FILE = '/tmp/pasted/pasted.ratelimit.dbm'

CLOUD_ID_TYPE = None
CLOUD_REGION = None
RACKSPACE_USERNAME = None
RACKSPACE_API_KEY = None
CDN_CONTAINER_NAME = 'pasted'

GOOGLE_ANALYTICS = 'UA-128874436-1'

# if you don't override the secret key, one will be chosen for you
SECRET_KEY = uuid.uuid4().hex
