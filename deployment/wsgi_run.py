import sys
from cohmo import app as application
from cohmo.views import init_chief, init_authentication_manager
init_chief()
init_authentication_manager()
