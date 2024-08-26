import cv2
import numpy as np
import pyrealsense2 as rs

from utils import viewer
from auto_exposure import AE

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
        print("[INFO] Sensor name:",s)
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
    
    # set sensor option
    color_sensor = pipeline_profile.get_device().query_sensors()[rgb_sensor_index]
    color_sensor.set_option(rs.option.enable_auto_exposure, False)
    color_sensor.set_option(rs.option.power_line_frequency, 1)
    
    # setting for streams
    framerate = 30
    image_resolution = [1280, 720]
    config.enable_stream(rs.stream.color, image_resolution[0], image_resolution[1], rs.format.bgr8, framerate)
    # calculate exposure time range
    indoor_flicker_freq = 50
    exposure_range = color_sensor.get_option_range(rs.option.exposure)
    max_exposure_time = min(1 / framerate * 1e3, exposure_range.max * 0.1)
    min_exposure_time = max((1 / (indoor_flicker_freq * 2)) * 1e3, exposure_range.min * 0.1)
    print(f"exposure time min: {round(min_exposure_time, 1)} msec")
    print(f"exposure time max: {round(max_exposure_time, 1)} msec")
    
    # initialize Auto Exposure algorithm
    intial_exposure_time = (min_exposure_time + max_exposure_time) / 2
    target_brightness = 90
    auto_exposure = AE(intial_exposure_time, max_exposure_time, min_exposure_time, 
                       image_resolution, target_brightness)

    # start streaming
    pipeline.start(config)

    try:
        next_exposure_time = intial_exposure_time 
        while True:
            # set exposure time 
            manual_exposure_time = next_exposure_time
            color_sensor.set_option(rs.option.exposure, manual_exposure_time * 10)
            
            # Wait for a frames metadata
            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            if not color_frame:
                continue

            # Convert images to numpy arrays
            color_image = np.asanyarray(color_frame.get_data())

            # get actual exposure time
            actual_exp_time = color_frame.get_frame_metadata(rs.frame_metadata_value.actual_exposure)
            # print("[INFO] Actual exposure time:", (actual_exp_time / 10), "msec")

            # calculate exposure time for next frame
            next_exposure_time = auto_exposure.adjust_exposure(color_image)
            # print("[INFO] exposure time for next frame", next_exposure_time, "msec")

            # Show images
            viewer.visualizer(color_image, actual_exp_time, auto_exposure.w_avg_bright)
            
            key = cv2.waitKey(1)
            if key & 0xFF == ord('q') or key == 27:
                cv2.destroyAllWindows()
                break
    except Exception as e:
        print("[ERROR] ",e)
    finally:
        # Stop streaming
        pipeline.stop()