from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from shapely import Polygon

from peltomappi.logger import LOGGER


class AbstractWeatherBackend(ABC):
    """
    Represents an abstract weather service backend which the Weather class will
    call to include data in subprojects.
    """

    @abstractmethod
    def write_data(
        self,
        filter_geometry: Polygon,
        output_path: Path,
        begin: datetime,
        end: datetime,
    ):
        """
        Abstract method for writing out data. The data should be only from the
        area of the requested geometry and time period, and it is up to each
        implemented backend to determine how that is achieved.
        """
        pass


class WeatherBackendTest(AbstractWeatherBackend):
    def write_data(
        self,
        filter_geometry: Polygon,
        output_path: Path,
        begin: datetime,
        end: datetime,
    ):
        LOGGER.info(f"""WeatherBackendTest writing with parameters {output_path}, {begin}, {end} {filter_geometry}""")
