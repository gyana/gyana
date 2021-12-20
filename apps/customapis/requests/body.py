from requests import Session

from ..models import CustomApi, FormDataEntry

# discussion of requests files vs data
# https://stackoverflow.com/a/12385661/15425660


def _get_body_for_form_data(session: Session, customapi: CustomApi):
    return {
        "files": {
            f.key: f.text if f.format == FormDataEntry.Format.TEXT else f.file.file
            for f in customapi.formdataentries.all()
        }
    }


def _get_body_for_form_url_encoded(session: Session, customapi: CustomApi):
    return {"data": {f.key: f.value for f in customapi.formdataentries.all()}}


def _get_body_for_raw(session: Session, customapi: CustomApi):
    return {"data": customapi.body_raw}


def _get_body_for_binary(session: Session, customapi: CustomApi):
    return {"data": customapi.body_binary.file}


BODY = {
    CustomApi.Body.NONE: lambda session, customapi: None,
    CustomApi.Body.FORM_DATA: _get_body_for_form_data,
    CustomApi.Body.X_WWW_FORM_URLENCODED: _get_body_for_form_url_encoded,
    CustomApi.Body.RAW: _get_body_for_raw,
    CustomApi.Body.BINARY: _get_body_for_binary,
}


def get_body(session: Session, customapi: CustomApi):
    return BODY[customapi.body](session, customapi)
