#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:     eye tracking
#
# Author:      lukea_000
# First Modifier:    galal1
# Firstly Modified parts: Just some parts to fit my gui.py (parts signed)
#
# Created:     02/11/2013
# Firstly Modified:    10/12/2018
# Copyright:   (c) lukea_000 2013
# Licence:     GNU Lesser General Public License v3.0
#-------------------------------------------------------------------------------
import ctypes
import sys, pygame, os
from builtins import dict

from pygame.locals import *

pygame.init()

white = 255, 255, 255
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0, 30)
info = pygame.display.Info()    # modified: display settings for all screen sizes(galal1)
width, height = info.current_w, info.current_h
ctypes.windll.user32.SetProcessDPIAware()
ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1)

class Crosshair(object):
    def __init__(self, speed = [1, 1], quadratic = True):
        self.screen = pygame.display.set_mode((width, height-60))
        pygame.display.set_caption("Kalibráció")    # modified: icon and title (galal1)
        iconPath = os.path.join(os.getcwd() + '/datas/images/pygame_logo.png')
        icon = pygame.image.load(iconPath)
        icon.set_colorkey((238, 237, 252))
        pygame.display.set_icon(icon.convert_alpha())

        self.quadratic = quadratic
        self.speed = speed
        self.cross = pygame.image.load(os.path.join(os.getcwd() + '/datas/images/gaussianBlur.png'))
        self.crossrect = self.cross.get_rect()
##        print(self.crossrect.center, "is the center")
##        print(self.crossrect, "is the rect")
##        print(self.crossrect.top, "is the top")
##        print(self.crossrect.left, "is the left")
        self.result = []
        self.delay = 20
        self.userWantsToQuit = False
        self.draw()

    def draw(self):
        self.remove()
        #could maybe edit the crossrect directly for smoother motions
        #The Rect object has several virtual attributes which can be used to move and align the Rect:
        #top, left, bottom, right
        #topleft, bottomleft, topright, bottomright
        #midtop, midleft, midbottom, midright
        #center, centerx, centery
        #size, width, height
        #w,h
        self.screen.blit(self.cross, self.crossrect)
        pygame.display.flip()

    def drawCrossAt(self, coords):
        self.crossrect.center = coords
        self.draw()

    def move(self):
        self.crossrect = self.crossrect.move(self.speed)
        if self.crossrect.left < 0 or self.crossrect.right > width:
            self.speed[0] = -self.speed[0]
        if self.crossrect.top < 0 or self.crossrect.bottom > height:
            self.speed[1] = -self.speed[1]

    def record(self, x, y):
        cx, cy = self.crossrect.centerx, self.crossrect.centery
        lis = [x, y, cx, cy]
        if self.quadratic == True:
            lis.append([cx * cx, cx * cy, cy * cy])
        self.result.append(lis)

    def record(self, inputTuple):
        self.result.append(list(inputTuple)+[self.crossrect.centerx,self.crossrect.centery])

    def write(self):
        completeName = os.path.join(os.getcwd() + "/datas/offset/1700wxoffsetyoffsetxy.csv")   # modified: path (galal1)
        fo = open(completeName, "w")
        for line in self.result:
            print(line)
            result = ""
            for number in line:
                result += str(number) + str(',')
            fo.write(result + "\n")
        fo.close()

    #collects data, returns true if done looping
    def loop(self):
        self.move()
        pygame.time.delay(self.delay)
        self.draw()

    def remove(self):
        self.screen.fill(white)
        pygame.display.flip()

    def clearEvents(self):
        pygame.event.clear()

    # Blocks the thread while waiting for a click.
    def getClick(self):
        needClick = True
        while needClick:
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    self.crossrect.center = pos
                    self.draw()
                    needClick = False
                else:
                    continue

    # Returns True, saves position, and draws the crosshairs if a click has occurred.
    # Returns False if not.
    def pollForClick(self):
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                self.crossrect.center = pos
                self.draw()
                return True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.userWantsToQuit = True
            elif event.type == pygame.QUIT:     # modified: when Close(X) button clicked exit too (galal1)
                self.userWantsToQuit = True
        return False

    def close(self):
        pygame.display.quit()

    def minimizeScreen(self):   # modified: screen will be really small to come back to testing on gui (galal1)
        self.screen = pygame.display.set_mode((1, 1))

##ch = Crosshair()
##for i in range(10):
##    pygame.time.delay(100)
##    ch.getClick()


#while 1:
#    pressed = pygame.mouse.get_pressed()
#    if any(pressed):
#        break
#    for event in pygame.event.get():
#        if event.type in (QUIT, pygame.KEYDOWN):
#            break

#    crosshair.draw()
#    pygame.time.delay(10)#miliseconds
#    xoffset = 0
#    yoffset = 0
#    crosshair.record(xoffset, yoffset)
#    crosshair.move()