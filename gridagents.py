import math
import numpy
import uuid
import gridworld
from pprint import pprint

# base class for all objects that can be in a GridWorld. Not much here other than
# the world of which they are a part and their x-y coordinates in the world (which may
# be actual or believed coordinates)


class GridObject(object):

    def __init__(self, name, obj_id=None, world=None, x=0, y=0):

        # obscure: with a __setattr__ method override, setters for any sort of internal
        # attribute must be set even in the constructor using the base class' __setattr__ method.
        # what kind of object this is
        object.__setattr__(self, "_objectName", name)
        if obj_id is None:
            # unique identifier
            object.__setattr__(self, "_objectID", uuid.uuid4().hex)
        else:
            # no special guards here against duplicate IDs - this is the user's responsibility!
            object.__setattr__(self, "_objectID", obj_id)
        # agents which are not static can take actions.
        object.__setattr__(self, "_static", False)
        self.x = x
        self.y = y
        object.__setattr__(self, "_world", world)

    # name, object ID, and world cannot be set directly. name and ID are fixed at
    # at construction. world is set through the embed method below.
    def __setattr__(self, name, value):
        if name not in ["_objectName", "_objectID", "_world", "_static"]:
            object.__setattr__(self, name, value)

    @property
    def objectName(self):
        return self._objectName

    @property
    def objectID(self):
        return self._objectID

    def embed(self, world):
        self._world = world

    def place(self, world, x, y):
        if self._world is None:
            self._world = world
        if self._world == world:
            self.x = x
            self.y = y


class Action():

    # define the possible actions here
    inaction = -1
    move = 0

    # set up a basic action. An action stores the agent, what action it is doing,
    # in what direction the action is made, any possible object of the action (self.actedUpon),
    # and the action start point position.
    def __init__(self, agent, code, target, direction):

        self.agent = agent
        self.actionCode = code
        self.actionDirection = direction
        self.actedUpon = target
        self.x = agent.x
        self.y = agent.y


class GridAgent(GridObject):

    # set up the agent, which needs a name, an ID, a world to live in, and a start point.
    def __init__(self, name, obj_id=None, world=None, x=0, y=0):

        # call the generic GridObject constructor to set up common properties
        super().__init__("agent", obj_id, world, x, y)
        # no current action selected
        self._currentAction = Action(self, -1, None, 0)
        self.owned = []  # any objects the agent may possess
        # a dictionary of (x,y) positions containing a target dictionary of accessible locations with distances
        self._map = {}
        # initialise our start point so we know when the map is complete
        self._frontier = [(self.x, self.y)]
        # this will keep track of what our path has been, so we can navigate back to a starting point
        self._backtrack = []

    # don't allow arbitrary redirection of current actions
    def __setattr__(self, name, value):
        if name != "_currentAction":
            GridObject.__setattr__(self, name, value)

    # actionResult gives the agent its observation model: what happens when it takes an action. In general, in the GridWorld,
    # the observation will be a returned object or location indicating the agent successfully acquired the object or occupied
    # the location. If there were objects this agent could have removed in its location, it can interrogate
    # the occupants property of a returned location to check that the object in concern no longer exists.
    def actionResult(self, result):
        # filter out non-actions
        if self._currentAction.actionCode >= 0:
            # move action expects a GridPoint in return. Any result observations you add should check as below for
            # the correct class!
            if self._currentAction.actionCode == 0:
                if result.__class__.__name__ != "GridPoint":
                    raise ValueError("Expected a GridPoint class for a Move action, got a {0} class instead".format(
                        result.__class__.__name__))
                self.x = result.x
                self.y = result.y
            # any other actions you may implement should have their observed results dealt with here

    # this is the main function that generates intelligent behaviour. It implements
    # a 'policy': a mapping from the state (which you can get from the world, your x, y
    # position, and the occupants which you will get as a list), to an action.
    def chooseAction(self, world, x, y, occupants):

        # don't attempt to act in a world we're not in. This also prevents us from accidentally
        # resetting the world.
        if world != self._world:
            GridObject.__setattr__(
                self, "_currentAction", Action(self, -1, None, 0))
            return self._currentAction

        # TODO
        # --- Insert your actions here ---
        # Needed: explore the world. Decide if there's still something to explore, then
        # use appropriate search to explore the space.

        # default action is just a random move in some direction.

        actiondata = GridAgent._depthFirstExploration(self, world, x, y)
        if len(self._frontier) == 0:
            pprint("All locations found! Frontier length 0")
            pprint("Found " + str(len(self._corridors)))
            pprint("At Coordinates:")
            pprint(self._corridors)
        pprint("Frontier locations: " + str(len(self._frontier)))
        return self._currentAction

    # TODO
    # implement depth-first search, creating a map in the process
    # a depth-first exploration should proceed as far as it can, by choosing a direction at each point
    # where a decision is possible, then 'backtracking' once no further choices are available, back
    # to the last point where a choice was possible.
    def _depthFirstExploration(self, world, x, y):
        # FIXME build the map, indexed by (origin)(destination) pairs
        # Here im just setting up the map info, it contains the location and whether its directions can be accessed
        self._initrun = 1
        self._map[(x, y)] = {
            "access": {}
        }
        currentGrid = world._grid[y][x]
        self._map[(x, y)]["access"] = {
            "0": currentGrid.canGo(0),
            "1": currentGrid.canGo(1),
            "2": currentGrid.canGo(2),
            "3": currentGrid.canGo(3),
        }
        self._corridors = []
        self._map[x,y]["accessCount"] = 0
        # Adding the current location to backtrack for later use, also remove it from the fronteir as we have visited it!
        self._backtrack.append((x, y))
        self._removeFrontier(x, y)
        # This is how we determine if we need to backtrack, see my later comments
        move = False
        for direction in self._map[(x, y)]["access"]:
            # Loop through all the directions and make sure they are accessible
            if self._map[(x, y)]["access"][direction] == True:
                # Get the new coords for our accessable direction
                newlocation = currentGrid._neighbours[int(
                    direction)].x, currentGrid._neighbours[int(direction)].y
                # Have we been here before? is it in the frontier? if not we add it.
                if self._inFrontier(newlocation) == None and self._map.get(newlocation) == None:
                    self._frontier.append(newlocation)
                # It is in the frontier?! Great, lets go
                if self._inFrontier(newlocation) != None:
                    GridObject.__setattr__(self, "_currentAction", Action(
                        self, Action.move, None, direction))
                    move = True
            else:
                self._map[x,y]["accessCount"] + 1
         #Add it to corridors list for later if there is only 1 exit
        if self._map[x,y]["accessCount"] + 1 >= 3:
            self._corridors.append((x,y))
            pprint("Corridor found at " + x,y)
        # We are stuck here, lets go back a few steps
        if move == False:
            backMove = self._backtrackFunc(world)
            return backMove
        if self._frontier == None:
            pprint("discovered all points!")
        return self._currentAction

    # TODO
    # prune the map to get rid of uninteresting 'corridor' points where no turns are allowed
    def _pruneMap(self):
        locsToDelete = []  # list of map locations that can be pruned
        # FIXME this just exits
        while self._frontier is not None:
            self._frontier = None

    # convenience function allows us to extract the direction to a target location
    def _getDirection(self, target):
        if target[0] == self.x:
            if target[1] == self.y:
                return self._world.Nowhere
            elif target[1] > self.y:
                return self._world.South
            else:
                return self._world.North
        elif target[0] < self.x:
            if target[1] != self.y:
                return self._world.Nowhere
            else:
                return self._world.West
        else:
            if target[1] != self.y:
                return self._world.Nowhere
            else:
                return self._world.East

    # an efficient way to identify if a tuple is in a list. Creates a python generator expression to evaluate.
    def _inFrontier(self, target):
        try:
            nextTgt = next(
                loc for loc in self._frontier if loc[0] == target[0] and loc[1] == target[1])
        except StopIteration:
            return None
        return nextTgt

   #Convenience function to remove a location from the frontier
    def _removeFrontier(self, x, y):
        for location in self._frontier:
            if location == (x, y):
                self._frontier.remove(location)

    def _backtrackFunc(self, world):
        #loop is somewhat a cautionairy measure, not sure if its needed to be honest.
        while self._backtrack:
            #Take the current locaton off (as we have already added it) to avoid loops n such
            lastloc = self._backtrack.pop()
            backtrackDirection = self._getDirection(lastloc)
            #Security check, we shouldnt have a -1 result but this is part of our loops cautionary measures
            if backtrackDirection == -1:
                continue
            currentGrid = world._grid[self.y][self.x]
            #Make sure we dan acutually go that direction (damn those sneaky corridors)
            if currentGrid.canGo(backtrackDirection) == False:
                continue
            #Add the current location back for later backtracks
            self._backtrack.append(lastloc)
            print("Backing up!")
            #Make our move!
            return GridObject.__setattr__(self, "_currentAction", Action(self, Action.move, None, backtrackDirection))
