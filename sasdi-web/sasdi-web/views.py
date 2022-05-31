from django.shortcuts import render
from django.http import HttpResponse
import os
import ast
import csv                                  # standard library
import subprocess
import numpy as np
from scipy.io import wavfile
from scipy import signal

from . import helpers, sasdi_functions as sf

# Create your views here.


def index(request):
    context = {
        "file_name": helpers.get_video_file_name(request)
    }
    return render(request, 'index.html', context)


def results(request):
    index = int(request.GET["index"])
    serie_index = int(request.GET["serie_index"])
    videos_infos_all, message = sf.read_list_videos()
    labels = []
    audio_labels = []
    power_labels = []
    datasets = []
    videos_infos = []
    numbers_cfg = {}
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
    #timemin_right_limit = timemin[-1]
    motion_upper_limit = np.amax(timesec_motion[:, 1:])
    graph_max_val = round(motion_upper_limit) + 1
    numbers_cfg["count"] = graph_max_val
    numbers_cfg["min"] = 0
    numbers_cfg["max"] = graph_max_val - 1
    #five_empty_labels = [0, 0, 0, 0, 0]
    #nb_rois = len(roi_coord)
    roi_coord, _ = sf.read_roi_coord()
    if serie_index < 0:
        roi_coord = roi_coord[0]
    else:
        print(roi_coord)
        roi_coord = roi_coord[serie_index]
    '''j = 0
    print(f"DEBUG, timemin:", timemin)
    # for i in np.arange(0, round(timemin_right_limit, 2), 0.01):
    for i in timemin:
        labels.append(round(i, 2))
        # if j % 5 == 0:
        #   labels.extend(five_empty_labels)
    if message != '':
        return HttpResponse(message)
    for i in range(nb_rois):
        datasets.append({
            "label": f"ROI {i+1}",
            "data": [],
        })
        for j in range(len(timesec_motion[:, 1:])):
            datasets[i]["data"].append(round(timesec_motion[:, 1:][j][i], 10))

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
        axe_audio_power_graph_upper_limit = np.amax(np.abs(audio_values))
        has_audio = True
        for x in axe1_x_values_min:
            audio_labels.append(round(x, 10))
    except:
        has_audio = False
        axe_audio_power_graph_upper_limit = 0
        audio_values = []
    audio_max_value = np.amax(audio_values)
    audio_min_value = np.amin(audio_values)
    audio_datasets = [{
        "label": "",
        "data": []
    }]
    for y in audio_values:
        audio_datasets[0]["data"].append(round(y, 10))

    power_values = []
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
        power_axe1_x_values_sec = np.array(
            time_val, dtype=np.float32) / sampling_frequency_int
        # ADD POWER PLOTS
        power_axe1_x_values_min = power_axe1_x_values_sec / 60
        for x in power_axe1_x_values_min:
            power_labels.append(round(x, 10))
    except:
        power_labels = []
    power_max_value = np.amax(power_values)
    power_min_value = np.amin(power_values)
    power_datasets = [{
        "label": "",
        "data": []
    }]
    print(f"DEBUG, power_axe1_y_values:", power_axe1_y_values)'''
    # for val in power_values:
    #    power_datasets[0]["data"].append(round(val[serie_index], 10))

    context = {
        # "timemin_right_limit": timemin_right_limit,
        # "labels": labels,
        # "audio_labels": audio_labels,
        # "power_labels": power_labels,
        # "datasets": str(datasets).replace("'", '\"').replace('\"', '\\"'),
        "index": index,
        # "numbers_cfg": str(numbers_cfg).replace("'", '\"').replace('\"', '\\"'),
        "serie_index": serie_index,
        "roi_coord": roi_coord,
        "filename": videos_infos[videos_current_index][0],        
    }
    return render(request, 'results.html', context)


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
