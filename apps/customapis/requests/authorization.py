from requests import Session
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from ..models import CustomApi


def _get_authorization_for_api_key(session: Session, customapi: CustomApi):
    key_value = {customapi.api_key_key: customapi.api_key_value}
    if customapi.api_key_add_to == CustomApi.ApiKeyAddTo.HTTP_HEADER:
        session.headers.update(key_value)
    else:
        session.params.update(key_value)


def _get_authorization_for_bearer_token(session: Session, customapi: CustomApi):
    session.headers.update({"Authorization": f"Bearer {customapi.bearer_token}"})


def _get_authorization_for_basic_auth(session: Session, customapi: CustomApi):
    session.auth = HTTPBasicAuth(customapi.username, customapi.password)


def _get_authorization_for_digest_auth(session: Session, customapi: CustomApi):
    session.auth = HTTPDigestAuth(customapi.username, customapi.password)


AUTHORIZATION = {
    CustomApi.Authorization.NO_AUTH: lambda session, customapi: None,
    CustomApi.Authorization.API_KEY: _get_authorization_for_api_key,
    CustomApi.Authorization.BEARER_TOKEN: _get_authorization_for_bearer_token,
    CustomApi.Authorization.BASIC_AUTH: _get_authorization_for_basic_auth,
    CustomApi.Authorization.DIGEST_AUTH: _get_authorization_for_digest_auth,
    # authorization is handled internally by OAuth2Session
    CustomApi.Authorization.OAUTH2: lambda session, customapi: None,
}


def get_authorization(session: Session, customapi: CustomApi):
    AUTHORIZATION[customapi.authorization](session, customapi)
