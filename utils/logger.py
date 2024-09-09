import os
import time
import threading
import pyrealsense2 as rs

timestr = time.strftime("%Y%m%d-%H%M%S")
WORK_DIR = os.path.expanduser("./bags/yakitori1_" + timestr)

class ExposureTimeSaver:
    def __init__(self):
        self.dir_path = WORK_DIR
        self.file_path = os.path.join(self.dir_path, "exposure_times.txt")
        self.lock = threading.Lock()
        self.file = None
        if os.path.isfile(self.file_path):
            os.remove(self.file_path)

    def _open_file(self):
        # Open the file with append mode
        if self.file is None:
            self.file = open(self.file_path, "a")

    def _close_file(self):
        # Close the file if it's open
        if self.file is not None:
            self.file.close()
            self.file = None

    def save_exposure_time(self, ts):
        # Ensure the directory exists
        os.makedirs(self.dir_path, exist_ok=True)

        with self.lock:
            # Open file
            self._open_file()
            # Write the exposure time
            self.file.write("{:.2f}".format(ts) + "\n")
            # Ensure the file is properly closed
            self._close_file()

class TimeStampSaver:
    def __init__(self):
        self.dir_path = WORK_DIR
        self.file_path = os.path.join(self.dir_path, "timestamps.txt")
        self.lock = threading.Lock()
        self.file = None
        if os.path.isfile(self.file_path):
            os.remove(self.file_path)

    def _open_file(self):
        # Open the file with append mode
        if self.file is None:
            self.file = open(self.file_path, "a")

    def _close_file(self):
        # Close the file if it's open
        if self.file is not None:
            self.file.close()
            self.file = None

    def save_timestamps(self, ts):
        # Ensure the directory exists
        os.makedirs(self.dir_path, exist_ok=True)

        with self.lock:
            # Open file
            self._open_file()
            # Write the exposure time
            self.file.write("{:.2f}".format(ts) + "\n")
            # Ensure the file is properly closed
            self._close_file()

def save_sensor_intrinsics(pipeline_profile: rs.pipeline_profile, stream_type: rs.stream):
    stream_profile = pipeline_profile.get_stream(stream_type)
    video_stream_profile = stream_profile.as_video_stream_profile()
    sensor_intrinsics = video_stream_profile.get_intrinsics()

    dir = WORK_DIR
    os.makedirs(dir, exist_ok=True)

    if stream_type == rs.stream.color:
        f = os.path.join(dir, "color_sensor_intrinsics.txt")
        with open(f, "w") as file:
            file.write("sensor_type: \"color_sensor\"\n")
            file.write("distortion_model: " + "\"" + str(sensor_intrinsics.model) + "\"" + "\n")
            file.write("distortion_coeffs: " + str(sensor_intrinsics.coeffs) + "\n")
            file.write("width: " + str(sensor_intrinsics.width) + "\n")
            file.write("height: " + str(sensor_intrinsics.height) + "\n")
            file.write("fx: " + str(sensor_intrinsics.fx) + "\n")
            file.write("fy: " + str(sensor_intrinsics.fy) + "\n")
            file.write("cx: " + str(sensor_intrinsics.ppx) + "\n")
            file.write("cy: " + str(sensor_intrinsics.ppy) + "\n")
            file.close()

def set_record_to_bag_file(config: rs.config):
    dir = WORK_DIR
    os.makedirs(dir, exist_ok=True)
    config.enable_record_to_file(os.path.join(dir, "data.bag"))
