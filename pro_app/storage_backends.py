# from django.core.files.storage import Storage
# from supabase import create_client
# from django.conf import settings
# from django.core.files.base import ContentFile

# class SupabaseStorage(Storage):
#     def __init__(self, bucket=None, root_path=None):
#         self.bucket = bucket or settings.SUPABASE_BUCKET
#         self.root_path = root_path or ''
#         self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

#     def _full_path(self, name):
#         return f"{self.root_path}{name}"

#     def _open(self, name, mode='rb'):
#         path = self._full_path(name)
#         res = self.client.storage.from_(self.bucket).download(path)
#         return ContentFile(res, name=name)

#     def _save(self, name, content):
#         path = self._full_path(name)
#         self.client.storage.from_(self.bucket).upload(path, content.file, {'content-type': content.content_type})
#         return name

#     def delete(self, name):
#         path = self._full_path(name)
#         self.client.storage.from_(self.bucket).remove([path])

#     def exists(self, name):
#         path = self._full_path(name)
#         try:
#             self.client.storage.from_(self.bucket).get_public_url(path)
#             return True
#         except:
#             return False

#     def url(self, name):
#         path = self._full_path(name)
#         return f"{settings.SUPABASE_URL}/storage/v1/object/public/{self.bucket}/{path}"



from django.core.files.storage import Storage
from supabase import create_client
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.deconstruct import deconstructible

@deconstructible  # <-- Add this decorator
class SupabaseStorage(Storage):
    def __init__(self, bucket=None, root_path=None):
        self.bucket = bucket or settings.SUPABASE_BUCKET
        self.root_path = root_path or ''
        self.client = None  # Don't initialize client here (lazy loading)

    def _get_client(self):
        if not self.client:
            self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        return self.client

    def _full_path(self, name):
        return f"{self.root_path}{name}"

    def _open(self, name, mode='rb'):
        path = self._full_path(name)
        res = self._get_client().storage.from_(self.bucket).download(path)
        return ContentFile(res, name=name)

    def _save(self, name, content):
        path = self._full_path(name)
        self._get_client().storage.from_(self.bucket).upload(path, content.file, {'content-type': content.content_type})
        return name

    def delete(self, name):
        path = self._full_path(name)
        self._get_client().storage.from_(self.bucket).remove([path])

    def exists(self, name):
        path = self._full_path(name)
        try:
            self._get_client().storage.from_(self.bucket).get_public_url(path)
            return True
        except:
            return False

    def url(self, name):
        path = self._full_path(name)
        return f"{settings.SUPABASE_URL}/storage/v1/object/public/{self.bucket}/{path}"