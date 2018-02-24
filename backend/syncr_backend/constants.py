NODE_ID_BYTE_SIZE = 32
DROP_ID_BYTE_SIZE = 64

# Request structure indices for Tracker
TRACKER_TYPE_INDEX = 0
TRACKER_ID_INDEX = 1
TRACKER_VALUE_INDEX = 2

# Tuple structure for drop availability
TRACKER_DROP_NODE_INDEX = 0
TRACKER_DROP_IP_INDEX = 1
TRACKER_DROP_PORT_INDEX = 2
TRACKER_DROP_TIMESTAMP_INDEX = 3

# Tracker drop availability time to live
TRACKER_DROP_AVAILABILITY_TTL = 300

# Tracker server result responses
TRACKER_OK_RESULT = 'OK'
TRACKER_ERROR_RESULT = 'ERROR'

# file_metadata constants
DEFAULT_CHUNK_SIZE = 2**23
DEFAULT_FILE_METADATA_LOCATION = b".files/"

# Node init constants
DEFAULT_INIT_DIR = ".node/"
