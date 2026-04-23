import tempfile
import shutil
from typing import cast, Optional
import os
from contextlib import contextmanager



#class TempPath:
#    """Writes a BinaryIO in a temporary file to return path (for validators/libraries that require a path)."""
#    def __init__(self, file: BinaryIO, suffix: str = ""):
#        self.file = file
#        self.suffix = suffix
#        self.path = None


#    def __enter__(self) -> str:
        #tmp = tempfile.NamedTemporaryFile(delete=False, suffix=self.suffix)
#        fd, temp_path = tempfile.mkstemp(suffix=self.suffix)
#        os.close(fd)
        #tmp_path = tmp.name
        #tmp.close()
#        try:
#            self.file.seek(0)
#        except Exception:
#            pass
#        try:
            #check_file_exists(self.file)
#            with open(temp_path, "wb") as dst:
#                shutil.copyfileobj(self.file, dst)
#                dst.flush()
#                try:
#                    os.fsync(dst.fileno())
#                except Exception:
#                    pass
#        except Exception as e:
            # cleanup partial file on error
#            try:
#                os.remove(temp_path)
#            except Exception:
#                pass
#        self.path = temp_path
#        return self.path


#    def __exit__(self, exc_type, exc, tb):
#        try:
#            if self.path and os.path.exists(self.path):
#                os.remove(self.path)
#        except Exception:
#            pass

def create_temp_path_inner(file: BinaryIO, suffix: str = ""):
    """Writes a BinaryIO in a temporary file to return path (for validators/libraries that require a path)."""
    # tmp = tempfile.NamedTemporaryFile(delete=False, suffix=self.suffix)
    fd, temp_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    # tmp_path = tmp.name
    # tmp.close()
    try:
        file.seek(0)
    except Exception:
        pass
    try:
        # check_file_exists(self.file)
        with open(temp_path, "wb") as dst:
            shutil.copyfileobj(file, dst)
            dst.flush()
            try:
                os.fsync(dst.fileno())
            except Exception:
                pass
    except Exception as e:
        # cleanup partial file on error
        try:
            os.remove(temp_path)
        except Exception:
            pass

    return temp_path





@contextmanager
def create_temp_path(file=None, suffix=""):
    temp_path = create_temp_path_inner(file=file, suffix=suffix)
    try:
        yield temp_path
    finally:
        try:
            os.remove(temp_path)
        except Exception:
            pass



