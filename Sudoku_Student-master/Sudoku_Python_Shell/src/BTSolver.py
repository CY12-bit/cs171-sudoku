import SudokuBoard
import Variable
import Domain
import Trail
import Constraint
import ConstraintNetwork
import time
import random

class BTSolver:

    # ==================================================================
    # Constructors
    # ==================================================================

    def __init__ ( self, gb, trail, val_sh, var_sh, cc ):
        self.network = ConstraintNetwork.ConstraintNetwork(gb)
        self.hassolution = False
        self.gameboard = gb
        self.trail = trail

        self.varHeuristics = var_sh
        self.valHeuristics = val_sh
        self.cChecks = cc
    

    # ==================================================================
    # Consistency Checks
    # ==================================================================

    # Basic consistency check, no propagation done
    def assignmentsCheck ( self ):
        for c in self.network.getConstraints():
            if not c.isConsistent():
                return False
        return True

    """
        Part 1 TODO: Implement the Forward Checking Heuristic

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        Note: remember to trail.push variables before you assign them
        Return: a tuple of a dictionary and a bool. The dictionary contains all MODIFIED variables, mapped to their MODIFIED domain.
                The bool is true if assignment is consistent, false otherwise.
    """
    def forwardChecking(self):
        def removeValueFromNeighbors(v):
            assignment = v.getAssignment()
            neighbors = self.network.getNeighborsOfVariable(v)
            for neigh in neighbors:
                if not neigh.isAssigned() and neigh.getDomain().contains(assignment):
                    self.trail.push(neigh)
                    neigh.removeValueFromDomain(assignment)
                    if neigh.getDomain().isEmpty(): return ({}, False)
                    # Not sure if I should assign the neighbor if its domain size is 1
                    # If not needed, could legit just trackback to last assigned value (self.lastAssigned)
                    # elif neigh.size() == 1:
                    #    self.trail.push(neigh)
                    #    neigh.assignValue(neigh.domain.values[0])
                    #    neigh.setModified(True)
            
            return ({},self.assignmentsCheck())
        
        for v in self.network.variables:
            if v.isAssigned() and v.isModified(): # Very weird 'modified' status
                checkResults = removeValueFromNeighbors(v)
                v.setModified(False) # Very weird 'modified' status. So now not RECENTLY modified
                if checkResults[1] == False: return ({},False)

        return ({},True) 
           
    # =================================================================
	# Arc Consistency
	# =================================================================
    def arcConsistency( self ):
        assignedVars = []
        for c in self.network.constraints:
            for v in c.vars:
                if v.isAssigned():
                    assignedVars.append(v)
        while len(assignedVars) != 0:
            av = assignedVars.pop(0)
            for neighbor in self.network.getNeighborsOfVariable(av):
                if neighbor.isChangeable and not neighbor.isAssigned() and neighbor.getDomain().contains(av.getAssignment()):
                    neighbor.removeValueFromDomain(av.getAssignment())
                    if neighbor.domain.size() == 1:
                        neighbor.assignValue(neighbor.domain.values[0])
                        assignedVars.append(neighbor)

    
    """
        Part 2 TODO: Implement both of Norvig's Heuristics

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        (2) If a constraint has only one possible place for a value
            then put the value there.

        Note: remember to trail.push variables before you assign them
        Return: a pair of a dictionary and a bool. The dictionary contains all variables 
		        that were ASSIGNED during the whole NorvigCheck propagation, and mapped to the values that they were assigned.
                The bool is true if assignment is consistent, false otherwise.
    """
    def norvigCheck ( self ):
        def returnOnlyUnassigned(c):
            unassigned_v = None
            for v in c.vars:
                if not v.isAssigned():
                    if unassigned_v == None:
                        unassigned_v = v
                    else: return False
            return unassigned_v
        def removeValueFromNeighbors(v):
            assignment = v.getAssignment()
            neighbors = self.network.getNeighborsOfVariable(v)
            for neigh in neighbors:
                if not neigh.isAssigned() and neigh.getDomain().contains(assignment):
                    self.trail.push(neigh)
                    neigh.removeValueFromDomain(assignment)
                    if neigh.getDomain().isEmpty(): return ({}, False)
                    # Not sure if I should assign the neighbor if its domain size is 1
                    # elif neigh.size() == 1:
                    #     self.trail.push(neigh)
                    #     neigh.assignValue(neigh.domain.values[0])
                    #     neigh.setModified(True)
            return ({},self.assignmentsCheck())

        for v in self.network.variables:
            if v.isAssigned() and v.isModified(): # Very weird 'modified' status
                checkResults = removeValueFromNeighbors(v)
                v.setModified(False) # Very weird 'modified' status
                if checkResults[1] == False: return ({},False)
       
        # Now, we check all constraints to see if there's only one unassigned variable in each constraint
        for c in self.network.constraints:
            last_unassigned = returnOnlyUnassigned(c)
            # If there is only one un-assigned variable in the constraint
            if last_unassigned not in (None, False):
                self.trail.push(last_unassigned)
                last_unassigned.assignValue(last_unassigned.domain.values[0])
                last_unassigned.setModified(True) # Very weird 'modified' status
        
        return ({},self.assignmentsCheck())

    """
         Optional TODO: Implement your own advanced Constraint Propagation

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournCC ( self ):
        # Exact Cover 
        return False

    # ==================================================================
    # Variable Selectors
    # ==================================================================

    # Basic variable selector, returns first unassigned variable
    def getfirstUnassignedVariable ( self ):
        for v in self.network.variables:
            if not v.isAssigned():
                return v

        # Everything is assigned
        return None

    """
        Part 1 TODO: Implement the Minimum Remaining Value Heuristic

        Return: The unassigned variable with the smallest domain
    """
    def getMRV ( self ):
        min_var = None 
        for v in self.network.variables:
            if not v.isAssigned() and (min_var == None or min_var.size() > v.size()):
                min_var = v
        return min_var
    """
        Part 2 TODO: Implement the Minimum Remaining Value Heuristic
                       with Degree Heuristic as a Tie Breaker

        Return: The unassigned variable with the smallest domain and affecting the  most unassigned neighbors.
                If there are multiple variables that have the same smallest domain with the same number of unassigned neighbors, add them to the list of Variables.
                If there is only one variable, return the list of size 1 containing that variable.
    """
    def MRVwithTieBreaker ( self ):
        min_var = list()
        for v in self.network.variables:
            if not v.isAssigned():
                if len(min_var) == 0:
                    min_var.append(v)
                elif min_var[-1].size() > v.size():
                    min_var.clear()
                    min_var.append(v)
                elif min_var[-1].size() == v.size():
                    min_var.append(v)
        return sorted(min_var, key = lambda x : sum(1 if n.isAssigned() == False else 0 for n in self.network.getNeighborsOfVariable(x))) if len(min_var) != 0 else [None]

    """
         Optional TODO: Implement your own advanced Variable Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournVar ( self ):
        return None

    # ==================================================================
    # Value Selectors
    # ==================================================================

    # Default Value Ordering
    def getValuesInOrder ( self, v ):
        values = v.domain.values
        return sorted( values )

    """
        Part 1 TODO: Implement the Least Constraining Value Heuristic

        The Least constraining value is the one that will knock the least
        values out of it's neighbors domain.

        Return: A list of v's domain sorted by the LCV heuristic
                The LCV is first and the MCV is last
    """
    # Colin will take this one
    def getValuesLCVOrder ( self, v ):
        def returnNeighsContains(val, neighs:list):
            return sum(n.getDomain().contains(val) for n in neighs)
        values = v.domain.values
        neighs = self.network.getNeighborsOfVariable(v)
        return sorted(values, key = lambda x: returnNeighsContains(x,neighs))


    """
         Optional TODO: Implement your own advanced Value Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournVal ( self, v ):
        return None

    # ==================================================================
    # Engine Functions
    # ==================================================================

    def solve ( self, time_left=600):
        if time_left <= 60:
            return -1

        start_time = time.time()
        if self.hassolution:
            return 0

        # Variable Selection
        v = self.selectNextVariable()
        # print(v)
        # check if the assigment is complete
        if ( v == None ):
            # Success
            self.hassolution = True
            return 0

        # Attempt to assign a value
        for i in self.getNextValues( v ):

            # Store place in trail and push variable's state on trail
            self.trail.placeTrailMarker()
            self.trail.push( v )

            # Assign the value
            v.assignValue( i )


            # Propagate constraints, check consistency, recur
            if self.checkConsistency():
                elapsed_time = time.time() - start_time 
                new_start_time = time_left - elapsed_time
                if self.solve(time_left=new_start_time) == -1:
                    return -1

            # If this assignment succeeded, return
            if self.hassolution:
                return 0

            # Otherwise backtrack
            self.trail.undo()
        
        return 0

    def checkConsistency ( self ):
        if self.cChecks == "forwardChecking":
            return self.forwardChecking()[1]

        if self.cChecks == "norvigCheck":
            return self.norvigCheck()[1]

        if self.cChecks == "tournCC":
            return self.getTournCC()

        else:
            return self.assignmentsCheck()

    def selectNextVariable ( self ):
        if self.varHeuristics == "MinimumRemainingValue":
            return self.getMRV()

        if self.varHeuristics == "MRVwithTieBreaker":
            return self.MRVwithTieBreaker()[0]

        if self.varHeuristics == "tournVar":
            return self.getTournVar()

        else:
            return self.getfirstUnassignedVariable()

    def getNextValues ( self, v ):
        if self.valHeuristics == "LeastConstrainingValue":
            return self.getValuesLCVOrder( v )

        if self.valHeuristics == "tournVal":
            return self.getTournVal( v )

        else:
            return self.getValuesInOrder( v )

    def getSolution ( self ):
        return self.network.toSudokuBoard(self.gameboard.p, self.gameboard.q)