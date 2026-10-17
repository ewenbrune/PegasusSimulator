#!/usr/bin/env python
"""
| File: 0_template_app.py
| Author: Marcelo Jacinto (marcelo.jacinto@tecnico.ulisboa.pt)
| License: BSD-3-Clause. Copyright (c) 2023, Marcelo Jacinto. All rights reserved.
| Description: This files serves as a template on how to build a clean and simple Isaac Sim based standalone App.
"""

# Imports to start Isaac Sim from this script
import carb
from isaacsim import SimulationApp

# Start Isaac Sim's simulation environment
# Note: this simulation app must be instantiated right after the SimulationApp import, otherwise the simulator will crash
# as this is the object that will load all the extensions and load the actual simulator.
simulation_app = SimulationApp({"headless": False})

# -----------------------------------
# The actual script should start here
# -----------------------------------
import omni.timeline
import omni.kit.app
from isaacsim.core.simulation_manager import SimulationManager, SimulationEvent
from isaacsim.core.experimental.utils import app as app_utils
from isaacsim.core.experimental.objects import GroundPlane

class Template:
    """
    A Template class that serves as an example on how to build a simple Isaac Sim standalone App.
    """

    def __init__(self):
        """
        Method that initializes the template App and is used to setup the simulation environment.
        """

        # Acquire the timeline that will be used to start/stop the simulation
        self.timeline = omni.timeline.get_timeline_interface()

        # Initialize the simulation
        SimulationManager.setup_simulation(dt=1.0/60.0, device="cpu")

        # Create a ground plane for the simulation
        ground_plane = GroundPlane(paths="/World/ground_plane")

        # Create an example physics callback
        SimulationManager.register_callback(self.physics_callback, SimulationEvent.PHYSICS_POST_STEP)

        # Create an example render callback
        self._render_sub = omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(
            self.render_callback
        )

        # Create an example timeline callback
        SimulationManager.register_callback(self.timeline_callback, SimulationEvent.SIMULATION_STOPPED)

        # Reset the simulation environment so that all articulations (aka robots) are initialized
        SimulationManager.invalidate_physics()
        SimulationManager.initialize_physics()

        # Auxiliar variable for the timeline callback example
        self.stop_sim = False

    def physics_callback(self, dt: float):
        """An example physics callback. It will get invoked every physics step.

        Args:
            dt (float): The time difference between the previous and current function call, in seconds.
        """
        carb.log_info("This is a physics callback. It is called every " + str(dt) + " seconds!")

    def render_callback(self, event):
        """An example render callback. It will get invoked for every rendered frame.

        Args:
            event: Rendering data.
        """
        carb.log_info("This is a render callback. It is called every frame!")

    def timeline_callback(self, event):
        """An example timeline callback. It will get invoked every time a timeline event occurs. In this example,
        we will check if the event is for a 'simulation stop'. If so, we will attempt to close the app

        Args:
            event: A timeline event
        """
        if not SimulationManager.is_simulating():
            self.stop_sim = True

    def run(self):
        """
        Method that implements the application main loop, where the physics steps are executed.
        """

        # Start the simulation
        self.timeline.play()

        # The "infinite" loop
        while simulation_app.is_running() and not self.stop_sim:

            # Update the UI of the app and perform the physics step
            SimulationManager.step()
            app_utils.update_app()

        # Cleanup and stop
        carb.log_warn("Template Simulation App is closing.")
        self.timeline.stop()
        simulation_app.close()

def main():

    # Instantiate the template app
    template_app = Template()

    # Run the application loop
    template_app.run()

if __name__ == "__main__":
    main()
