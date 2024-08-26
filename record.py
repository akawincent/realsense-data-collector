import cv2
import numpy as np
import pyrealsense2 as rs

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
    
    # set exposure option
    color_sensor = pipeline_profile.get_device().query_sensors()[rgb_sensor_index]
    color_sensor.set_option(rs.option.enable_auto_exposure, False)
    framerate = 30
    indoor_flicker_freq = 50
    exposure_range = color_sensor.get_option_range(rs.option.exposure)
    max_exposure_time = min(1 / framerate * 1e3, exposure_range.max * 0.1)
    min_exposure_time = max((1 / (indoor_flicker_freq * 2)) * 1e3, exposure_range.min * 0.1)
    print(f"exposure time min: {round(min_exposure_time, 1)} msec")
    print(f"exposure time max: {round(max_exposure_time, 1)} msec")
    
    # setting for streams
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, framerate)
    
    # start streaming
    pipeline.start(config)

    try:
        while True:
            # Wait for a frames metadata
            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            if not color_frame:
                continue

            # Convert images to numpy arrays
            color_image = np.asanyarray(color_frame.get_data())
            color_colormap_dim = color_image.shape

            # Show images
            cv2.namedWindow('RealSense D455 online stream', cv2.WINDOW_AUTOSIZE)
            cv2.imshow('RealSense D455 online stream', color_image)
            
            key = cv2.waitKey(1)
            if key & 0xFF == ord('q') or key == 27:
                cv2.destroyAllWindows()
                break
    except Exception as e:
        print("[ERROR] ",e)
    finally:
        # Stop streaming
        pipeline.stop()