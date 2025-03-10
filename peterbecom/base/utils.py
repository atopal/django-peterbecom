import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from django.conf import settings


def get_base_url(request):
    base_url = ["http"]
    if request.is_secure():
        base_url.append("s")
    base_url.append("://")
    x_forwarded_host = request.headers.get("X-Forwarded-Host")
    if x_forwarded_host and x_forwarded_host in settings.ALLOWED_HOSTS:
        base_url.append(x_forwarded_host)
    else:
        base_url.append(request.get_host())
    return "".join(base_url)


def requests_retry_session(
    retries=4, backoff_factor=0.4, status_forcelist=(500, 502, 504), session=None
):
    """Opinionated wrapper that creates a requests session with a
    HTTPAdapter that sets up a Retry policy that includes connection
    retries.

    If you do the more naive retry by simply setting a number. E.g.::

        adapter = HTTPAdapter(max_retries=3)

    then it will raise immediately on any connection errors.
    Retrying on connection errors guards better on unpredictable networks.
    From http://docs.python-requests.org/en/master/api/?highlight=retries#requests.adapters.HTTPAdapter
    it says: "By default, Requests does not retry failed connections."

    The backoff_factor is documented here:
    https://urllib3.readthedocs.io/en/latest/reference/urllib3.util.html#urllib3.util.retry.Retry
    A default of retries=3 and backoff_factor=0.3 means it will sleep like::

        [0.3, 0.6, 1.2]
    """  # noqa
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
