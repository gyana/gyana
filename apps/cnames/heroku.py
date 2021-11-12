from honeybadger import honeybadger
from requests.models import HTTPError

from apps.base import clients

from .models import CName

# https://devcenter.heroku.com/articles/automated-certificate-management#view-your-certificate-status

HEROKU_DOMAIN_STATE_TO_ICON = {
    "cert issued": "fa fa-check text-green",
    "in progress": "fa fa-spinner-third fa-spin",
    "dns verified": "fa fa-spinner-third fa-spin",
    "waiting": "fa fa-spinner-third fa-spin",
    "failing": "fa fa-exclamation-circle text-orange",
    "failed": "fa fa-times text-red",
}

HEROKU_DOMAIN_STATE_TO_MESSAGE = {
    "cert issued": "A certificate has been issued for the domain.",
    "in progress": "We are verifying your custom domain’s DNS",
    "dns verified": "We have verified your custom domain’s DNS and are in the process of generating the certificate",
    "waiting": "We are currently waiting to process your certificate",
    "failing": "We are unable to verify your DNS. We will keep trying to verify for up to an hour. Reach out to support if you need help.",
    "failed": "We are unable to verify your DNS. We have stopped trying to verify this domain. Reach out to support if you need help.",
}


def create_heroku_domain(cname: CName):
    # https://github.com/martyzz1/heroku3.py/blob/master/README.rst#domains
    clients.heroku().add_domain(cname.domain, None)


def get_heroku_domain_status(cname: CName):
    domain = clients.heroku().get_domain(cname.domain)
    return domain.acm_status or "waiting"


def delete_heroku_domain(cname: CName):
    try:
        clients.heroku().get_domain(cname.domain).remove()
    except HTTPError as e:
        honeybadger.notify(e)
        pass
