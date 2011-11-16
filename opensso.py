# -*- coding: utf-8 -*-

# Python interface to OpenSSO/OpenAM REST API
#
# Code borrowed and reworked from django-opensso by nsb 
# https://github.com/nsb/django-opensso
#
# For detailed usage information please see "The OpenSSO REST Interface in
# Black/White"
# http://blogs.sun.com/docteger/entry/opensso_and_rest
#
# This is not a complete implementation. Only the end-user functionality has
# been included.  None of the administrative methods are implemented... yet.

__author__ = 'Jathan McCollum <jathan+bitbucket@gmail.com>'
__version__ = '0.1.3'

import urllib
import urllib2

# REST API URIs
REST_OPENSSO_LOGIN = '/identity/authenticate'
REST_OPENSSO_LOGOUT = '/identity/logout'
REST_OPENSSO_COOKIE_NAME_FOR_TOKEN = '/identity/getCookieNameForToken'
REST_OPENSSO_COOKIE_NAMES_TO_FORWARD = '/identity/getCookieNamesToForward'
REST_OPENSSO_IS_TOKEN_VALID = '/identity/isTokenValid'
REST_OPENSSO_ATTRIBUTES = '/identity/attributes'


# Exports
__all__ = ('OpenSSO', 'OpenSSOError', 'UserDetails',)


# Exceptions
class OpenSSOError(Exception): pass
class AuthenticationFailure(OpenSSOError): pass


# Classes
class OpenSSO(object):
    """
    OpenSSO Rest Interface
    http://blogs.sun.com/docteger/entry/opensso_and_rest

    Based on django-opensso
    https://github.com/nsb/django-opensso

    Example:
        >>> from opensso import OpenSSO
        >>> rest = RestInterface('https://mydomain.com/opensso')
        >>> token = rest.authenticate('joeblow', 'bogus')
        >>> rest.is_token_valid(token)
        True
        >>> rest.attributes(token).attributes['name']
        'joeblow'
        >>> rest.logou(ttoken)
        >>> rest.is_token_valid(token)
        False
    """
    def __init__(self, opensso_url='',):
        """
        @param opensso_url: the URL to the OpenSSO server
        """
        if not opensso_url:
            raise AttributeError('This interface needs an OpenSSO URL to work!')

        self.opensso_url = opensso_url

    def __repr__(self):
        """So we can see what is inside!"""
        return '{0}({1})'.format(self.__class__.__name__, self.__dict__)

    def _GET(self, urlpath, params=None):
        """
        Wrapper around http_get() to save keystrokes.
        """
        if params is None:
            params = {}
        #data = GET(
        data = http_get(
            ''.join((self.opensso_url, urlpath)), params
        )

        return data

    def authenticate(self, username, password, uri=''):
        """
        Authenticate and return a login token.
        """
        params = {'username':username, 'password':password, 'uri':uri}
        data = self._GET(REST_OPENSSO_LOGIN, params)
        if data == '':
            msg = 'Invalid Credentials for user "{0}".'.format(username)
            raise AuthenticationFailure(msg)

        token = _parse_token(data)

        return token

    def logout(self, subjectid):
        """
        Logout by revoking the token passed. Returns nothing!
        """
        params = {'subjectid':subjectid}
        data = self._GET(REST_OPENSSO_LOGOUT, params)

    def is_token_valid(self, tokenid):
        """
        Validate a token. Returns a boolen.
        """
        params = {'tokenid':tokenid}
        data = self._GET(REST_OPENSSO_IS_TOKEN_VALID, params)

        # 'boolean=true\r\n' or 'boolean=true\n'
        return data.strip() == 'boolean=true'

    def attributes(self, subjectid, attributes_names='uid', **kwargs):
        """
        Read subject attributes. Returns UserDetails object. 
        
        The 'attributes_names' argument doesn't really seem to make a difference
        in return results, but it is included because it is part of the API.  
        """
        params = {'attributes_names':attributes_names, 'subjectid':subjectid}
        if kwargs: 
            params.update(kwargs)
        data = self._GET(REST_OPENSSO_ATTRIBUTES, params)

        attrs = _parse_attributes(data)
        userdetails = UserDetails(attrs)

        return userdetails

    def get_cookie_name_for_token(self, tokenid):
        """
        Returns name of the token cookie that should be set on the client.
        """
        params = {'tokenid':tokenid}
        data = self._GET(REST_OPENSSO_COOKIE_NAME_FOR_TOKEN, params)

        return data.split('=')[1].strip()

    def get_cookie_names_to_forward(self):
        """
        Returns a list of cookie names required by the server. Accepts no arguments.
        """
        data = self._GET(REST_OPENSSO_COOKIE_NAMES_TO_FORWARD)
        # => 'string=iPlanetDirectoryPro\r\nstring=amlbcookie\r\n'

        # Ditch the 'string=' crap and make into a list
        cookie_string = data.replace('string=', '')
        cookie_names = cookie_string.strip().splitlines()

        return cookie_names

class DictObject(object):
    """
    Pass it a dict and now it's an object! Great for keeping variables!
    """
    def  __init__(self, data=None):
        if data is None:
            data = {}
        self.__dict__.update(data)

    def __repr__(self):
        """So we can see what is inside!"""
        return '{0}({1})'.format(self.__class__.__name__, self.__dict__)

class UserDetails(DictObject):
    """
    A dict container to make 'userdetails' keys available as attributes.
    """
    pass


# Functions
def _parse_attributes(data):
    """
    Parse a 'userdetails' key-value blob and return it as a dictionary.
    """
    lines = data.splitlines()

    # The containers we need
    attrs = {}
    attrs['roles'] = []
    attrs['attributes'] = {}

    for i, line in enumerate(lines):
        try:
            this_key, this_value = line.split('=', 1)
        except ValueError:
            continue

        # These are pairs of 'name', 'value' on new lines. Lame.
        if line.startswith('userdetails.attribute.name'):
                next_key, next_value = lines[i + 1].split('=', 1)
                attrs['attributes'][this_value] = next_value

        # A bunch of LDAP-style roles
        if line.startswith('userdetails.role'):
            attrs['roles'].append(this_value)

    return attrs

def _parse_token(data):
    """
    Slice/split the token and return it. Exceptions will fall through.
    """
    # Server returns tokens as 'key=<value>\r\n' or 'key=<value>\n'
    key, value = data.strip().split('=', 1)
    return value

def http_get(url, data):
    """
    Send a simple HTTP GET and attempt to return the response data.
    """
    params = urllib.urlencode(data)
    try:
        resp = urllib2.urlopen(url, params)
    except urllib2.HTTPError:
        return ''

    if resp.code != 200:
        # This exception could probably be more meaningful...
        raise OpenSSOError('Response was not ok for {0}'.format(url))

    data = resp.read()

    return data
