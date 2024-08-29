import cv2
import numpy as np

class AE:
    def __init__(self, initial_exposure_time, max_exposure_time, min_exposure_time, 
                 image: np.ndarray, target_brightness = 128, contrast_factor = 1.0) -> None:
        self.base_exp_t = initial_exposure_time
        self.max_exp_t = max_exposure_time * 10
        self.min_exp_t = min_exposure_time * 10
        self.c_f = contrast_factor
        self.target_bright = target_brightness
        self.counter_ = 1
        self.hist = self.calculate_histogram(image)
        self.gsw = self.generate_gaussian_weight(image.shape)
        self.w_avg_bright = self.calculate_average_brightness(image)

    def crop_image(self, image, crop_width = 320, crop_height = 240):
        img_height, img_width = image.shape[:2]
        
        start_x = (img_width - crop_width) // 2
        start_y = (img_height - crop_height) // 2
        
        cropped_image = image[start_y:start_y + crop_height, start_x:start_x + crop_width]
        
        return cropped_image

    def calculate_average_brightness(self, color_image):
        gray_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
        return np.mean(gray_image)
        
    def generate_gaussian_weight(self, shape, sigma = 1.0):
        rows, cols, _ = shape
        x = np.linspace(-1, 1, cols)
        y = np.linspace(-1, 1, rows)
        x, y = np.meshgrid(x, y)
        d = np.sqrt(x * x + y * y)
        gaussian_weights = np.exp(-(d ** 2 / (2.0 * sigma ** 2)))
        return gaussian_weights

    def calculate_weighted_average_brightness(self, color_image):
        gray_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
        weighted_brightness = np.sum(self.gsw * gray_image) / np.sum(self.gsw)
        return weighted_brightness

    def calculate_histogram_contrast(self, color_image):
        hist = cv2.calcHist([color_image], [0], None, [256], [0, 256])
        hist = hist / hist.sum()  
        cdf = hist.cumsum()  
        cdf = np.ma.masked_equal(cdf, 0)  
        cdf = (cdf - cdf.min()) / (cdf.max() - cdf.min())  
        contrast = -np.sum(cdf * np.log(cdf + 1e-2, where = (cdf + 1e-2) > 0)) 
        return contrast
    
    def calculate_histogram(self, color_image):
         gray_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
         hist = cv2.calcHist([gray_image], [0], None, [256], [0, 256])
         return hist
        
    def adjust_exposure(self, color_image, old_et):
        total_pix_num = color_image.shape[0] * color_image.shape[1]
        # calculate image histogram
        self.hist = self.calculate_histogram(color_image)
        # calculate weighted average brightness
        crop_image = self.crop_image(color_image)
        self.w_avg_bright = self.calculate_average_brightness(crop_image)

        if (abs(self.w_avg_bright - self.target_bright) <= 20):
            # if (np.sum(self.hist[220:]) > total_pix_num / 20):
            #     print(self.counter_)
            #     if self.counter_ % 10 == 0:
            #         new_et = old_et / np.cbrt(2)
            #         self.counter_ = 1
            #         return np.clip(new_et, self.min_exp_t, self.max_exp_t)
            #     else:
            #         self.counter_ = self.counter_ + 1
            # elif (np.sum(self.hist[30:]) > total_pix_num / 20):
            #     if self.counter_ % 10 == 0:
            #         new_et =  old_et * np.cbrt(2)
            #         self.counter_ = 1
            #         return np.clip(new_et, self.min_exp_t, self.max_exp_t)
            #     else:
            #         self.counter_ = self.counter_ + 1
            # else: 
            new_et = old_et
        if old_et == self.max_exp_t:
            old_et = old_et - 1   

        new_et = (256. - self.w_avg_bright) * old_et * self.max_exp_t / ((self.target_bright - self.w_avg_bright) * old_et + (256. - self.target_bright) * self.max_exp_t)
        return np.clip(new_et, self.min_exp_t, self.max_exp_t)

    # def adjust_exposure(self, color_image):
    #     # calculate weighted average brightness
    #     self.w_avg_bright = self.calculate_weighted_average_brightness(color_image)
    #     # w_avg_bright = np.mean(cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY))
    #     # print("[INFO] weighted average brightness: ", self.w_avg_bright)

    #     # calculate histogram contrast
    #     histogram_contrast = self.calculate_histogram_contrast(color_image)
    #     # print("[INFO] histogram_contrast: ", histogram_contrast)

    #     # calculate new exposure time
    #     linear_term = 0.75 * (self.target_bright - self.w_avg_bright) / self.target_bright
    #     # print("[INFO] linear term value: ", linear_term)
    #     nonlinear_term = 10 * (1 / 2.71 - np.exp( - (self.target_bright / self.w_avg_bright)))
    #     # print("[INFO] nonlinear term value: ", nonlinear_term)
    #     # exposure_time = self.base_exp_t * (self.target_bright / w_avg_bright) * (1 + self.c_f * histogram_contrast)\
    #     # exposure_time = self.base_exp_t * (1 + 0.75 * (self.target_bright - w_avg_bright) / self.target_bright) 
    #     exposure_time = self.base_exp_t * (1 + 0.8 * linear_term) + 1.0 * nonlinear_term
    #     # constrains exposure time
    #     return np.clip(exposure_time, self.min_exp_t, self.max_exp_t)  
