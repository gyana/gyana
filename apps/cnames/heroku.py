from honeybadger import honeybadger
from requests.models import HTTPError

from apps.base.clients import heroku_client

from .models import CName


def create_heroku_domain(cname: CName):
    heroku_client().add_domain(cname.domain)


def get_heroku_domain_status(cname: CName):
    domain = heroku_client().get_domain(cname.domain)
    return domain.acm_status


def delete_heroku_domain(cname: CName):
    try:
        heroku_client().get_domain(cname.domain).remove()
    except HTTPError as e:
        honeybadger.notify(e)
        pass
