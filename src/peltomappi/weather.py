import shutil
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from osgeo import ogr

from peltomappi.config import Config
from peltomappi.logger import LOGGER
from peltomappi.utils import config_description_to_path


class WeatherError(Exception):
    pass


class AbstractWeatherBackend(ABC):
    """
    Represents an abstract weather service backend which the Weather class will
    call to include data in subprojects.
    """

    @abstractmethod
    def write_data(
        self,
        *,
        request_geometry: ogr.Geometry,
        output_path: Path,
        begin: datetime,
        end: datetime,
    ):
        """
        Abstract method for writing out data. The data should be only from the
        area of the requested geometry and time period, but it is up to each
        implemented backend to determine how that is achieved.
        """
        pass


class TestBackend(AbstractWeatherBackend):
    __input_gpkg: Path

    def __init__(self, input: Path):
        self.__input_gpkg = input

    def write_data(
        self,
        *,
        request_geometry: ogr.Geometry,
        output_path: Path,
        begin: datetime,
        end: datetime,
    ):
        LOGGER.info(f"""TestBackend writing with parameters {request_geometry}, {output_path}, {begin}, {end}""")
        shutil.copy(self.__input_gpkg, output_path)


class FMIBackend(AbstractWeatherBackend):
    def write_data(
        self,
        *,
        request_geometry: ogr.Geometry,
        output_path: Path,
        begin: datetime,
        end: datetime,
    ):
        pass


class Weather:
    """
    Requests weather data from given backend and writes it to subprojects
    according to a configuration.
    """

    __config: Config
    __output_dir: Path
    __backend: AbstractWeatherBackend
    __overwrite: bool

    def __init__(
        self,
        *,
        config: Config,
        output_dir: Path,
        backend: AbstractWeatherBackend,
        overwrite: bool = False,
    ):
        self.__config = config
        self.__output_dir = output_dir
        self.__backend = backend
        self.__overwrite = overwrite

    def write(self):
        for description, geom in self.__config.to_dict().items():
            output_path = config_description_to_path(description, self.__output_dir) / "weather.gpkg"
            if not self.__overwrite and output_path.exists():
                msg = (
                    f"attempting to write file {output_path} but it already exists and overwrite has not been permitted"
                )
                raise WeatherError(msg)

            self.__backend.write_data(
                request_geometry=geom,
                output_path=output_path,
                begin=datetime.now(),
                end=datetime.now(),
            )
