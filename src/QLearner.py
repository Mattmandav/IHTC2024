import numpy as np

class QLearner:

    """
    A class to represent the tabular form of reinforcement learning known as Q-learning

    ...

    Attributes
    ----------
    n_states: tuple(int)
        number of states in the Markov desicion process (MDP) environment

    n_actions: tuple(int)
        number of actions in the MDP environment

    learn_rate: float
        learning rate/step size of the Q-learning algorithm
        takes value between [0,1]

    discount_factor: float
        discount factor of the Q-learning algorithm
        takes value between [0,1]

    q_table: np.array[float]
        table of size n_states*n_actions that holds all Q-values of the Q-learning algorithm

    current_state: tuple(int)
        the state of the MDP that the Q-learner is currently in

    new_state: tuple(int)
        the state of the MDP that the Q-learner observes after taking an action

    Methods
    -------
    getNStates() -> tuple(int):
        returns number of states in the MDP environment

    setNStates(number_of_states: tuple(int)):
        changes Q-Learner's n_states attribute to 'number_of_states'

    getNActions() -> tuple(int):
        returns number of actions in the MDP environment

    setNActions(number_of_actions: tuple(int)):
        changes Q-Learner's n_actions attribute to 'number_of_actions' 
    
    getLearnRate() -> float:
        returns the learning rate/step size of the Q-Learning algorithm

    setLearnRate(learning_rate: float)
        changes the Q-Learner's learn_rate attribute to the float 'learning_rate'
    
    getDiscountFactor() -> float:
        returns the discount factor of the Q-Learning algorithm

    setDiscountFactor(discount_factor: float):
        changes the Q-Learner's discount_factor attribute to the float 'discount_factor'    
    
    getQTable() -> np.array[float]:
        returns the Q-table of the Q-learning algorithm

    setQTable(q_table: np.array[float]):
        changes the Q-Learner's q_table attribute to the np.array[float] 'q_table'
    
    initialiseQTable(q_value: float):
        creates a Q-table of size |States|*|Actions|, with all values initialised at float 'q_table'
    
    getQValue(state: tuple(int), action: tuple(int)) -> float:
        returns the Q-value of a state-action pair

    setQValue(state: tuple(int), action: tuple(int), q_value: float):
        Changes Q-value of Q(S,A) to the float 'q_value'    

    getBestAction(state: tuple(int)) -> tuple(int):
        returns the actions that corresponds to the argmax Q-table(state,:) 
    
    getCurrentState() -> tuple(int):
        returns the current state of the MDP that the Q-learner is in

    setCurrentState(state: tuple(int)):
        changes the current state of the Q-learner in the MDP to the int 'state'

    getNewState() -> tuple(int):
        returns the new state the Q-learner observes after taking an action

    setNewState(state: tuple(int)):
        changes the new state that is observed by the Q-Learner after taking an action
    
    QLearningUpdate(action: tuple(int), reward: float):
        Updates the current Q(S,A) value according to the Q-learning update step of the algorithm
    
    """

    def __init__(self, 
                 n_states: tuple = None, 
                 n_actions: tuple = tuple, 
                 learn_rate: float = float, 
                 discount_factor: float = float, 
                 q_table: np.array = np.array,
                 current_state: tuple = None,
                 new_state: tuple = None):
        """
        Constructs all the necessary attributes for the QLearner object
        
        Parameters
        ----------
            n_states: tuple(int), optional
                number of states in the Markov decision process that the Q-learner interacts with
                (default of tuple(int))

            n_actions: tuple(int), optional
                number of actions in the Markov decision process that the Q-learner interacts with
                (default is tuple(int))

            learn_rate: float, optional
                learning rate/step size of the Q-learning algorithm 
                takes value between [0,1]
                (default is float)

            discount_factor: float, optional
                discount factor of the Q-learning algorithm to help approximate discounted return of state-action pairs
                takes value between [0,1]
                (default is float)
            
            q_table: np.array[float], optional
                Q Table that holds all teh Q-values of each state-action pair
                (default is np.array[float])

            current_state: tuple(int), optional
                the state of the MDP that the Q-Learner is currently in
                (default is int)
            
            new_state: tuple(int), optional
                the state the of the MDP that Q-learner is moving to after taking an action
        """

        self.__n_states = n_states
        self.__n_actions = n_actions
        self.__learn_rate = learn_rate
        self.__discount_factor = discount_factor
        self.__q_table = q_table
        self.__current_state = current_state
        self.__new_state = new_state

    def getNStates(self) -> tuple:
        """Returns number of states in the MDP"""
        return self.__n_states
    
    def setNStates(self, number_of_states: tuple):
        """
        Changes the Q-learner's n_states attribute to tuple(int) 'number_of_states'

        Parameters
        ----------
            number_of_states: tuple
                number of states in the MDP
        """
        self.__n_states = number_of_states

    def getNActions(self) -> tuple:
        """Returns number of actions in the MDP"""
        return self.__n_actions
    
    def setNActions(self, number_of_actions: tuple):
        """
        Changes the Q-learner's n_actions attribute to tuple 'number_of_actions'

        Parameters
        ----------
            number_of_actions: tuple
                number of actions in the MDP
        """
        self.__n_actions = number_of_actions

    def getLearnRate(self) -> float:
        """Returns the learning rate of the Q-learning algorithm"""
        return self.__learn_rate
    
    def setLearnRate(self, learning_rate: float):
        """
        Changes the Q-learner's learn_rate attribute to float 'learning_rate'

        Parameters
        ----------
            learning_rate: float
                learning rate/step size of the Q-learning algorithm
                takes value between [0,1]
        """
        self.__learn_rate = learning_rate

    def getDiscountFactor(self) -> float:
        """Returns the discount factor of the Q-learning algorithm"""
        return self.__discount_factor
    
    def setDiscountFactor(self, discount_factor: float):
        """
        Changes the Q-learner's discount_factor attribute to float 'discount_factor'

        Parameters
        ----------
            discount_factor: float
                discount_factor of the Q-learning algorithm
                takes value between [0,1]
        """
        self.__discount_factor = discount_factor

    def getQTable(self) -> np.array:
        """Returns the Q-table of the Q-learner"""
        return self.__q_table
    
    def setQTable(self, q_table: np.array):
        """
        Changes the q_table attribute to the np.array[float] 'q_table'

        Parameters
        ----------
            q_table: np.array[float]
                Q table used in the Q-learning algorithm, holds the Q-value for every state-action pair 
        """
        self.__q_table = q_table

    def initialiseQTable(self, q_value: float = 0.0):
        """
        Initialises the Q-table for the Q-learning algorithm dependent on the number of states and actions of the MDP

        Parameters
        ----------
            q_value: float, optional
                Initial Q-value that is applied to eery vstate-action pair
                (default is 0)
        """
        #Create an array of size |States|*|Actions|, and then add initial Q-Value
        if self.__n_states == None:
            self.__q_table = np.zeros(self.__n_actions) + q_value

        elif type(self.__n_states) == tuple and type(self.__n_actions) == tuple:
            self.__q_table = np.zeros(self.__n_states + self.__n_actions) + q_value

        elif type(self.__n_states) == tuple:
            self.__q_table = np.zeros(self.__n_states + (self.__n_actions,)) + q_value
        
        elif type(self.__n_actions) == tuple:
            self.__q_table = np.zeros((self.__n_states,) + self.__n_actions) + q_value
        
        else:
            self.__q_table = np.zeros((self.__n_states,) + (self.__n_actions,)) + q_value

    def getQValue(self, state: tuple, action: tuple) -> float:
        """
        Returns the Q-value of a specific state-action pair
        
        Parameters
        ----------
            state: tuple
                state of the wanted value

            action: tuple
                action of the wanted value
        """
        return self.__q_table[state,action]
    
    def setQValue(self, state: tuple, action: tuple, q_value: float):
        """
        Changes a Q-value for a specific state-action pair to teh float 'q_value'

        Parameters
        ----------
            state: int
                state of the value we want to change

            action: int
                action of the value we want to change

            q_value: float
                the float value we want to change the q_value to
        """
    
        self.__q_table[state,action] = q_value

    def getBestActionInt(self, state: tuple = None) -> int:
        """
        Returns the action that maximises the Q-values of a specific state as an integer
        
        Parameters
        ----------
            state: tuple
                state to find the argmax of
        """
        if state == None:
            return np.argmax(self.__q_table[...])
        elif type(state) == tuple:
            return np.argmax(self.__q_table[state + (...,)])
        else:
            return np.argmax(self.__q_table[(state,) + (...,)])
    
    def getBestAction(self, state: tuple = None) -> tuple:
        """
        Returns the action that maximises the Q-values of a specific state as a tuple
        
        Parameters
        ----------
            state: tuple
                state to find the argmax of
        """
        if state == None:
            return tuple(np.unravel_index(self.__q_table.argmax(), self.__q_table.shape))
        return tuple(np.unravel_index(self.__q_table[state + (...,)].argmax(), self.__q_table[state + (...,)].shape))
    
    def getCurrentState(self) -> tuple:
        """Returns the current state of the MDP that the Q-Learner is currently in"""
        return self.__current_state
    
    def setCurrentState(self, state: tuple):
        """
        Changes the Q-learner's current_state attribute to the int 'state'
        
        Parameters
        ----------
            state: tuple
                current state of the MDP we want to put the Q-learner in
        """
        self.__current_state = state

    def getNewState(self) -> tuple:
        """Returns the new state that the Q-learner has observed after taking an action"""
        return self.__new_state
    
    def setNewState(self, state: tuple):
        """
        Changes the Q-Learner's new_state attribute to the int 'state'

        Parameters
        ----------
            state: int
                new state in the MDP that the Q-learner observes after taking an action 
        """
        self.__new_state = state

    def QLearningUpdate(self, action: tuple, reward: float):
        """
        Updates the Q-learner's Q-value for the current state and action according to the Q-learning update step
        
        Parameters
        ----------
            action: int
                action taken by the Q-learner at this step of the algorithm
                the Q-value ofthe current state-action pair will be updated

            reward: float
                current realisation of the reward function given to teh Q-leaner
                will be used to update the current Q(S,A) value
        """
        if self.__n_states == None:
            self.__q_table[action] = (1 - self.__learn_rate)*self.__q_table[action] + self.__learn_rate*reward
        elif type(self.__n_states) == tuple and type(self.__n_actions) == tuple:
            self.__q_table[self.__current_state + action] = (1 - self.__learn_rate)*self.__q_table[self.__current_state + action] + self.__learn_rate*(reward + self.__discount_factor*np.max(self.__q_table[self.__new_state + (...,)]))
        elif type(self.__n_states) == tuple:
            self.__q_table[self.__current_state + (action,)] = (1 - self.__learn_rate)*self.__q_table[self.__current_state + (action,)] + self.__learn_rate*(reward + self.__discount_factor*np.max(self.__q_table[self.__new_state + (...,)]))
        else:
            self.__q_table[(self.__current_state,)+(action,)] = (1 - self.__learn_rate)*self.__q_table[(self.__current_state,)+(action,)] + self.__learn_rate*(reward + self.__discount_factor*np.max(self.__q_table[(self.__new_state,) + (...,)]))    