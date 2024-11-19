import pickle
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd


class __Scaler(ABC):
    def __init__(self, dataset_input: pd.DataFrame, dataset_output: pd.DataFrame):
        self.tagnames_input = dataset_input.columns.values.tolist()
        self.tagnames_output = dataset_output.columns.values.tolist()

    @property
    def cnt_tagnames_input(self):
        return len(self.tagnames_input)

    @property
    def cnt_tagnames_output(self):
        return len(self.tagnames_output)

    @property
    @abstractmethod
    def scaler_type(self):
        raise NotImplementedError

    @abstractmethod
    def fit(self):
        ...

    @abstractmethod
    def transform(self):
        ...

    @abstractmethod
    def inverse_transform(self):
        ...

    def save(self, path: str) -> None:
        with open(path, "wb") as f:
            pickle.dump(self, f, protocol=5)


class MinMaxScaler(__Scaler):
    __slots__ = [
        "tagnames_input",
        "tagnames_output",
        "data_input_min",
        "data_input_max",
        "data_output_min",
        "data_output_max",
        "ref_min",
        "ref_max",
        "ref_range",
    ]

    def __init__(self, convert_range: tuple = (0, 1)):
        self.ref_min = convert_range[0]
        self.ref_max = convert_range[1]
        self.ref_range = self.ref_max - self.ref_min

    def fit(
        self,
        dataset_input: pd.DataFrame,
        dataset_output: pd.DataFrame,
    ) -> None:
        self.data_input_min = np.array(dataset_input.min())
        self.data_input_max = np.array(dataset_input.max())
        self.data_output_min = np.array(dataset_output.min())
        self.data_output_max = np.array(dataset_output.max())
        super().__init__(dataset_input, dataset_output)

    def update(
        self,
        tagname: str,
        data_input_min: float,
        data_input_max: float,
        data_output_min: float,
        data_output_max: float,
    ) -> None:
        try:
            _idx = self.tagnames_input.index(tagname)
        except IndexError:
            raise ValueError(tagname)
        self.data_input_min[_idx] = data_input_min
        self.data_input_max[_idx] = data_input_max
        self.data_output_min[_idx] = data_output_min
        self.data_output_max[_idx] = data_output_max

    @property
    def scaler_type(self):
        return __class__.__name__

    def transform(self, values: np.array) -> np.array:
        return (
            (values - self.data_input_min) / (self.data_input_max - self.data_input_min)
        ) * self.ref_range + self.ref_min

    def inverse_transform(self, values: np.array) -> np.array:
        return ((values - self.ref_min) / self.ref_range) * (
            self.data_output_max - self.data_output_min
        ) + self.data_output_min

    @property
    def info_input(self):
        return {
            tagname: [min_v, max_v]
            for tagname, min_v, max_v in zip(
                self.tagnames_input, self.data_input_min, self.data_input_max
            )
        }

    @property
    def info_output(self):
        return {
            tagname: [min_v, max_v]
            for tagname, min_v, max_v in zip(
                self.tagnames_output, self.data_output_min, self.data_output_max
            )
        }


class StandardScaler(__Scaler):
    __slots__ = []

    def __init__(self):
        """Nothing to initialize"""
        pass

    def fit(self, dataset_input: pd.DataFrame, dataset_output: pd.DataFrame):
        self.data_input_mean = np.array(dataset_input.mean())
        self.data_input_std = np.array(dataset_input.std())
        self.data_output_mean = np.array(dataset_input.mean())
        self.data_output_std = np.array(dataset_input.std())
        super().__init__(dataset_input, dataset_output)

    @property
    def scaler_type(self):
        return __class__.__name__

    def transform(self, values: np.array) -> np.array:
        return (values - self.data_input_mean) / self.data_input_std

    def inverse_transform(self, values: np.array) -> np.array:
        return (values * self.data_input_std) + self.data_input_mean

    def update(
        self,
        tagname: str,
        data_input_mean: float,
        data_input_std: float,
        data_output_mean: float,
        data_output_std: float,
    ) -> None:
        try:
            _idx = self.tagnames_input.index(tagname)
        except IndexError:
            raise ValueError(tagname)
        self.data_input_mean[_idx] = data_input_mean
        self.data_input_std[_idx] = data_input_std
        self.data_output_mean[_idx] = data_output_mean
        self.data_output_std[_idx] = data_output_std