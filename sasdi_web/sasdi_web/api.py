from http.client import SWITCHING_PROTOCOLS
import shutil
import mimetypes
import os
import sys                  # standard library
import subprocess

from scipy import signal

from numpy import char

import cv2
import ast
import csv                                  # standard library
import json
import multiprocessing
import time                             # standard library
import numpy as np
from scipy.io import wavfile

from . import helpers, sasdi_functions as sf, video_analysis

from django.http import JsonResponse, HttpResponse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
two_html_space = '&nbsp &nbsp'
four_html_space = '&nbsp &nbsp &nbsp &nbsp'
six_html_space = '&nbsp &nbsp &nbsp &nbsp &nbsp &nbsp'


def putVideos(request):
    input_type = request.POST['type']
    infos_serie_file_path = os.path.join(
        BASE_DIR, "params", "infos_serie.json")
    roi_coord_file_path = os.path.join(
        BASE_DIR, "params", "roi_coord.json")
    send_rois = request.POST["rois"]
    try:
        os.remove(infos_serie_file_path)
    except:
        pass

    try:
        # if not send_rois:
        os.remove(roi_coord_file_path)
    except:
        pass

    if input_type == "series":
        dir_relativePath = json.loads(request.POST['dir_relativePath'])
        videos_data = select_serie(request, dir_relativePath)
        result = videos_data["result"]
        nb_vids = videos_data["nb_vids"]
        file_names_list = videos_data["file_names_list"]
        roi_text = get_roi_text(roi_type="series")
        first_frame_aspect_ratio = ""
        file_name = ""
    else:
        videos_data = select_videos(request, input_type)
        result = videos_data["result"]
        nb_vids = videos_data["nb_vids"]
        file_names_list = videos_data["file_names_list"]
        roi_text = get_roi_text(roi_type="new")
        first_frame_aspect_ratio = helpers.get_aspect_ratio(os.path.join(
            BASE_DIR, 'videos', helpers.get_client_ip(request), "first_frame.jpg"))
        file_name = helpers.get_video_file_name(request)
    roi_coord, message = sf.read_roi_coord()
    if input_type == "series":
        ROIs = roi_coord
        serie_subdir_names = sf.read_infos_serie()
    else:
        serie_subdir_names = []
        try:
            ROIs = roi_coord[0]
        except:
            ROIs = []
    response_data = {
        'result': result,
        'roi_text': roi_text,
        'first_frame_aspect_ratio': first_frame_aspect_ratio,
        'file_name': file_name,
        'rois': ROIs,
        'serie_subdir_names': serie_subdir_names,
        "nb_vids": nb_vids,
        "file_names_list": file_names_list
    }
    return JsonResponse(response_data)


def save_rois(request):
    send_rois = json.loads(request.POST["rois"])
    input_type = request.POST['type']
    if input_type == "series":
        boxes = []
        print("send_rois", send_rois)
        for series in send_rois:
            print("series", series)
            serie = []
            for roi in series:
                print("roi", roi)
                serie.append([(roi[0][0], roi[0][1]), (roi[1][0], roi[1][1])])
            boxes.append(serie)
        print("boxes", boxes)
    else:
        boxes = [[]]
        for roi in send_rois:
            boxes[0].append([(roi[0][0], roi[0][1]), (roi[1][0], roi[1][1])])
    save_roi_coord(boxes)
    roi_coord, message = sf.read_roi_coord()
    roi_text = get_roi_text(roi_type="new")
    if input_type == "series":
        rois = roi_coord
    else:
        rois = roi_coord[0]
    response_data = {
        'roi_text': roi_text,
        'rois': rois,
    }
    return JsonResponse(response_data)


def save_roi_coord(boxes):
    """ INPUT sasdi directory, ROI coordinates,
        SAVE selected ROI coordinates to roi_coord.json
    """
    with open(os.path.join(BASE_DIR, 'params', 'roi_coord.json'), 'w') as filewriter:
        try:
            filewriter.write(json.dumps(boxes, indent=""))
        except IOError as json_error:
            print(f"Error writing roi_coord.json: {json_error}")


def upload_file(f, path):
    with open(path + '\\' + f.name, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)


def select_videos(request, input_type):
    """ INPUT input_type = 'directory' or multiple 'files',
        GET all videos shortnames,
        SAVE directory name to lastdir.txt,
        SAVE infos of valid videos to list_videos.json,
        GET infos in self.list_videos and statistics in self.stats_videos,
        Refresh display in listbox
    """

    # Delete serie file
    # if os.path.isfile(os.path.join(sys.path[0], 'params', 'infos_serie.json')):
    #   os.remove(os.path.join(sys.path[0], 'params', 'infos_serie.json'))
    # Indicate that ROI(s) is from previous selection
    # self.show_roi(roi_type="previous")

    # Clear listbox to display informations
    # self.listbox_files.delete(0, "end")
    # Get serie main directory full path
    main_fullpath = os.path.join(
        BASE_DIR, 'videos', helpers.get_client_ip(request))
    path_exist = os.path.exists(main_fullpath)
    if(path_exist):
        shutil.rmtree(main_fullpath)

    os.makedirs(main_fullpath)

    video_files = []

    if(input_type == 'files'):
        files = request.FILES.getlist('videos_files')

    if(input_type == 'dir'):
        files = request.FILES.getlist('videos_dir')
    # Get max fps value and accepted video files extensions
    _, fps_limit, _, images_extensions_lower, extensions_upper = sf.read_parameters()
    images_extensions = images_extensions_lower + extensions_upper
    video_files = get_video_files_from_dir(files, main_fullpath)
    # Sort list of video short filenames
    video_files.sort()  # sort the list in ascending order
    # Save valid selected videos infos to list_videos.json
    # Get self.list_videos: [0]:video filename, [1]:fps, [2]:nb_frames, [3]:pathname, [4]:index, [5]:status ('A', '-')
    # Get self.stats_videos (int): [0]:total number, [1]:to analyse, [2]:analysed, [3]:corrupted
    list_videos, stats_videos = sf.save_get_list_videos(
        main_fullpath, video_files)
    # Refresh display in listbox
    save_first_frame(os.path.join(main_fullpath, list_videos[0][0]), os.path.join(
        main_fullpath, "first_frame.jpg"))
    return get_video_output_text(list_videos, stats_videos, request)


def select_serie(request, dir_relativePath):
    """ GET main directory path, first level subdirectories and all videos shortnames,
        SAVE main directory full path and then all subdirectories short name to infos_serie.json,
        SAVE directory name to lastdir.txt,
        SAVE infos of valid videos to list_videos.json,
        GET infos in self.list_videos and statistics in self.stats_videos,
        Refresh display in listbox and ROI list
    """

    main_fullpath = os.path.join(
        BASE_DIR, 'videos', helpers.get_client_ip(request))
    path_exist = os.path.exists(main_fullpath)
    if(path_exist):
        shutil.rmtree(main_fullpath)

    os.makedirs(main_fullpath)

    create_series_directories(dir_relativePath, main_fullpath)

    files = request.FILES.getlist('videos_dir')
    files_directories = save_serie_files(
        dir_relativePath, files, main_fullpath)
    print("files_directories", files_directories)

    result = ""
    main_fullpath = os.path.normpath(main_fullpath)
    sf.save_to_lastdir(main_fullpath)
    list_videos, stats_videos, serie_subdir_names = sf.update_serie()
    sf.create_serie_roi()
    # Display serie infos in listbox
    grand_total = 0
    nb_vids = 0
    result += f"  You have selected the serie containing the following subseries: <br>"
    list_first_vids = []
    file_names_list = {}
    for subdir_index, subdir_name in enumerate(serie_subdir_names):
        file_names_list[subdir_name] = []
        for elt in list_videos:
            dir_path = elt[3]
            if dir_path.endswith(subdir_name):
                list_first_vids.append(
                    [os.path.join(dir_path, elt[0]), subdir_name])
                break
        for elt in list_videos:
            dir_path = elt[3]
            if dir_path.endswith(subdir_name):
                if elt[5] == "_":
                    file_names_list[subdir_name].append(elt[0])
        stats = stats_videos[subdir_index]
        grand_total = grand_total + stats[1] + stats[2]
        nb_vids += stats[1]
        result += f" <{subdir_name}>: {stats[0]} total video files with: <br>"
        result += f"{four_html_space} {stats[1]} to analyse (_), <br>"
        result += f"{four_html_space} {stats[2]} already analysed (A), <br>"
        result += f"{four_html_space} {stats[3]} with user modified fps or number of frames (M), <br>"
        result += f"{four_html_space} {stats[4]} corrupted files (C) <br>"
        result += f"{two_html_space}Legend : (status) #index = <subserie> 'filename' (fps, duration) <br>"
        result += two_html_space + \
            "========================================================================== <br>"
        result += two_html_space + \
            "Note that unselecting a video is not permitted within series selection. <br>"
        result += f"{two_html_space}List of found video files : <br>"
    for file_info in list_videos:

        if file_info[1]:
            duration_sec = round(file_info[2] / file_info[1])
        else:
            duration_sec = 0
        # [0]:video filename     [1]:fps        [2]:nb frames    [4]:video index+1      [5]:status          [6]:subdir index
        result += f"({file_info[5]}) #{file_info[4] + 1:<4}= <{serie_subdir_names[file_info[6]]}> '{file_info[0]}' (fps: {file_info[1]}, duration: {sf.format_duration(duration_sec)}) <br>"
    for vid_path in list_first_vids:
        save_first_frame(vid_path[0], os.path.join(
            main_fullpath, vid_path[1], "first_frame.jpg"))
    ans = {
        "result": result,
        "nb_vids": nb_vids,
        "file_names_list": file_names_list
    }

    return ans


def get_video_output_text(list_videos, stats_videos, request):
    main_fullpath = os.path.join(
        BASE_DIR, 'videos', helpers.get_client_ip(request))
    file_names_list = []
    result = ''
    result += 'Selection : <br>'
    result += two_html_space + \
        f'{stats_videos[0]} total video files with: <br>'
    result += six_html_space + f"{stats_videos[1]} to analyse (_), <br>"
    result += six_html_space + f"{stats_videos[2]} already analysed (A), <br>"
    result += six_html_space + \
        f"{stats_videos[3]} with user modified fps or number of frames (M), <br>"
    result += six_html_space + f"{stats_videos[4]} corrupted files (C) <br>"
    result += two_html_space + \
        f"Legend : (status) #index = 'filename' (fps, duration) <br>"
    result += " ========================================================================== <br>"
    result += two_html_space + f"List of found video files: <br>"
    result += "<div id='files_infos_wrap'>"
    for file_info in list_videos:
        if file_info[5] == "_":
            file_names_list.append(file_info[0])

        # [0]:video filename  [1]:fps    # [2]:nb frames [4]:video index+1  [5]:status
        if file_info[1]:
            duration_sec = round(file_info[2] / file_info[1])
        else:
            duration_sec = 0
        result += f"<span class='file_infos'>({file_info[5]}) #{file_info[4] + 1:<4}= '{file_info[0]}' (fps: {file_info[1]}, duration: {sf.format_duration(duration_sec)})</span>"
    result += "</div>"

    ans = {
        "result": result,
        "nb_vids": stats_videos[1],
        "file_names_list": file_names_list,
    }

    return ans


def get_roi_text(roi_type):
    """  Get selected ROIs from roi_coord.json and display in selectbox listRoi
            Argument roi_type : "previous"=using previously saved ROI, "new"=newly selected ROI
    """
    # list with roi (read first element of returned list)
    roi_coord, message = sf.read_roi_coord()
    result = ""
    # Display error message
    if not message:
        result += message + "<br>"
    # Display if no coordinates found
    if not roi_coord:
        result += "No ROI selected <br>"
        return result
    # Start display in ListBox
    # NOT A SERIE DISPLAY
    # ROIs lists are in roi_coord[0]
    if not os.path.exists(os.path.join(BASE_DIR, 'params', 'infos_serie.json')):
        if roi_type == "previous":         # no new ROi selected, using saved one
            result += f" Using {len(roi_coord[0])} previously saved ROI(s) : <br>"
        else:       # using newly selected ROI
            result += f" You have selected {len(roi_coord[0])} ROI(s) : <br>"
        # In both case display list of ROIs
        result += "<br>"
        for i, _ in enumerate(roi_coord[0]):
            result += four_html_space + \
                f"ROI[{i + 1}] --> {' , '.join([str(coord) for coord in roi_coord[0][i]])}<br>"
    # SERIE DISPLAY
    # There is a ROIs list for each subdir roi_coord[0], roi_coord[1, ...]
    else:
        # Get subdirectory shortnames lists
        serie_subdir_names = sf.read_infos_serie()
        # By default using each subserie video dimensions as ROI coordinates
        result += two_html_space + "SERIE ANALYSIS <br>"
        result += two_html_space + \
            "Default ROIs are full size of first valid video for each subserie, standard selection is disabled <br>"
        result += two_html_space + \
            "Click 'Reselect subseries ROIs' if you need to reselect ROIs (max 8), you will be prompted for each subserie. <br>"
        result += two_html_space + \
            "Legend: **Subserie <subserie name>     ROI[roi index] ----> [x_topleft, y_topleft], [x_bottomright, y_bottomright] <br>"
        for subdir_index, subdir_name in enumerate(serie_subdir_names):
            result += f"**Subserie &lt;{subdir_name}&gt; <br>"
            for roi_index, coordinates in enumerate(roi_coord[subdir_index]):
                result += six_html_space + \
                    f"ROI[{roi_index + 1}] ----> {' , '.join([str(coord) for coord in coordinates])} <br>"
    return result


def save_first_frame(video_pathname, image_pathname):
    print("video_pathname", video_pathname)
    print("image_pathname", image_pathname)
    success = False
    # Create image from first valid frame of video, start SelectROI
    count = 0
    while not success and count < 1000:
        try:
            # read first frame
            vidcap = cv2.VideoCapture(video_pathname)
            success, image = vidcap.read()
        except cv2.error as cv2_error:  # Exclude empty video or with read error
            vidcap.release()
            success = False
            print(f"Error reading {video_pathname} : {cv2_error}")
        else:       # video is correctly read
            vidcap.release()
        count += 1
    if not success:
        return "No valid frame found"
    cv2.imwrite(image_pathname, image)
    return 'ok'


def get_first_frame(request):
    try:
        image_fullpath = os.path.join(
            BASE_DIR, 'videos', helpers.get_client_ip(request), 'first_frame.jpg')
        path = open(image_fullpath, 'rb')
        mime_type, _ = mimetypes.guess_type(image_fullpath)
        response = HttpResponse(path, content_type=mime_type)
        response['Content-Disposition'] = "attachment; filename=%s" % image_fullpath
        return response
    except:
        return HttpResponse("Not Found!", content_type='text/plain')


def get_first_serie_frame(request):
    serie_subdir_names = sf.read_infos_serie()
    index = int(request.GET["index"])
    full_path = os.path.join(
        BASE_DIR, 'videos', helpers.get_client_ip(request))
    for subdir_index, subdir_name in enumerate(serie_subdir_names):
        if subdir_index == index:
            image_fullpath = os.path.join(
                full_path, subdir_name, 'first_frame.jpg')
    try:
        path = open(image_fullpath, 'rb')
        mime_type, _ = mimetypes.guess_type(image_fullpath)
        response = HttpResponse(path, content_type=mime_type)
        response['Content-Disposition'] = "attachment; filename=%s" % image_fullpath
        return response
    except:
        return HttpResponse("Not Found!", content_type='text/plain')


def create_series_directories(dir_relativePath, main_fullpath):
    for line in dir_relativePath:
        elts = line.split("/")
        del elts[0]
        elts.pop()
        dir_path = os.path.join(main_fullpath, *elts)
        if(os.path.exists(dir_path)):
            shutil.rmtree(dir_path)
        os.makedirs(dir_path)


def save_serie_files(dir_relativePath, files, main_fullpath):
    result = {}
    i = 0
    for file in files:
        elts = dir_relativePath[i].split("/")
        del elts[0]
        elts.pop()
        # Get max fps value and accepted video files extensions
        _, fps_limit, _, images_extensions_lower, extensions_upper = sf.read_parameters()
        images_extensions = images_extensions_lower + extensions_upper

        dir_path = os.path.join(main_fullpath, *elts)
        if file.name.endswith(images_extensions):
            upload_file(file, dir_path)
        i += 1
    return result


def unselect(request):
    """ Unselect one video file and remove it from list_videos.json and displayed list
    """
    index = int(request.POST["selected_vid_index"])
    type = request.POST["type"]
    if(type == 'files'):
        files = request.FILES.getlist('videos_files')

    if(type == 'dir'):
        files = request.FILES.getlist('videos_dir')
    main_fullpath = os.path.join(
        BASE_DIR, 'videos', helpers.get_client_ip(request))
    video_files = []
    for filename in os.listdir(main_fullpath):
        video_files.append(filename)
    # Sort list of video short filenames
    video_files.sort()  # sort the list in ascending order
    # Save valid selected videos infos to list_videos.json
    # Get self.list_videos: [0]:video filename, [1]:fps, [2]:nb_frames, [3]:pathname, [4]:index, [5]:status ('A', '-')
    # Get self.stats_videos (int): [0]:total number, [1]:to analyse, [2]:analysed, [3]:corrupted
    print("video_files ----------------------->", video_files)
    list_videos, stats_videos = sf.save_get_list_videos(
        main_fullpath, video_files)

    # Get index of selected line
    video = list_videos.pop(index)
    video_fullpath = os.path.join(main_fullpath, video[0])
    list_videos, stats_videos = sf.save_get_list_videos(
        main_fullpath, [info[0] for info in list_videos])
    os.remove(video_fullpath)
    try:
        save_first_frame(os.path.join(main_fullpath, list_videos[0][0]), os.path.join(
            main_fullpath, "first_frame.jpg"))
    except:
        print("error")
    roi_text = get_roi_text(roi_type="new")
    first_frame_aspect_ratio = helpers.get_aspect_ratio(os.path.join(
        BASE_DIR, 'videos', helpers.get_client_ip(request), "first_frame.jpg"))
    file_name = helpers.get_video_file_name(request)

    response_data = {
        'result': get_video_output_text(list_videos, stats_videos, request),
        'roi_text': roi_text,
        'first_frame_aspect_ratio': first_frame_aspect_ratio,
        'file_name': file_name,
    }
    return JsonResponse(response_data)


def get_video_files_from_dir(files, main_fullpath):
    video_files = []
    _, fps_limit, _, images_extensions_lower, extensions_upper = sf.read_parameters()
    images_extensions = images_extensions_lower + extensions_upper
    for f in files:
        if f.name.endswith(images_extensions):
            if(not os.path.exists(os.path.join(main_fullpath, f.name))):
                upload_file(f, main_fullpath)
            video_files.append(f.name)
    return video_files


def start_analysis(request):
    "Initialisation for videos analysis, started with BUTTON START"
    stop = 1
    # Get selected ROIs coordinates in roi_coord
    roi_coord, message = sf.read_roi_coord()
    if message != "":
        return JsonResponse({
            "stop": stop,
            "message": message,
        })

    # Get list of videos
    list_videos, message = sf.read_list_videos()
    if message != "":
        print(message, content_type='text/plain')

    # If videos and ROI coordinates present then start analysis
    if not list_videos:
        return JsonResponse({
            "stop": stop,
            "message": "WARNING: Please select at least one video to analyse",
        })
    elif not roi_coord:
        return JsonResponse({
            "stop": stop,
            "message": "WARNING: Please select at least one ROI",
        })
    else:
        nb_videos, list_videos_to_analyse = get_video_to_analyse(
            request, list_videos, roi_coord)

        if not list_videos_to_analyse and list_videos:
            return JsonResponse({
                "stop": stop,
                "message": 'WARNING: All videos are already analysed, please tick "Allow reanalyse"',
            })
        else:
            # Update listbox
            return JsonResponse({
                "stop": 0,
                "message": f" Starting analysing {nb_videos} video(s)... <br>  See terminal for more informations",
            })


def process_analysis(request):
    roi_coord, _ = sf.read_roi_coord()
    list_videos, _ = sf.read_list_videos()
    nb_videos, list_videos_to_analyse = get_video_to_analyse(
        request, list_videos, roi_coord)
    choice_number_process = request.POST["nb_threads"]
    max_number_threads = multiprocessing.cpu_count()
    # Get present time
    process_start_time = time.time()
    if choice_number_process == "auto":
        # Update auto value
        # 80% of available threads
        number_process = int(max_number_threads * 0.8)
        # Max 1 thread / video to analyse
        number_process = min(
            len(list_videos_to_analyse), number_process)
        print(f" Auto = {number_process} thread(s)")
    else:
        number_process = int(choice_number_process)
    with multiprocessing.Pool(processes=number_process) as pool:
        # Analyse each video in one process
        pool.imap_unordered(func=video_analysis.one_video_analysis,
                            iterable=list_videos_to_analyse
                            )
        pool.close()
        pool.join()
    print("Exiting Main Thread. ANALYSIS FINISHED")
    # Calculate process duration in sec and display it
    fullprocessduration = time.time() - process_start_time
    # Update listbox
    message = "<br><br>"
    message += two_html_space + \
        f" ANALYSIS OF {nb_videos} VIDEO(S) COMPLETED IN {sf.format_duration(int(fullprocessduration))} <br>"
    message += "<br><br>"
    return JsonResponse({
        "message": message,
    })


def get_video_to_analyse(request, list_videos, roi_coord):
    if request.POST["admit_reanalise"]:
        admit_reanalise = 1
    else:
        admit_reanalise = 0
    print(admit_reanalise)
    # Number of videos to analyse
    nb_videos = 0
    list_videos_to_analyse = []
    for video_infos in list_videos:
        # for info: [0]:video filename, [1]:fps, [2]:nb frames, [3]:pathname, [4]:file index, [5]:status ('A', '-', 'M', 'C'), [6]:subdir index
        if video_infos[5] != 'C':
            # csv_fullpathname = os.path.join(video_infos[3], video_infos[0] + ".csv")
            # if self.check_reanalyse.get() == 0 and os.path.exists(csv_fullpathname):
            print(f"DEBUG, video_infos[5]", video_infos[5])
            if admit_reanalise == 0 and video_infos[5] == 'A':
                print("analysed")
                # reanalyse not asked and file already analysed
                continue
            else:
                # For each video file, generate a list with specific infos needed for analysis
                list_videos_to_analyse.append(
                    [video_infos[0], video_infos[1], video_infos[2], video_infos[3], roi_coord[video_infos[6]], nb_videos])
                nb_videos += 1
    # Add total number of videos to analyse to each video list infos
    # [0]:video filename, [1]:fps, [2]:nb frames, [3]:pathname, [4] roi coordinates of corresponding subdir (0 if not a serie), [5]:"to analyse" video index, [6] total number of analysed videos
    list_videos_to_analyse = [infos + [nb_videos]
                              for infos in list_videos_to_analyse]
    return nb_videos, list_videos_to_analyse


def get_chart_data(request):
    index = int(request.GET["index"])
    serie_index = int(request.GET["serie_index"])
    labels = []
    audio_labels = []
    power_labels = []
    datasets = []
    audio_datasets = []
    power_datasets = []
    videos_infos = []
    numbers_cfg = {}
    videos_infos_all, message = sf.read_list_videos()
    if message != '':
        return HttpResponse(message)
    # Initialise index of current video
    videos_current_index = index
    for infos in videos_infos_all:
        # Check that corresponding analysis csv file exists
        if os.path.exists(os.path.join(infos[3], infos[0] + ".csv")):
            videos_infos.append(infos)

    # Get all ROI values of first video in numpy array self.timesec_motion and ROI coordinates from first row
    roi_coord, timesec_motion = open_csv_file(os.path.join(
        videos_infos[videos_current_index][3], videos_infos[videos_current_index][0] + ".csv"))
    timemin = timesec_motion[:, 0] / 60
    timemin_right_limit = timemin[-1]
    motion_upper_limit = np.amax(timesec_motion[:, 1:])
    graph_max_val = round(motion_upper_limit) + 1
    nb_rois = len(roi_coord)
    roi_coord, _ = sf.read_roi_coord()
    if serie_index < 0:
        roi_coord = roi_coord[0]
    else:
        roi_coord = roi_coord[serie_index]

# motion
    numbers_cfg["count"] = graph_max_val
    numbers_cfg["min"] = 0
    numbers_cfg["max"] = graph_max_val - 1
    motion_upper_limit = np.amax(timesec_motion[:, 1:])
    graph_max_val = round(motion_upper_limit) + 1
    for i in timemin:
        labels.append(round(i, 2))
    for i in range(nb_rois):
        datasets.append({
            "label": f"ROI {i+1}",
            "data": [],
        })
        for j in range(len(timesec_motion[:, 1:])):
            datasets[i]["data"].append(
                round(timesec_motion[:, 1:][j][i], 10))

# audio
    input_file = os.path.join(
        videos_infos[videos_current_index][3], videos_infos[videos_current_index][0])
    output_file = input_file[:-3] + "wav"
    if not os.path.isfile(output_file):   # audio file does not already exist
        try:
            print("Generating wav file ...")
            # try extracting audio from current video and save to wav file
            subprocess.check_call("ffmpeg -i " + input_file +
                                  " -map 0:a:0? -ac 1 -ar 2205 -y " + output_file, shell=False)
        except:     # error extracting audio
            print(f"{output_file} file wav creation error")
    else:
        print(f"wav created: {output_file}")
    try:
        rate, axe1_y_values = wavfile.read(output_file)
        axe1_x_values_sec = np.linspace(
            0, axe1_y_values.size / rate, num=axe1_y_values.size)
        # ADD AUDIO PLOT
        axe1_x_values_min = axe1_x_values_sec / 60
        motion_index_left_limit = 0
        # new self.motion_index_right_limit limit in points
        motion_index_right_limit = len(timemin) - 1
        left_time_min = timemin[motion_index_left_limit]
        right_time_min = timemin[motion_index_right_limit]
        audio_index_left_limit = np.nonzero(axe1_x_values_min >= left_time_min)[
            0][0]         # first value >= left limit
        audio_index_right_limit = np.nonzero(axe1_x_values_min <= right_time_min)[
            0][-1]      # last value <=right limit
        audio_values = axe1_y_values[audio_index_left_limit:audio_index_right_limit]
        axe_audio_upper_limit = round(np.amax(audio_values), 2)
        axe_audio_lower_limit = round(np.amin(audio_values), 2)
        for x in axe1_x_values_min:
            audio_labels.append(round(x, 10))
    except:
        audio_values = []
        audio_index_left_limit = 0
        audio_index_right_limit = 0
        axe_audio_upper_limit = 0
        axe_audio_lower_limit = 0

    audio_datasets = [{
        "label": "",
        "data": []
    }]
    for y in audio_values:
        audio_datasets[0]["data"].append(round(y, 10))
    audio_datasets[0]["borderColor"] = "#F00"
    audio_datasets[0]["backgroundColor"] = "#F00"
    audio_datasets[0]["pointRadius"] = 0

# Power
    power_values = []
    power_labels = []
    try:
        sampling_frequency = 1 / (60 * (timemin[2] - timemin[1]))
        sampling_frequency_int = int(round(sampling_frequency, 0))
        for roi_values in timesec_motion.T[1:, :]:
            # return sample frequencies, segment times (indices), spectrogram
            _, time_val, spectro_val = signal.spectrogram(x=roi_values,
                                                          noverlap=0,
                                                          nperseg=sampling_frequency_int,
                                                          )
            power_values.append(np.sum(spectro_val, axis=0))
        power_axe1_y_values = np.transpose(
            np.array(power_values, dtype=np.float32))
        axe_power_upper_limit = np.amax(power_axe1_y_values)
        axe_power_lower_limit = np.amin(power_axe1_y_values)
        power_axe1_x_values_sec = np.array(
            time_val, dtype=np.float32) / sampling_frequency_int
        # ADD POWER PLOTS
        power_axe1_x_values_min = power_axe1_x_values_sec / 60
        axe_power_left_limit = np.amin(power_axe1_x_values_min)
        axe_power_right_limit = np.amax(power_axe1_x_values_min)
        for x in power_axe1_x_values_min:
            power_labels.append(round(x, 10))
    except:
        axe_power_upper_limit = 0
        axe_power_lower_limit = 0
        axe_power_left_limit = 0
        axe_power_right_limit = 0

    power_datasets = []
    #print(f"DEBUG, power_values:", power_values)
    for i in range(nb_rois):
        power_datasets.append({
            "label": f"ROI {i+1}",
            "data": [],
        })
        for elt in power_values[i]:
            power_datasets[i]["data"].append(round(elt, 10))

    data = {
        "labels": str(labels).replace("'", '"'),
        "numbers_cfg": str(numbers_cfg).replace("'", '"'),
        "datasets": str(datasets).replace("'", '"'),
        "timemin_right_limit": str(timemin_right_limit),
        "audio_labels": str(audio_labels).replace("'", '"'),
        "audio_datasets": str(audio_datasets).replace("'", '"'),
        "audio_index_left_limit": str(audio_index_left_limit),
        "audio_index_right_limit": str(audio_index_right_limit),
        "axe_audio_upper_limit": str(axe_audio_upper_limit),
        "axe_audio_lower_limit": str(axe_audio_lower_limit),
        "power_labels": str(power_labels).replace("'", '"'),
        "power_datasets": str(power_datasets).replace("'", '"'),
        "axe_power_upper_limit": str(axe_power_upper_limit),
        "axe_power_lower_limit": str(axe_power_lower_limit),
        "axe_power_left_limit": str(axe_power_left_limit),
        "axe_power_right_limit": str(axe_power_right_limit),
    }

    return JsonResponse(data)


def open_csv_file(file_pathname):
    """ INPUT full pathname of current CSV file containing sasdi analysis results,
        READ,
        RETURN ROI coordinates from first row (list), and all motion analysis values (numpy array)
    """

    # Get all ROI values in list motion_time_sec and ROI coordinates in all_roi_coord
    motion_time_sec = []
    all_roi_coord = []
    firstrow = True
    line = 0
    if os.path.exists(file_pathname):
        with open(file_pathname, newline='') as csvfile:
            filereader = csv.reader(
                csvfile, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for row in filereader:
                if firstrow:    # first row is list of list with ROI coordinates
                    firstrow = False
                    if isinstance(row, list):
                        # patch for former vasd version with 2 tuples only
                        if len(row) == 2 and isinstance(ast.literal_eval(row[0])[0], int):
                            one_roi_coord = []
                            # convert ['(val1, val2)', '(val3, val4)'] to [(val1, val2), (val3, val4)]
                            for pair_of_int in row:
                                one_roi_coord.append(
                                    tuple(ast.literal_eval(pair_of_int)))
                            all_roi_coord.append(one_roi_coord)
                        else:
                            for pair_of_pair in row:
                                one_roi_coord = []
                                # convert list from string format and to list of 2 tuples for each ROI
                                for pair_of_int in ast.literal_eval(pair_of_pair):
                                    one_roi_coord.append(
                                        tuple(pair_of_int))
                                all_roi_coord.append(one_roi_coord)
                    else:   # if error creates a list with tiny coordinates
                        all_roi_coord = [[(1, 1), (2, 2)]]
                        print(
                            f"{file_pathname} error with coordinates reading")

                else:
                    line += 1
                    floatline = [float(val.replace('/0', ''))
                                 for val in row]
                    # Append as float full row = time, valueROI1, valueROI2, ...
                    motion_time_sec.append(floatline)
    else:   # if empty creates list to avoid error
        all_roi_coord = [[(1, 1), (2, 2)]]
        motion_time_sec = [[0, 0], [0, 0], [0, 0], [0, 0]]
        print(f"{file_pathname} does not exists")

    return all_roi_coord, np.array(motion_time_sec, dtype=np.float32)


def refresh(request):
    main_fullpath = sf.read_from_lastdir()
    roi_text = ""
    output_test = ""
    # SERIE DISPLAY: show subserie directories names and number of files
    roi_text = get_roi_text("previous")
    if os.path.exists(os.path.join(sys.path[0], 'params', 'infos_serie.json')):
        # Update serie infos
        list_videos, stats_videos, serie_subdir_names = sf.update_serie()
        if (main_fullpath != "" and serie_subdir_names):
            output_test += f"  You have selected the serie containing the following subseries: <br>"
            for subdir_index, subdir_name in enumerate(self.serie_subdir_names):
                output_test += f" <{subdir_name}>: {stats[0]} total video files with: <br>"
                output_test += f"{four_html_space} {stats[1]} to analyse (_), <br>"
                output_test += f"{four_html_space} {stats[2]} already analysed (A), <br>"
                output_test += f"{four_html_space} {stats[3]} with user modified fps or number of frames (M), <br>"
                output_test += f"{four_html_space} {stats[4]} corrupted files (C) <br>"
                output_test += f"{two_html_space}Legend : (status) #index = <subserie> 'filename' (fps, duration) <br>"
                output_test += two_html_space + \
                    "========================================================================== <br>"
                output_test += two_html_space + \
                    "Note that unselecting a video is not permitted within series selection. <br>"
                output_test += f"{two_html_space}List of found video files : <br>"
            for file_info in list_videos:

                if file_info[1]:
                    duration_sec = round(file_info[2] / file_info[1])
                else:
                    duration_sec = 0
                # [0]:video filename     [1]:fps        [2]:nb frames    [4]:video index+1      [5]:status          [6]:subdir index
                result += f"({file_info[5]}) #{file_info[4] + 1:<4}= <{serie_subdir_names[file_info[6]]}> '{file_info[0]}' (fps: {file_info[1]}, duration: {sf.format_duration(duration_sec)}) <br>"
        else:
            result += {two_html_space} + \
                "***** No videos found, please reselect ********************"
    else:
        list_videos, message = sf.read_list_videos()
        list_videos, stats_videos = sf.save_get_list_videos(
            main_fullpath, [val[0] for val in list_videos])
        output_test += f"{two_html_space}Previously selected videos <br>"
        output_test += (get_video_output_text(list_videos,
                                              stats_videos, request))["result"]

    data = {
        "output_test": output_test,
        "roi_text": roi_text,
    }

    return JsonResponse(data)
