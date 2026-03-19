from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse_lazy

# Utility functions for user authentication and authorization


def authenticated(request, groups: list[str] = None) -> bool:
    """
    Check if the user belongs to any of the specified groups.

    Args:
        request: The HTTP request object containing the user.
        groups: A list of group names to check against. Defaults to ['MarDID Maintainers'].

    Returns:
        bool: True if the user belongs to any of the specified groups, False otherwise.
    """
    if groups is None:
        groups = ['MarDID Maintainers']

    if request.user.groups.filter(name__in=groups).exists():
        return True

    return False


def redirect_if_not_authenticated(request, next_page, groups: list[str] = None) -> HttpResponse | None:
    """
    Redirect the user to the login page if they are not authenticated.

    Args:
        request: The HTTP request object containing the user.
        next_page: The URL to redirect to after successful login.
        groups: A list of group names to check against. Defaults to ['MarDID Maintainers'].

    Returns:
        HttpResponseRedirect: A redirect response to the login page if the user is not authenticated.
        None: If the user is authenticated.
    """
    if not authenticated(request, groups):
        login_url = f"{reverse_lazy('login')}?next={next_page}"
        return HttpResponseRedirect(login_url)

    return None


def redirect_if_not_superuser(request, next_page, groups: list[str] = None) -> HttpResponse | None:
    """
    Redirect the user to the login page if they are not authenticated.
    If they are authenticated but not a superuser, return a forbidden response.

    Args:
        request: The HTTP request object containing the user.
        next_page: The URL to redirect to after successful login.
        groups: A list of group names to check against. Defaults to ['MarDID Maintainers'].

    Returns:
        HttpResponseRedirect: A redirect response to the login page if the user is not authenticated.
        HttpResponseForbidden: A response object indicating the user does not have permission.
        None: If the user is authenticated and is a superuser.
    """
    if response := redirect_if_not_authenticated(request, next_page, groups):
        return response

    if not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to access this resource.")

    return None