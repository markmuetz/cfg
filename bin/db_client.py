import os
from pathlib import Path

import dropbox
from tqdm import tqdm

ACCESS_TOKEN = (Path.home() / Path('.dropbox/ACCESS_TOKEN')).read_text().strip()


class DropboxClient:
    CHUNK_SIZE = 4 * 1024 * 1024

    def __init__(self):
        self.dbx = dropbox.Dropbox(ACCESS_TOKEN)

    def upload(self, local_path, db_path, overwrite=False):
        mode = (dropbox.files.WriteMode.overwrite
                if overwrite
                else dropbox.files.WriteMode.add)

        try:
            folder_metadata = self.dbx.files_get_metadata(db_path)
            if isinstance(folder_metadata, dropbox.files.FolderMetadata):
                db_path = Path(db_path) / Path(local_path).name
        except dropbox.exceptions.ApiError:
            pass

        # Check dropbox path already exists:
        db_folder = str(Path(db_path).parent)
        try:
            folder_metadata = self.dbx.files_get_metadata(db_folder)
            assert isinstance(folder_metadata, dropbox.files.FolderMetadata), f'{db_folder} is not a folder'
        except dropbox.exceptions.ApiError:
            print(f'Folder {db_folder} does not exist - not creating')
            return None

        print(f'Upload: {local_path} -> {db_path}')

        with open(local_path, 'rb') as f:
            file_size = os.path.getsize(local_path)
            if file_size <= self.CHUNK_SIZE:
                print(self.dbx.files_upload(f.read(), db_path))
            else:
                with tqdm(total=file_size, desc='Uploaded') as pbar:
                    upload_session_start_result = self.dbx.files_upload_session_start(
                        f.read(self.CHUNK_SIZE)
                    )
                    pbar.update(self.CHUNK_SIZE)
                    cursor = dropbox.files.UploadSessionCursor(
                        session_id=upload_session_start_result.session_id,
                        offset=f.tell(),
                    )
                    commit = dropbox.files.CommitInfo(path=db_path, mode=mode, mute=True)
                    while f.tell() < file_size:
                        if (file_size - f.tell()) <= self.CHUNK_SIZE:
                            print(
                                self.dbx.files_upload_session_finish(
                                    f.read(self.CHUNK_SIZE), cursor, commit
                                )
                            )
                        else:
                            self.dbx.files_upload_session_append_v2(
                                f.read(self.CHUNK_SIZE),
                                cursor,
                            )
                            cursor.offset = f.tell()
                        pbar.update(self.CHUNK_SIZE)

    def download(self, db_path, local_path=None):
        if local_path == None:
            local_path = Path(db_path).name
        if Path(local_path).is_dir():
            local_path = Path(local_path) / Path(db_path).name
        print(f'Download: {db_path} -> {local_path}')
        print(self.dbx.files_download_to_file(local_path, db_path))
