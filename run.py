from cohmo import app
from cohmo.views import init_chief, init_authentication_manager

if __name__ == '__main__':
    init_chief()
    init_authentication_manager()
    app.run()
