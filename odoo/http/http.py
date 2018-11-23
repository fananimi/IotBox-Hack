import re
import sys
import inspect
import logging

from .core import request, response, HTTPResponse, HTTPError


try: from simplejson import dumps as json_dumps
except ImportError: # pragma: no cover
    try: from json import dumps as json_dumps
    except ImportError:
        try: from django.utils.simplejson import dumps as json_dumps
        except ImportError:
            def json_dumps(data):
                raise ImportError("JSON support requires Python 2.6 or simplejson.")


_py2 = sys.version_info[0] == 2
_logger = logging.getLogger(__name__)


# Workaround for the missing "as" keyword in py3k.
def _e(): return sys.exc_info()[1]


def route(rule, **options):
    """A decorator that is used to define custom routes for methods in
    BottleView subclasses. The format is exactly the same as Bottle's
    `@app.route` decorator.
    """

    def decorator(f):
        method = options.get('method') or ['GET', 'POST', 'OPTIONS']
        if not isinstance(method, list):
            method = [method]
        method = [m.upper() for m in method]
        if 'OPTIONS' not in method:
            method.append('OPTIONS')
        options['method'] = method

        # Put the rule cache on the method itself instead of globally
        if not hasattr(f, '_rule_cache') or f._rule_cache is None:
            f._rule_cache = {f.__name__: [(rule, options)]}
        elif not f.__name__ in f._rule_cache:
            f._rule_cache[f.__name__] = [(rule, options)]
        else:
            f._rule_cache[f.__name__].append((rule, options))

        # Put the _method on the method itself instead of globally
        if not hasattr(f, '_method') or f._method is None:
            f._method = method

        # Put the _route on the method itself instead of globally
        if not hasattr(f, '_route') or f._route is None:
            f._route = options

        return f

    return decorator


class EnableCorsPlugin(object):
    name = 'enable_cors'
    api = 2

    def apply(self, callback, route):

        def wrapper(*args, **kwargs):
            # set CORS headers
            allowed_methods = [m for m in callback._method if m != 'OPTIONS']
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = ", ".join(allowed_methods)

            if request.method == 'OPTIONS':
                response.headers['Access-Control-Max-Age'] = 86400
                response.headers[
                    'Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept, X-Debug-Mode'
            else:
                # actual request; reply with the actual response
                return callback(*args, **kwargs)

        return wrapper


class JSONRPCPlugin(object):
    name = 'json_rpc'
    api  = 2

    def __init__(self, json_dumps=json_dumps):
        self.json_dumps = json_dumps

    def make_error(self, status_code, message):
        response.status = status_code
        PAGE_ERROR_TEMPLATE = '''
        <!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
        <html>
            <head>
                <title>Error: %s</title>
                <style type="text/css">
                  html {background-color: #eee; font-family: sans;}
                  body {background-color: #fff; border: 1px solid #ddd;
                        padding: 15px; margin: 15px;}
                  pre {background-color: #eee; border: 1px solid #ddd; padding: 5px;}
                </style>
            </head>
            <body>
                <h1>Error: %s</h1>
                <p>Sorry, the requested URL <tt>%s</tt>
                   caused an error:</p>
                <pre>%s</pre>
            </body>
        </html>
        ''' % (status_code, status_code, request.url, message)
        return PAGE_ERROR_TEMPLATE

    def apply(self, callback, route):
        dumps = self.json_dumps
        if not dumps: return callback

        def wrapper(*args, **kwargs):
            json_request = None
            json_response = {
                "jsonrpc": "2.0",
                "id": None,
                "result": None
            }

            try:
                json_request = request.json
                if isinstance(json_request, dict) and json_request.has_key('params'):
                    kwargs.update(json_request['params'])
                rv = callback(*args, **kwargs)
            except HTTPError:
                rv = _e()
            except TypeError as message:
                return self.make_error(400, message)
            except ValueError as message:
                return self.make_error(400, message)

            route = callback._route
            if route.get('type') == 'json':
                # build json
                try:
                    if not isinstance(json_request, dict):
                        raise ValueError("Function declared as capable of handling request of type 'json' but called with a request of type 'http'")
                    elif json_request.has_key('id'):
                        json_response['id'] = json_request['id']
                except ValueError as message:
                    return self.make_error(400, message)
                finally:
                    json_response['result'] = rv
                    rv = json_response

            if isinstance(rv, bool):
                rv = str(rv)

            if isinstance(rv, dict):
                #Attempt to serialize, raises exception on failure
                rv = dumps(rv)
                #Set content type only if serialization succesful
                response.content_type = 'application/json'
            elif isinstance(rv, HTTPResponse) and isinstance(rv.body, dict):
                rv.body = dumps(rv.body)
                rv.content_type = 'application/json'

            return rv

        return wrapper


class Controller(object):
    """ Class based view implementation for bottle (following flask-classy architech)
    """
    decorators = []
    DEFAULT_ROUTES = ["get", "put", "post", "delete", "index", "options"]
    base_route = None
    route_prefix = None
    view_identifier = "view"

    @classmethod
    def register(cls, app, base_route=None, route_prefix=None):
        """ Register all the possible routes of the subclass
        :param app: bottle app instance
        :param base_route: prepend to the route rule (/base_route/<class_name OR route_prefix>)
        :param route_prefix: used when want to register custom rule, which is not class name
        """
        if cls is Controller:
            raise TypeError("cls must be a subclass of Controller, not Controller itself")

        cls._app = app
        cls.route_prefix = route_prefix or cls.route_prefix
        cls.base_route = base_route or cls.base_route
        # import ipdb; ipdb.set_trace()
        # get all the valid members of  the class to register Endpoints
        routes = cls._get_interesting_members(Controller)

        # initialize the class
        klass = cls()

        # Iterate through class members to register Endpoints
        for func_name, func in routes:

            method_args = inspect.getargspec(func)[0]
            # Get
            rule = cls._build_route_rule(func_name, *method_args)
            method = "GET"

            if func_name in cls.DEFAULT_ROUTES:
                if func_name == "index":
                    method = "GET"
                else:
                    method = func_name.upper()

            # create name for endpoint
            endpoint = "%s:%s" % (cls.__name__, func_name)
            callable_method = getattr(klass, func_name)
            for decorator in cls.decorators:
                callable_method = decorator(callable_method)

            try:
                custom_rule = func._rule_cache
            except AttributeError:
                method_args = inspect.getargspec(func)[0]
                rule = cls._build_route_rule(func_name, *method_args)
                method = "GET"

                if func_name in cls.DEFAULT_ROUTES:
                    if func_name == "index":
                        method = "GET"
                    else:
                        method = func_name.upper()

                cls._app.route(callback=callable_method, method=method,
                               path=rule, name=endpoint)
            else:
                for cached_rule in custom_rule.values()[0]:
                    rule, options = cached_rule
                    try:
                        method = options.pop("method")
                    except KeyError:
                        method = "GET"

                    try:
                        endpoint = options.pop("name")
                    except KeyError:
                        pass

                    cls._app.route(callback=callable_method, path=rule,
                                   method=method, name=endpoint, **options)


    @classmethod
    def _build_route_rule(cls, func_name, *method_args):

        klass_name = cls.__name__.lower()
        klass_name = (klass_name[:-len(cls.view_identifier)]
                      if klass_name.endswith(cls.view_identifier)
                      else klass_name)

        if not (cls.base_route or cls.route_prefix):
            rule = klass_name
        elif not cls.base_route and cls.route_prefix:
            rule = cls.route_prefix
        elif cls.base_route and not cls.route_prefix:
            rule = "%s/%s" % (cls.base_route, klass_name)
        elif cls.base_route and cls.route_prefix:
            rule = "%s/%s" % (cls.base_route, cls.route_prefix)

        rule_parts = [rule]

        if func_name not in cls.DEFAULT_ROUTES:
            rule_parts.append(func_name.replace("_", "-").lower())

        ignored_rule_args = ['self']
        if hasattr(cls, 'base_args'):
            ignored_rule_args += cls.base_args

        for arg in method_args:
            if arg not in ignored_rule_args:
                rule_parts.append("<%s>" % arg)

        result = "/%s/" % join_paths(*rule_parts)
        result = re.sub(r'(/)\1+', r'\1', result)
        result = re.sub("/{2,}", "/", result)

        return result

    @classmethod
    def _get_interesting_members(cls, base_class):
        """Returns a list of methods that can be routed to"""
        base_members = dir(base_class)
        predicate = inspect.ismethod if _py2 else inspect.isfunction
        all_members = inspect.getmembers(cls, predicate=predicate)
        return [member for member in all_members
                if not member[0] in base_members
                and not not hasattr(member[1], '_method')
                and ((hasattr(member[1], "__self__")
                      and not member[1].__self__ in cls.__class__.__mro__) if _py2 else True)
                and not member[0].startswith("_")]


def join_paths(*path_pieces):
    """Join parts of a url path"""
    # Remove blank strings, and make sure everything is a string
    cleaned_parts = map(str, filter(None, path_pieces))

    return "/".join(cleaned_parts + [""])
