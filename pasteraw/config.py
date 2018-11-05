import uuid


CDN_ENDPOINT = 'http://cdn.pasted.tech'

PASTE_DIR = '/tmp/pasted'
LOG_FILE = '/tmp/pasted.log'
RATE_LIMIT_DBM_FILE = '/tmp/pasted.ratelimit.dbm'

# if you don't override the secret key, one will be chosen for you
SECRET_KEY = uuid.uuid4().hex

CLOUD_ID_TYPE = None
CLOUD_REGION = None
RACKSPACE_USERNAME = None
RACKSPACE_API_KEY = None
CDN_CONTAINER_NAME = 'pasted'

