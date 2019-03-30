""""
ASGI entrypoint file for default channel layer.
Points to the channel layer configured as "default" so you can point
ASGI applications at "djhome.asgi:channel_layer" as their channel layer.
"""

import os
import django
from channels.routing import get_default_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djhome.settings")
django.setup()
application = get_default_application()
#channel_layer = get_channel_layer()


def before_hook(watcher, arbiter, hook_name):
    print('before_hook ' + hook_name)
    path = os.path.join(watcher.env['PYTHONPATH'].split(':', 1)[0], 'run')
    try:
        os.remove(os.path.join(path, 'daphne.sock'))
    except OSError:
        pass
    try:
        os.remove(os.path.join(path, 'daphne.sock.lock'))
    except OSError:
        pass
    return True
