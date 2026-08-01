import mimetypes
import os

import requests

KEY_ID = os.environ["B2_KEY_ID"]
APP_KEY = os.environ["B2_APP_KEY"]
BUCKET_NAME = os.environ["B2_BUCKET"]

_auth = None
_bucket_cache = None


def _authorize():
    global _auth
    if _auth is None:
        r = requests.get(
            "https://api.backblazeb2.com/b2api/v2/b2_authorize_account",
            auth=(KEY_ID, APP_KEY),
        )
        r.raise_for_status()
        _auth = r.json()
    return _auth


def _ensure_bucket():
    global _bucket_cache
    if _bucket_cache is not None:
        return _bucket_cache

    auth = _authorize()
    api_url = auth["apiUrl"]
    token = auth["authorizationToken"]
    account_id = auth["accountId"]

    r = requests.post(
        f"{api_url}/b2api/v2/b2_list_buckets",
        json={"accountId": account_id, "bucketName": BUCKET_NAME},
        headers={"Authorization": token},
    )
    r.raise_for_status()
    buckets = r.json()["buckets"]
    if buckets:
        _bucket_cache = buckets[0]["bucketId"]
        return _bucket_cache

    r = requests.post(
        f"{api_url}/b2api/v2/b2_create_bucket",
        json={
            "accountId": account_id,
            "bucketName": BUCKET_NAME,
            "bucketType": "allPrivate",
        },
        headers={"Authorization": token},
    )
    r.raise_for_status()
    _bucket_cache = r.json()["bucketId"]
    return _bucket_cache


def _upload_data(data, file_name, content_type=None):
    auth = _authorize()
    api_url = auth["apiUrl"]
    token = auth["authorizationToken"]
    bucket_id = _ensure_bucket()

    ct = content_type or "application/octet-stream"
    if file_name.endswith(".srt"):
        ct = "text/plain; charset=utf-8"

    r = requests.post(
        f"{api_url}/b2api/v2/b2_get_upload_url",
        json={"bucketId": bucket_id},
        headers={"Authorization": token},
    )
    r.raise_for_status()
    upload_data = r.json()

    r = requests.post(
        upload_data["uploadUrl"],
        data=data,
        headers={
            "Authorization": upload_data["authorizationToken"],
            "X-Bz-File-Name": file_name,
            "Content-Type": ct,
            "X-Bz-Content-Sha1": "do_not_verify",
        },
    )
    r.raise_for_status()
    return r.json()


def _upload_file(local_path, file_name):
    ct, _ = mimetypes.guess_type(local_path)
    with open(local_path, "rb") as f:
        return _upload_data(f.read(), file_name, content_type=ct)


def get_download_url(key):
    auth = _authorize()
    api_url = auth["apiUrl"]
    token = auth["authorizationToken"]

    r = requests.post(
        f"{api_url}/b2api/v2/b2_get_download_authorization",
        json={
            "bucketId": _ensure_bucket(),
            "fileNamePrefix": key,
            "validDurationInSeconds": 86400,
        },
        headers={"Authorization": token},
    )
    r.raise_for_status()
    dl_token = r.json()["authorizationToken"]
    return f"{auth['downloadUrl']}/file/{BUCKET_NAME}/{key}?Authorization={dl_token}"


def upload(local_path, key):
    _upload_file(local_path, key)
    return get_download_url(key)


def upload_bytes(data, key, content_type=None):
    _upload_data(data, key, content_type=content_type)
    return get_download_url(key)
