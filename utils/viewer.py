import cv2

def visualizer(color_image, actual_exp_time, w_avg_bright, timestamps):
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.5
    thickness = 2
    line_type = cv2.LINE_AA

    text_1 = f'Actual exposure time: {(actual_exp_time / 10):.2f}'
    position_1 = (10, 30)
    font_color_1 = (0, 255, 0)  
    cv2.putText(color_image, text_1, position_1, font, font_scale, font_color_1, thickness, line_type)
    
    text_2 = f'Weighted average brightness: {w_avg_bright:.2f}'
    position_2 = (10, 70)  
    font_color_2 = (0, 0, 255)  
    cv2.putText(color_image, text_2, position_2, font, font_scale, font_color_2, thickness, line_type)

    text_3 = f'color sensor timestamps: {timestamps}'
    position_3 = (10, 110)  
    font_color_3 = (0, 255, 255)  
    cv2.putText(color_image, text_3, position_3, font, font_scale, font_color_3, thickness, line_type)
    
    cv2.namedWindow('RealSense D455 online stream', cv2.WINDOW_AUTOSIZE)
    cv2.imshow('RealSense D455 online stream', color_image)