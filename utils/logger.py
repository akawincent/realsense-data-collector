import os
import pyrealsense2 as rs

def save_sensor_intrinsics(pipeline_profile: rs.pipeline_profile, stream_type: rs.stream):
    stream_profile = pipeline_profile.get_stream(stream_type)
    video_stream_profile = stream_profile.as_video_stream_profile()
    sensor_intrinsics = video_stream_profile.get_intrinsics()
    
    dir = os.path.expanduser("./sensor_intrinsics_info")
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

def save_timestamps(ts):
    dir = os.path.expanduser("./timestamps")
    os.makedirs(dir, exist_ok=True)
    f = os.path.join(dir, "frame_timestamps.txt")
    with open(f, "a") as file:
        file.write(str(ts) + "\n")
        # file.close()

            
            
            

