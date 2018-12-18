class Coords():
    def __init__(self):
        super(Coords, self).__init__()
        self.coords = []

    def getCoords(self):
        return self.coords

    def appendCoords(self, coord):
        self.coords.append(coord)

    def delCoord(self, index):
        del self.coords[index]

    def delAllCoord(self):
        self.coords = []