# -*- coding: utf-8 -*-

import functools
import collections

import flask

BreadCrumb = collections.namedtuple('BreadCrumb', ['path', 'title'])

def breadcrumb(view_title, root=False):
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Put title into flask.g so views have access and
            # don't need to repeat it
            flask.g.title = view_title
            # Also put previous breadcrumbs there, ready for view to use
            session_crumbs = flask.session.setdefault('crumbs', [])
            flask.g.breadcrumbs = []
            if root == False:
                flask.session.modified = True
                session_crumbs.append((flask.request.path, view_title))
                for path, title in session_crumbs:
                    if not BreadCrumb(path, title) in flask.g.breadcrumbs:
                        flask.g.breadcrumbs.append(BreadCrumb(path, title))
                    if flask.request.path == path:
                        break
            else:
                session_crumbs.clear()

            # Call the view
            rv = f(*args, **kwargs)

            # Now add the request path and title for that view
            # to the list of crumbs we store in the session.
            flask.session.modified = True
            session_crumbs.append((flask.request.path, view_title))
            # Only keep most recent crumbs (number should be configurable)
            if len(session_crumbs) > 2:
                session_crumbs.pop()

            return rv
        return decorated_function
    return decorator