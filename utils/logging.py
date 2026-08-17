import datetime
import logging
import os
import sys
import traceback

format = logging.Formatter('%(asctime)s - %(filename)s - %(levelname)s - %(message)s')
timestamp = datetime.datetime.now(tz=datetime.timezone.utc).strftime('%d-%b-%y-%H_%M')
log_dir = os.path.join("logs", timestamp)
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

debug_file = os.path.abspath(os.path.join(log_dir, 'debug.log'))
warns_file = os.path.abspath(os.path.join(log_dir, 'warn.log'))




# Create a custom logger
logger = logging.getLogger(__name__)

# Create handlers
c_handler = logging.StreamHandler()
debug_handler = logging.FileHandler(debug_file)
warn_handler = logging.FileHandler(warns_file)





c_handler.setFormatter(format)
debug_handler.setFormatter(format)
warn_handler.setFormatter(format)



logger.addHandler(c_handler)
logger.addHandler(debug_handler)
logger.addHandler(warn_handler)
logger.setLevel(logging.DEBUG)

warn_handler.setLevel(logging.WARN)



def handle_exception(exc_type, exc_value, exc_traceback):
    
    tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

    # Log the exception
    logger.error(f"Unhandled exception:\n{tb_str}",)

# Set the exception hook
sys.excepthook = handle_exception

