# Hide the "Hello from the pygame community" message
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

import pygame
from pygame._sdl2 import controller
from PySide6.QtCore import QThread
import time

class ControlThread(QThread):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.reconnectTime = time.time() - 1000
        self.numControllers = 1
        self.controllers = [None] * self.numControllers

    def reconnect(self):
        reconnectNeeded = False
        for i in range(self.numControllers):
            if self.controllers[i] is not None and not self.controllers[i].attached():
                print(f'Controller {i} disconnected')
                self.controllers[i].quit()
                self.controllers[i] = None
            
            if self.controllers[i] is None:
                reconnectNeeded = True
        if not reconnectNeeded:
            return
        
        if time.time() - self.reconnectTime < 0.5:
            return
        
        self.reconnectTime = time.time()
        count = controller.get_count()
        for i in range(count):
            if not controller.is_controller(i):
                continue
            newController = controller.Controller(i)
            id = newController.as_joystick().get_instance_id()
            found = False
            for j in range(self.numControllers):
                if self.controllers[j] is not None and self.controllers[j].as_joystick().get_instance_id() == id:
                    found = True
                    break
            if found:
                continue
            for j in range(self.numControllers):
                if self.controllers[j] is None:
                    self.controllers[j] = newController
                    print(f'Controller {j} connected: {newController.name}')
                    break

    def run(self):
        pygame.init()
        controller.init()

        pygame.event.pump()
        self.reconnect()
        missingControllers = self.controllers.count(None)
        if missingControllers > 0:
            print(f'Not enough controllers connected at startup: expected {self.numControllers}, found {self.numControllers - missingControllers}')
        
        while not self.isInterruptionRequested():
            pygame.event.pump()
            self.reconnect()

            # Axis constants: pygame.CONTROLLER_AXIS_ (LEFTX/Y, RIGHTX/Y, TRIGGERLEFT/RIGHT)
            # Button constants: pygame.CONTROLLER_BUTTON_ (A/B/X/Y, LEFT/RIGHTSHOULDER, LEFT/RIGHTSTICK, BACK/START/GUIDE, DPAD_UP/DOWN/LEFT/RIGHT)
            x = 0
            y = 0
            z = 0
            roll = 0
            pitch = 0
            yaw = 0
            if self.controllers[0] is not None:
                x = -self.controllers[0].get_axis(pygame.CONTROLLER_AXIS_LEFTY) / 32768.0
                y = -self.controllers[0].get_axis(pygame.CONTROLLER_AXIS_LEFTX) / 32768.0
                z = (self.controllers[0].get_axis(pygame.CONTROLLER_AXIS_TRIGGERRIGHT) - self.controllers[0].get_axis(pygame.CONTROLLER_AXIS_TRIGGERLEFT)) / 32768.0
                yaw = -self.controllers[0].get_axis(pygame.CONTROLLER_AXIS_RIGHTX) / 32768.0
                pitch = -self.controllers[0].get_axis(pygame.CONTROLLER_AXIS_RIGHTY) / 32768.0
                roll = (self.controllers[0].get_button(pygame.CONTROLLER_BUTTON_RIGHTSHOULDER) - self.controllers[0].get_button(pygame.CONTROLLER_BUTTON_LEFTSHOULDER))
            print(f'x: {x}, y: {y}, z: {z}, roll: {roll}, pitch: {pitch}, yaw: {yaw}')
            
            # TODO: send controls to ROV

            time.sleep(0.02)
        
        for c in self.controllers:
            if c is not None:
                c.quit()
        pygame.quit()