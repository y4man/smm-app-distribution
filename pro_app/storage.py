# pro_app/utils/storage.py
import os
import tempfile

from django.conf import settings
from supabase import create_client, Client as SupabaseClient
from storage3.exceptions import StorageApiError

# initialize once
_supabase: SupabaseClient = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_KEY,
)
storage = _supabase.storage.from_(settings.SUPABASE_BUCKET)

def save_file_to_supabase(
    uploaded_file,
    folder: str,
    target_key: str | None = None
) -> str:
    """
    - If target_key is given (a prior key), we overwrite that.
    - Otherwise we upload to folder/<filename>.
    Returns a clean bucket-path (no leading slash).
    """
    if target_key:
        # ensure no leading slash
        path_in_bucket = target_key.lstrip('/')
    else:
        path_in_bucket = f"{folder}/{uploaded_file.name}"

    tmp_path = None
    try:
        # dump to temp
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            for chunk in uploaded_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        # if overwriting existing key...
        if target_key:
            try:
                storage.update(
                    file=tmp_path,
                    path=path_in_bucket,
                    file_options={"content-type": uploaded_file.content_type},
                )
            except StorageApiError as exc:
                raw = exc.args[0] if exc.args else {}
                # if it wasn’t there, fall back to upload
                if isinstance(raw, dict) and raw.get("statusCode") == 404:
                    storage.upload(
                        file=tmp_path,
                        path=path_in_bucket,
                        file_options={"content-type": uploaded_file.content_type},
                    )
                else:
                    raise
        else:
            # brand-new upload
            storage.upload(
                file=tmp_path,
                path=path_in_bucket,
                file_options={"content-type": uploaded_file.content_type},
            )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return path_in_bucket