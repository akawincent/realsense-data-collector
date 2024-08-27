import cv2
import numpy as np

class AE:
    def __init__(self, initial_exposure_time, max_exposure_time, min_exposure_time, 
                 image_shape, target_brightness = 50, contrast_factor = 1.0) -> None:
        self.target_bright = target_brightness
        self.base_exp_t = initial_exposure_time
        self.max_exp_t = max_exposure_time 
        self.min_exp_t = min_exposure_time 
        self.c_f = contrast_factor
        self.gsw = self.generate_gaussian_weight(image_shape)
        self.w_avg_bright = None

    def generate_gaussian_weight(self, shape, sigma = 1.0):
        cols, rows = shape
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

    def adjust_exposure(self, color_image):
        # calculate weighted average brightness
        self.w_avg_bright = self.calculate_weighted_average_brightness(color_image)
        # w_avg_bright = np.mean(cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY))
        # print("[INFO] weighted average brightness: ", self.w_avg_bright)

        # calculate histogram contrast
        histogram_contrast = self.calculate_histogram_contrast(color_image)
        # print("[INFO] histogram_contrast: ", histogram_contrast)

        # calculate new exposure time
        linear_term = 0.75 * (self.target_bright - self.w_avg_bright) / self.target_bright
        # print("[INFO] linear term value: ", linear_term)
        nonlinear_term = 10 * (1 / 2.71 - np.exp( - (self.target_bright / self.w_avg_bright)))
        # print("[INFO] nonlinear term value: ", nonlinear_term)
        # exposure_time = self.base_exp_t * (self.target_bright / w_avg_bright) * (1 + self.c_f * histogram_contrast)\
        # exposure_time = self.base_exp_t * (1 + 0.75 * (self.target_bright - w_avg_bright) / self.target_bright) 
        exposure_time = self.base_exp_t * (1 + 0.8 * linear_term) + 1.0 * nonlinear_term
        # constrains exposure time
        return np.clip(exposure_time, self.min_exp_t, self.max_exp_t)  
