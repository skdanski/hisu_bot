import time
import sys

from util import logger


logging = logger.Logger('logging_test', 'logging_test_logger')

starttime = time.monotonic()
i = 0
while True:
    print("tick " + str(i))
    logging.info("YEP COCK", 'MongoDB: This is an info ' + str(i))
    logging.debug("YEP COCK", 'MongoDB: This is a debug ' + str(i))
    logging.warning("YEP COCK", 'MongoDB: This is a warning ' + str(i))
    logging.error("YEP COCK", 'MongoDB: This is an error ' + str(i))

    time.sleep(60.0 - ((time.monotonic() - starttime) % 60.0))
    i+= 1
