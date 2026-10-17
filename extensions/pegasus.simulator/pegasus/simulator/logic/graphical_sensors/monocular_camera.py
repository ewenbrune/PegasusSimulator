"""
| File: monocular_camera.py
| Author: Marcelo Jacinto (marcelo.jacinto@tecnico.ulisboa.pt)
| License: BSD-3-Clause. Copyright (c) 2024, Marcelo Jacinto. All rights reserved.
| Description: Simulates a monocular camera attached to the vehicle
"""
__all__ = ["MonocularCamera"]

from pegasus.simulator.logic.state import State
from pegasus.simulator.logic.graphical_sensors import GraphicalSensor
from pegasus.simulator.logic.interface.pegasus_interface import PegasusInterface

from isaacsim.sensors.experimental.rtx import CameraSensor
from isaacsim.core.experimental.utils.stage import get_current_stage
from omni.usd import get_stage_next_free_path

# Auxiliary scipy and numpy modules
import numpy as np
from scipy.spatial.transform import Rotation


class MonocularCamera(GraphicalSensor):
    """
    The class that implements a monocular camera sensor. This class inherits the base class GraphicalSensor.
    """

    def __init__(self, camera_name, config={}):
        """
        Initialize the MonocularCamera class

        Args:
            config (dict): A Dictionary that contains all the parameters for configuring the MonocularCamera - it can be empty or only have some of the parameters used by the MonocularCamera.

        Examples:
            The dictionary default parameters are

            >>> {"depth": True,
            >>> "position": np.array([0.30, 0.0, 0.0]),
            >>> "orientation": np.array([0.0, 0.0, 0.0]),
            >>> "resolution": (1920, 1200),
            >>> "clipping_range": (0.05, 100.0),
            >>> "frequency": 30,
            >>> "intrinsics": None,
            >>> "distortion_coefficients": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])}
        """

        # Initialize the Super class "object" attributes
        super().__init__(sensor_type="MonocularCamera", update_rate=config.get("frequency", 30.0))

        # Setup the name of the camera primitive path
        self._camera_name = camera_name
        self._stage_prim_path = ""

        # Configurations of the camera
        self._depth = config.get("depth", True)
        self._position = config.get("position", np.array([0.30, 0.0, 0.0]))
        self._orientation = config.get("orientation", np.array([0.0, 0.0, 180.0]))
        self._resolution = config.get("resolution", (1920, 1200))
        self._clipping_range = config.get("clipping_range", (0.05, 100.0))
        self._frequency = config.get("frequency", 30)
        self._intrinsics = config.get("intrinsics", None)
        self._distortion_coefficients = config.get("distortion_coefficients", None)

        # Set the values for the intrinsics if provided
        if self._intrinsics is not None:
            # Set the camera intrinsics
            ((self.fx,_,self.cx),(_,self.fy,self.cy),(_,_,_)) = self._intrinsics
        else:
            # Assume a default field of view of 70 degrees
            self.fov = 70.0  # degrees
            self.fx = 0.5 * self._resolution[0] / np.tan(0.5 * np.radians(self.fov))
            self.fy = self.fx
            self.cx = 0.5 * self._resolution[0]
            self.cy = 0.5 * self._resolution[1]

        self._intrinsics = np.array([[self.fx, 0.0, self.cx],
                                     [0.0, self.fy, self.cy],
                                     [0.0, 0.0, 1.0]])

        # Setup an empty camera output dictionary
        self._state = {}
        self._camera_full_set = False

        self.counter = 0


    def initialize(self, vehicle):

        # Initialize the Super class "object" attributes
        super().initialize(vehicle)

        # Get the complete stage prefix for the camera
        self._stage_prim_path = get_stage_next_free_path(get_current_stage(), self._vehicle.prim_path + "/body/" + self._camera_name, False)

        # Get the camera name that was actually created (and update the camera name)
        self._camera_name = self._stage_prim_path.rpartition("/")[-1]

        # Build annotators list
        annotators = ["rgb"]
        if self._depth:
            annotators.append("distance_to_image_plane")

        # Create the camera sensor using the new experimental RTX API
        # Note: resolution follows OpenCV/NumPy convention (height, width)
        self._camera = CameraSensor(
            path=self._stage_prim_path,
            resolution=(self._resolution[1], self._resolution[0]),
            annotators=annotators,
        )

        # Set the camera position locally with respect to the drone
        self._camera.authoring_object.set_local_poses(
            translations=[self._position],
            orientations=[Rotation.from_euler("ZYX", self._orientation, degrees=True).as_quat().tolist()]
        )

    def start(self):
        # Signal that the camera is fully set
        self._camera_full_set = True

    def stop(self):
        self._camera_full_set = False

    @property
    def state(self):
        """
        (dict) The 'state' of the sensor, i.e. the data produced by the sensor at any given point in time
        """
        return self._state


    @GraphicalSensor.update_at_rate
    def update(self, state: State, dt: float):
        """Method that gets the current RGB image from the camera and returns it as a dictionary.

        Args:
            state (State): The current state of the vehicle.
            dt (float): The time elapsed between the previous and current function calls (s).

        Returns:
            (dict) A dictionary containing the current state of the sensor (the data produced by the sensor)
        """

        while self.counter < 100:
            self.counter += 1
            return

        # If all the camera properties are not set yet, return None
        if not self._camera_full_set:
            return None

        # Get the data from the camera
        try:
            self._state = {}
            self._state["camera_name"] = self._camera_name
            self._state["stage_prim_path"] = self._stage_prim_path
            self._state["height"] = self._resolution[1]
            self._state["width"] = self._resolution[0]
            self._state["frequency"] = self._frequency
            self._state["camera"] = self._camera
            self._state["intrinsics"] = self._intrinsics

            if self._depth:
                self._state["depth"] = True

            # To actually get the image data from the camera, you can use:
            # self._camera.get_data("rgb")  # For RGB image
            # self._camera.get_data("distance_to_image_plane")  # For depth

        # If something goes wrong during the data acquisition, just return None
        except:
            self._state = None

        return self._state
