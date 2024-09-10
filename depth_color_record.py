import os
import cv2
import numpy as np
import pyrealsense2 as rs

from utils import viewer
from utils import logger
from auto_exposure import AE
from colorama import Fore, Style, init

if __name__ == "__main__":
    pipeline = rs.pipeline()
    config = rs.config()

    # config
    pipeline_wrapper = rs.pipeline_wrapper(pipeline)
    pipeline_profile = config.resolve(pipeline_wrapper)
    device = pipeline_profile.get_device()
    device_product_line = str(device.get_info(rs.camera_info.product_line))
    print("[INFO] Device type:",device_product_line)

    # check sensor
    found_rgb = False
    found_depth = False
    found_imu = False
    rgb_sensor_index = None
    depth_sensor_index = None
    imu_sensor_index = None
    for i, s in enumerate(device.query_sensors()):
        print("[INFO] Sensor name:", s)
        if s.get_info(rs.camera_info.name) == 'RGB Camera':
            found_rgb = True
            rgb_sensor_index = i
            print("[INFO] RGB camera sensor is sucessfully detected!")
        if s.get_info(rs.camera_info.name) == 'Stereo Module':
            found_depth = True
            depth_sensor_index = i
            print("[INFO] Depth camera sensor is sucessfully detected!")
        if s.get_info(rs.camera_info.name) == 'Motion Module':
            found_imu = True
            imu_sensor_index = i
            print("[INFO] Motion sensor is sucessfully detected!")
        else:
            pass
    if not found_rgb:
        print("[ERROR] Can't find RGB camera sensor!")
        exit(0)
    if not found_depth:
        print("[ERROR] Can't find Depth camera sensor!")
        exit(0)
    if not found_imu:
        print("[ERROR] Can't find motion sensor!")
        exit(0)

    # setting for streams
    framerate = 30
    image_resolution = [640, 480]
    config.enable_stream(rs.stream.color, image_resolution[0], image_resolution[1], rs.format.bgr8, framerate)
    config.enable_stream(rs.stream.depth, image_resolution[0], image_resolution[1], rs.format.z16, framerate)

    # Initialize logger
    timestamps_saver = logger.TimeStampSaver()
    logger.set_record_to_bag_file(config)
    logger.save_sensor_intrinsics(pipeline_profile, rs.stream.color)
    logger.save_sensor_intrinsics(pipeline_profile, rs.stream.depth)

    # set sensor option
    color_sensor = pipeline_profile.get_device().query_sensors()[rgb_sensor_index]
    color_sensor.set_option(rs.option.enable_auto_exposure, False)
    color_sensor.set_option(rs.option.enable_auto_white_balance, False)
    color_sensor.set_option(rs.option.power_line_frequency, 1)
    color_sensor.set_option(rs.option.global_time_enabled, 1)
    color_sensor.set_option(rs.option.exposure, 100)

    depth_sensor = pipeline_profile.get_device().first_depth_sensor()
    depth_sensor.set_option(rs.option.enable_auto_exposure, False)
    # depth_sensor.set_option(rs.option.enable_auto_white_balance, False)
    # depth_sensor.set_option(rs.option.power_line_frequency, 1)
    depth_sensor.set_option(rs.option.global_time_enabled, 1)
    depth_sensor.set_option(rs.option.exposure, 100)

    #depth scale
    depth_scale = depth_sensor.get_depth_scale()
    print("Depth Scale is: " , depth_scale)

    #align depth frame to color frame
    align_to = rs.stream.color
    align = rs.align(align_to)

    # start pipeline
    pipeline.start(config)

    # loop collect data
    try:
        while True:
            # Wait for a frames metadata
            frames = pipeline.wait_for_frames()

            # Get aligned frames
            aligned_frames = align.process(frames)
            aligned_depth_frame = aligned_frames.get_depth_frame()
            color_frame = frames.get_color_frame()

            # Validate that both frames are valid
            if not aligned_depth_frame or not color_frame:
                continue

            # Convert depth/color images to numpy arrays
            color_image = np.asanyarray(color_frame.get_data())
            depth_image = np.asanyarray(aligned_depth_frame.get_data())

            # get timestamp
            color_sensor_timestamp_domain = color_frame.get_frame_timestamp_domain()
            color_sensor_timestamp = color_frame.get_timestamp() / 1000
            timestamps_saver.save_timestamps(color_sensor_timestamp)

            # Show images
            depth_image_normalized = cv2.normalize(depth_image, None, 0, 255, cv2.NORM_MINMAX)
            depth_image_8bit = np.uint8(depth_image_normalized)
            depth_image_colored = cv2.cvtColor(depth_image_8bit, cv2.COLOR_GRAY2BGR)
            combined_image = np.hstack((color_image, depth_image_colored))

            cv2.namedWindow('Depth frame and color frame', cv2.WINDOW_AUTOSIZE)
            cv2.imshow('Depth frame and color frame', combined_image)
            
            key = cv2.waitKey(1)
            if key & 0xFF == ord('q') or key == 27:
                cv2.destroyAllWindows()
                break
    except Exception as e:
        print("[ERROR] ",e)
    finally:
        # Stop streaming
        pipeline.stop()