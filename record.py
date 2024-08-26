import cv2
import numpy as np
import pyrealsense2 as rs

if __name__ == "__main__":
    pipeline = rs.pipeline()
    config = rs.config()

    # Get device product line for setting a supporting resolution
    pipeline_wrapper = rs.pipeline_wrapper(pipeline)
    pipeline_profile = config.resolve(pipeline_wrapper)
    device = pipeline_profile.get_device()
    device_product_line = str(device.get_info(rs.camera_info.product_line))
    print("[INFO] Device type:",device_product_line)

    # find RGB camera
    found_rgb = False
    for s in device.sensors:
        print("[INFO] Sensor name:",s)
        if s.get_info(rs.camera_info.name) == 'RGB Camera':
            found_rgb = True
            print("[INFO] RGB camera sensor is sucessfully detected!")
            break
    if not found_rgb:
        print("[ERROR] Can't find RGB camera sensor!")
        exit(0)
    
    # setting for streams
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 10)
    
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