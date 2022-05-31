from PIL import Image
import os
from os import walk
from . import sasdi_functions as sf
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_aspect_ratio(image_path):
    im = Image.open(image_path)
    width, height = im.size
    return width / height

def get_video_file_name(request):
    main_fullpath = os.path.join(BASE_DIR, 'videos', get_client_ip(request))
    _, _, filenames = next(walk(main_fullpath), (None, None, []))
    list_videos, _ = sf.save_get_list_videos(main_fullpath, filenames) 
    try:
        print(list_videos[0][0])
        return list_videos[0][0]
    except:
        return ""

