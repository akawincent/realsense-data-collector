import cv2
import os
import sys
from pathlib import Path
import pyrealsense2 as rs
import numpy as np
print("Environment Ready")

bag_path = Path(sys.argv[1])
assert bag_path.exists()

output_dir = bag_path.with_suffix("")
output_dir.mkdir(parents=True, exist_ok=True)

depth_t_path = output_dir / "depth.txt"
rgb_t_path = output_dir / "rgb.txt"

depth_path = output_dir / "depth"
rgb_path = output_dir / "rgb"

depth_path.mkdir(parents=True, exist_ok=True)
rgb_path.mkdir(parents=True, exist_ok=True)

exposure_time_file = output_dir / "exposure_time.txt"
sensor_time_file = output_dir / "sensor_timestamp.txt"
depth_scale_file = output_dir / "depth_scale.txt"

# Setup:
pipe = rs.pipeline()
cfg = rs.config()
cfg.enable_device_from_file(str(bag_path), repeat_playback=False)
profile = pipe.start(cfg)

# Getting the depth sensor's depth scale (see rs-align example for explanation)
depth_sensor = profile.get_device().first_depth_sensor()
depth_scale = 1. / depth_sensor.get_depth_scale()
print("Depth Scale is: " , depth_scale)
with open(depth_scale_file, 'w') as f:
    f.write(f"{depth_scale}\n")

# Skip first 10 frames
for x in range(10):
    pipe.wait_for_frames()

# # We will be removing the background of objects more than
# #  clipping_distance_in_meters meters away
# clipping_distance_in_meters = 1
# clipping_distance = clipping_distance_in_meters / depth_scale

# Create an align object
# rs.align allows us to perform alignment of depth frames to others frames
# The "align_to" is the stream type to which we plan to align depth frames.
align_to = rs.stream.color
align = rs.align(align_to)


# Streaming loop
try:
    while True:
        # Get frameset of color and depth
        frames = pipe.wait_for_frames()
        # frames.get_depth_frame() is a 640x360 depth image

        # Align the depth frame to color frame
        aligned_frames = align.process(frames)

        # Get aligned frames
        aligned_depth_frame = aligned_frames.get_depth_frame() # aligned_depth_frame is a 640x480 depth image
        color_frame = aligned_frames.get_color_frame()

        # Validate that both frames are valid
        if not aligned_depth_frame or not color_frame:
            continue

        depth_image = np.asanyarray(aligned_depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())
        # color_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)

        # # Remove background - Set pixels further than clipping_distance to 0
        # bg_color = 0
        # depth_image_3d = np.dstack((depth_image,depth_image,depth_image)) #depth image is 1 channel, color is 3 channels
        # bg_removed = np.where((depth_image_3d > clipping_distance) | (depth_image_3d <= 0), bg_color, color_image)

        # # Render images:
        # #   depth align to color on left
        # #   depth on right
        # depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
        # images = np.hstack((bg_removed, depth_colormap))

        # cv2.namedWindow('Align Example', cv2.WINDOW_NORMAL)
        # cv2.imshow('Align Example', images)
        # key = cv2.waitKey(1)
        # # Press esc or 'q' to close the image window
        # if key & 0xFF == ord('q') or key == 27:
        #     cv2.destroyAllWindows()
        #     break
        
        ######### Timestamps ########
        # Sensor(optical)_timestamp is a Firmware-generated timestamp that marks middle of sensor exposure.
        # Frame_timestamp - Generated in FW; designates the beginning of UVC frame transmission. (the first USB chunk sent towards host).
        # Sensor_timestamp and Frame_timestamp share the same clock and require the kernel patch for Video4Linux and registry patch for Windows OS.
        #
        # Backend_timestamp - Host clock applied to kernel-space buffers (URB) when the data from USB controller is copied to OS kernel. (HW->Kernel transition)
        # Time_of_arrival - Host clock for the time when the frame buffer reaches Librealsense (kernel->user space transition).
        #
        # The relations hold:
        # Sensor_timestamp << Frame_timestamp.
        # Backend_timestamp << Time_of_arrival.
        #
        # The clocks of the first pair of timestamps and the second pairs are not related.
        # Ref: https://github.com/IntelRealSense/librealsense/issues/12058

        stamp_sensor = frames.get_frame_metadata(rs.frame_metadata_value.sensor_timestamp) / 1e6
        stamp_frame = frames.get_frame_metadata(rs.frame_metadata_value.backend_timestamp) / 1e3
        timestr = f"{stamp_frame:.8f}"
        image_name = f"{timestr}.png"

        with open(depth_t_path,'a') as file:
            file.write(f"{timestr} depth/{image_name}\n")
        cv2.imwrite(str(depth_path / image_name), depth_image)
        print(depth_path / image_name)

        with open(rgb_t_path,'a') as file:
            file.write(f"{timestr} rgb/{image_name}\n")
        cv2.imwrite(str(rgb_path / image_name), color_image)
        print(rgb_path / image_name)

        ###### sensor timestamp #####
        with open(sensor_time_file, 'a') as file:
            file.write(f"{timestr} {stamp_sensor:.8f}\n")

        ###### exposure time #####
        exposure_t = color_frame.get_frame_metadata(rs.frame_metadata_value.actual_exposure)
        with open(exposure_time_file, 'a') as file:
            file.write(f"{timestr} {exposure_t}\n")

finally:
    pipe.stop()