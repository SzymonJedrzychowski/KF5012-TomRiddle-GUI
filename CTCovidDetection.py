from tensorflow import keras
from PIL import Image, ImageOps
import numpy as np


class CTCovidDetection:
    def __init__(self):
        self.__model = None
        self.__image_sizes = (0, 0)

    def load_model(self, model_location):
        '''Load model to be used

        :param model_location: location of *.h5 file

        :return success_information: 1 - model loaded successfully, 0 - problems with loading model
        '''
        try:
            self.__model = keras.models.load_model(model_location)
            self.__set_image_sizes()
            return 1
        except Exception as exc:
            print(exc)
            return 0

    def predict(self, data):
        '''Predict data

        :param data: array of file locations

        :return array [success_information, results]:
        success_information: 1 - successful prediction, 0 - error while predicting, -1 - model not loaded
        results - array of results if successful, None if not successful
        '''

        if self.__model == None:
            return [-1, None]
        try:
            loaded_data = self.__load_data(data)
            preprocessed_data = self.__preprocess_data(loaded_data)
            numerical_data = self.__create_numerical_data(preprocessed_data)
            results = self.__predict_photos(numerical_data)
            processed_results = self.__process_results(results, data)
            return [1, processed_results]
        except Exception as exc:
            print(exc)
            return [0, None]

    def __set_image_sizes(self):
        '''Set sizes of image according to model input shape 
        '''
        model_data = self.__model.get_config()
        model_input = model_data["layers"][0]["config"]["batch_input_shape"]
        self.__image_sizes = (model_input[1], model_input[2])

    def __load_data(self, data):
        '''Load image data

        :param data: array of file locations

        :return loaded_data: array of Image data
        '''

        loaded_data = []
        for image_name in data:
            loaded_data.append(Image.open(image_name))
        return loaded_data

    def __preprocess_data(self, loaded_data):
        '''Preprocess loaded data by changing size and applying grayscale

        :param loaded_data: array of Image data of all photos

        :return preprocessed_data: array of preprocessed Image data af all photos 
        '''

        preprocessed_data = []
        for image in loaded_data:
            resized_image = image.resize(
                (self.__image_sizes[0], self.__image_sizes[1]))
            gray_image = ImageOps.grayscale(resized_image)
            preprocessed_data.append(gray_image)
        return preprocessed_data

    def __create_numerical_data(self, preprocessed_data):
        '''Change Image data to numerical data

        :param preprocessed_data: array of preprocessed Image data af all photos 

        :return numerical_data: numpy array of data af all photos 
        '''

        numerical_data = []
        for data in preprocessed_data:
            numerical_data.append(np.asarray(data))
        numerical_data = np.array(numerical_data)
        
        numerical_data = numerical_data.astype('float32')
        numerical_data /= 255
        
        numerical_data = numerical_data.reshape(
            numerical_data.shape[0], self.__image_sizes[0], self.__image_sizes[1], 1)
        return numerical_data

    def __predict_photos(self, numerical_data):
        '''Predict if data suggests Covid or no

        :param numerical_data: numpy array of data af all photos 

        :return results: numpy array of predictions (prediction array: [no-covid, covid])
        '''

        results = self.__model.predict(numerical_data)
        return results

    def __process_results(self, results, data):
        '''Process results so that it includes file name

        :param results: numpy array of predictions (prediction array: [no-covid, covid])
        :param data: array of file locations

        :return processed_results: dictionary of file names and probability of covid
        '''

        processed_results = {}
        for data_index, file_name in enumerate(data):
            processed_results[file_name] = results[data_index][1]
        return processed_results
