import os
import shutil
import zipfile
import tempfile
import urllib.request
from urllib.parse import urlparse

def copy_file(src_url: str, dest_dir: str):
    """Handle file:// scheme (local files or directories)."""
    parsed = urlparse(src_url)
    src_path = parsed.path

    if not os.path.exists(src_path):
        raise FileNotFoundError(f"Source path not found: {src_path}")

    if os.path.isdir(src_path):
        dest_path = os.path.join(dest_dir, os.path.basename(src_path))
        shutil.copytree(src_path, dest_path)
    else:
        if zipfile.is_zipfile(src_path):
            with zipfile.ZipFile(src_path, 'r') as zip_ref:
                zip_ref.extractall(dest_dir)
        else:
            shutil.copy(src_path, dest_dir)

def copy_http(src_url: str, dest_dir: str):
    """Handle http(s):// scheme (assumed to be a downloadable file, typically zip)."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        with urllib.request.urlopen(src_url) as response:
            tmp_file.write(response.read())
            tmp_file_path = tmp_file.name

    if zipfile.is_zipfile(tmp_file_path):
        with zipfile.ZipFile(tmp_file_path, 'r') as zip_ref:
            zip_ref.extractall(dest_dir)
    else:
        filename = os.path.basename(urlparse(src_url).path)
        shutil.move(tmp_file_path, os.path.join(dest_dir, filename))

def copy_file_or_directory(src: str, dest: str):
    """Dispatch to appropriate scheme-specific function."""
    parsed = urlparse(src)
    scheme = parsed.scheme

    os.makedirs(dest, exist_ok=True)

    if scheme == 'file':
        copy_file(src, dest)
    elif scheme in ('http', 'https'):
        copy_http(src, dest)
    else:
        raise ValueError(f"Unsupported URL scheme: {scheme}")
