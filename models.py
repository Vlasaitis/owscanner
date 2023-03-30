import tensorflow as tf
import numpy as np
from config import top_bar_model_path, kill_entry_path, kill_entry_model_classes, killfeed_model_path
import torch
from torchvision.models.detection import fasterrcnn_resnet50_fpn
from torchvision.models.detection import FasterRCNN_ResNet50_FPN_Weights
import torchvision
from typing import Tuple

class_names = ['ana', 'ashe', 'baptiste', 'bastion', 'brigitte', 'cassidy', 'doomfist', 'dva', 'echo', 'genji', 'hammond', 'hanzo', 'junkerqueen', 'junkrat', 'kiriko', 'lucio', 'mei', 'mercy',
               'moira', 'orisa', 'pharah', 'ramattra', 'reaper', 'reinhardt', 'roadhog', 's76', 'sigma', 'sojourn', 'sombra', 'symmetra', 'torbjorn', 'tracer', 'widowmaker', 'winston', 'zarya', 'zenyatta']


class Models:
    def __init__(self):
        self.top_bar = tf.keras.models.load_model(top_bar_model_path)
        self.kill_entry_finder = self.initiate_kf_finder()
        self.kf_model = tf.keras.models.load_model(killfeed_model_path)
        self.ke_device = torch.device(
            'cuda' if torch.cuda.is_available() else 'cpu')
        self.low_confidence = []

    def scan_hero_kf(self, image) -> Tuple[str, float]:
        resize = tf.image.resize(image, (30, 30))
        img_array = np.array(resize)
        predictions = self.kf_model(np.array([img_array]))
        max_percentage = np.max(tf.nn.softmax(predictions[0]))
        predicted_class_index = np.argmax(predictions[0])
        predicted_class = class_names[predicted_class_index]
        return predicted_class, max_percentage

    def scan_hero_top(self, image, timestamp):
        resize = tf.image.resize(image, (38, 38))
        img_array = np.array(resize)  # normalize pixel values

        # Make prediction
        predictions = self.top_bar(np.array([img_array]))
        max_percentage = np.max(tf.nn.softmax(predictions[0]))
        predicted_class_index = np.argmax(predictions[0])
        predicted_class = class_names[predicted_class_index]

        if max_percentage < 0.9:
            self.low_confidence.append({"hero": predicted_class, "certainty": float(
                max_percentage), "time": timestamp})

        return predicted_class, max_percentage

    def initiate_kf_finder(self):
        # create model with resnet50 backbone, FPN neck.
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = fasterrcnn_resnet50_fpn(weights=None, num_classes=2)

        in_features = model.roi_heads.box_predictor.cls_score.in_features
        # set the predictor to right number of classes
        model.roi_heads.box_predictor = torchvision.models.detection.faster_rcnn.FastRCNNPredictor(
            in_features, kill_entry_model_classes)
        model.load_state_dict(torch.load(kill_entry_path, map_location=device))
        model.to(device)  # move model to CPU or GPU
        model.eval()
        '''
        if want to confirm model loaded correctly on GPU
        print("Model architecture:\n", model)
        print("Model loaded on device:", device)
        '''
        return model
