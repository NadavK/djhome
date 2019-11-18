from channels.auth import AuthMiddlewareStack
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from rest_framework.authentication import TokenAuthentication
from rest_framework_jwt.authentication import BaseJSONWebTokenAuthentication
import logging


class TokenAuthenticationQueryString(TokenAuthentication):
    def authenticate(self, request):
        try:
            self.logger = logging.getLogger(__name__)
            self.logger.debug(request)
            token = request.query_params.get('token')
            self.logger.info('token: ' + str(token))
            return self.authenticate_credentials(token)
        except:
            self.logger.exception('TokenAuthenticationQueryString: ')
            return None


class JSONWebTokenAuthenticationQueryString(BaseJSONWebTokenAuthentication):
    """
    Extracts the JWT from http query-param (instead of from http header)
    """
    logger = None

    def get_jwt_value(self, request):
        try:
            self.logger = logging.getLogger(__name__)
            self.logger.debug('request: %s', request)
            jwt = request.query_params.get('jwt')
            self.logger.info('jwt: ' + str(jwt))
            return jwt
        except:
            self.logger.exception('JSONWebTokenAuthenticationQueryString: ')
            return None


class JsonWebTokenAuthenticationFromScope(BaseJSONWebTokenAuthentication):
    """
    Extracts the JWT from a channel scope (instead of an http request)
    """
    logger = None

    def get_jwt_value(self, scope):
        try:
            self.logger = logging.getLogger(__name__)
            self.logger.debug(scope)

            #cookie = next(x for x in scope['headers'] if x[0].decode('utf-8') == 'cookie')[1].decode('utf-8')
            #return cookies.SimpleCookie(cookie)['JWT'].value

            jwt = scope['subprotocols']
            self.logger.info('protocols: ' + str(jwt))
            if len(jwt) > 0:
                jwt = jwt[0]
                return jwt
        except Exception:
            pass

        self.logger.warning('jwt: None')
        return None


class JsonTokenAuthMiddleware(BaseJSONWebTokenAuthentication):
    """
    Token authorization middleware for Django Channels 2
    """

    def __init__(self, inner):
        self.inner = inner
        self.logger = logging.getLogger(__name__)

    def __call__(self, scope):

        try:
            # Close old database connections to prevent usage of timed out connections
            close_old_connections()

            user, jwt_value = JsonWebTokenAuthenticationFromScope().authenticate(scope)
            self.logger.info('jwt %s (%s)' % (user, jwt_value))
            scope['user'] = user
            scope['jwt'] = jwt_value
        except Exception:
            scope['user'] = AnonymousUser()
            scope['jwt'] = None
            self.logger.warning('jwt: None')

        return self.inner(scope)


def JsonTokenAuthMiddlewareStack(inner):
    return JsonTokenAuthMiddleware(AuthMiddlewareStack(inner))
