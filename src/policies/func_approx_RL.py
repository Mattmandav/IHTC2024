import numpy as np

class ApproxAgent:

    """
    A class to represent the functional approximation form of reinforcement learning 

    ...

    Attributes
    ----------


    Methods
    -------

    
    """

    def __init__(self, 
                 n_features: int = None, #I think default should be number of 'cost breakdowns'
                 n_actions: int = None, #default should be number of LLHs
                 learn_rate: float = float, 
                 discount_factor: float = float, 
                 critic_weights: list = list,
                 actor_weights: list = list,
                 dimension: int = None,
                 big_i: float = float,
                 td_error: float = float):
        """
        Constructs all the necessary attributes for the QLearner object`
        
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
          
        """

        self.__n_features = n_features
        self.__n_actions = n_actions
        self.__learn_rate = learn_rate
        self.__discount_factor = discount_factor
        self.__critic_weights = critic_weights
        self.__actor_weights = actor_weights
        self.__dimension = dimension
        self.__big_i = big_i
        self.__td_error = td_error

    def setCurrentState(self,state):
        self.__current_state = state
    
    def getCriticWeights(self):
        return self.__critic_weights
    
    def getNActions(self):
        return self.__n_actions

    def stateFeatureVector(self,solution_costs):

        #use self.costs in optimiser.py for solution_costs
        # self.costs = {"RoomAgeMix": [],
        #               "RoomSkillLevel": [],
        #               "ContinuityOfCare": [],
        #               "ExcessiveNurseWorkload": [],
        #               "OpenOperatingTheater": [],
        #               "SurgeonTransfer": [],
        #               "PatientDelay": [],
        #               "ElectiveUnscheduledPatients": []}

        #scaling features to be inbetween [-1,1]
        #doing this by dividing by 200,000 as this was the close to the largest cost i could see (i27)
        max_cost = 200000
        #features
        try:
            feature1 = ((solution_costs["RoomAgeMix"][-1]/max_cost)*2) -1
        except:
            feature1 = -1

        try:
            feature2 = ((solution_costs["RoomSkillLevel"][-1]/max_cost)*2) -1
        except:
            feature2 = -1

        try:
            feature3 = ((solution_costs["ContinuityOfCare"][-1]/max_cost)*2) -1
        except:
            feature3 = -1
        
        try:
            feature4 = ((solution_costs["ExcessiveNurseWorkload"][-1]/max_cost)*2) -1
        except:
            feature4 = -1

        try:
            feature5 = ((solution_costs["OpenOperatingTheater"][-1]/max_cost)*2) -1
        except:
            feature5 = -1
        
        try:
            feature6 = ((solution_costs["SurgeonTransfer"][-1]/max_cost)*2) -1
        except:
            feature6 = -1

        try:
            feature7 = ((solution_costs["PatientDelay"][-1]/max_cost)*2) -1
        except:
            feature7 = -1
        
        try:
            feature8 = ((solution_costs["ElectiveUnscheduledPatients"][-1]/max_cost)*2) -1
        except:
            feature8 = -1

        #set up feature vector
        x = []
        # I wholeheartedly apologise for this
        for d1 in range(self.__dimension+1):
            for d2 in range(self.__dimension+1):
                for d3 in range(self.__dimension+1):
                    for d4 in range(self.__dimension+1):
                        for d5 in range(self.__dimension+1):
                            for d6 in range(self.__dimension+1):
                                for d7 in range(self.__dimension+1):
                                    x += [ (feature1**d1) *
                                            (feature2**d2) * 
                                            (feature3**d3) * 
                                            (feature4**d4) * 
                                            (feature5**d5) *
                                            (feature6**d6) * 
                                            (feature7**d7) * 
                                            (feature8**d8) for d8 in range(self.__dimension+1)]
        return x

    def valueGradient(self,state):
        #likely just x(s)
        #vector of the features
        self.__value_grad = self.stateFeatureVector(state)

        return self.__value_grad

    def valueFunction(self,state):
        #x(s)*w
        #vector of features multiplied by self.__critic_weight
        return np.dot(self.stateFeatureVector(state),self.__critic_weights)

    def stateActionFeatureVector(self,solution_costs,action):
        #features
        #issue with actions, kind of want to put them in range of 0,1,2,...
        #but are actions arent really numeric in anyway
        #might need to do something along the lines of one-hot coding

        #scaling features to be inbetween [-1,1]
        #doing this by dividing by 200,000 as this was the close to the largest cost i could see (i27)
        max_cost = 200000
        #features
        try:
            feature1 = ((solution_costs["RoomAgeMix"][-1]/max_cost)*2) -1
        except:
            feature1 = -1

        try:
            feature2 = ((solution_costs["RoomSkillLevel"][-1]/max_cost)*2) -1
        except:
            feature2 = -1

        try:
            feature3 = ((solution_costs["ContinuityOfCare"][-1]/max_cost)*2) -1
        except:
            feature3 = -1
        
        try:
            feature4 = ((solution_costs["ExcessiveNurseWorkload"][-1]/max_cost)*2) -1
        except:
            feature4 = -1

        try:
            feature5 = ((solution_costs["OpenOperatingTheater"][-1]/max_cost)*2) -1
        except:
            feature5 = -1
        
        try:
            feature6 = ((solution_costs["SurgeonTransfer"][-1]/max_cost)*2) -1
        except:
            feature6 = -1

        try:
            feature7 = ((solution_costs["PatientDelay"][-1]/max_cost)*2) -1
        except:
            feature7 = -1
        
        try:
            feature8 = ((solution_costs["ElectiveUnscheduledPatients"][-1]/max_cost)*2) -1
        except:
            feature8 = -1
            
        #set up feature vector
        x = []
        # I wholeheartedly apologise for this
        for d1 in range(self.__dimension+1):
            for d2 in range(self.__dimension+1):
                for d3 in range(self.__dimension+1):
                    for d4 in range(self.__dimension+1):
                        for d5 in range(self.__dimension+1):
                            for d6 in range(self.__dimension+1):
                                for d7 in range(self.__dimension+1):
                                    x += [ (feature1**d1) *
                                            (feature2**d2) * 
                                            (feature3**d3) * 
                                            (feature4**d4) * 
                                            (feature5**d5) *
                                            (feature6**d6) * 
                                            (feature7**d7) * 
                                            (feature8**d8) for d8 in range(self.__dimension+1)]
        
        x += [0] * (action)
        x += [1]
        x += [0] * (self.__n_actions - action - 1)
        return x

    def preferenceFunction(self,state,action):
        #probably h(s,a,theta) = features but considering an action
        return np.dot(self.stateActionFeatureVector(state,action), self.__actor_weights)


    def policyGradient(self,state,action):
        #x(s,a) - sum_b pi(b)*x(s,b)
        feature_vectors = [self.stateActionFeatureVector(state,a) for a in range(self.__n_actions)]
        policy_probs_numerator = np.exp([np.dot(feature_vectors[a],self.__actor_weights) for a in range(self.__n_actions)])
        probabilities = policy_probs_numerator/np.sum(policy_probs_numerator)
        eligibility_vector = feature_vectors[action] - np.sum([np.array(feature_vectors[a])*probabilities[a] for a in range(self.__n_actions)] )
        return eligibility_vector

    def sampleFromPolicy(self,state):
        #sample from softmax distribution
        soft_max_numerator = np.exp([self.preferenceFunction(state,action) for action in range(self.__n_actions)])
        probs = soft_max_numerator/np.sum(soft_max_numerator)
        action = np.random.choice(a  = range (self.__n_actions ),
                                  size = 1,
                                  p = probs)
        return action[0]

    def evalTDError(self,reward,new_state,curr_state):
        # R + gamma*value(new state) - value(current state)
        self.__td_error =  reward + self.__discount_factor*self.valueFunction(new_state) - self.valueFunction(curr_state)
    
    def actorUpdate(self,state,action):
        #SGD on policy
        #theta <- theta + alpha*TDerror*I*policyGrad
        self.__actor_weights = self.__actor_weights + self.__learn_rate*self.__td_error*self.__big_i*self.policyGradient(state,action)

    def criticUpdate(self,state):
        #SGD on value function
        # w <- w + alpha*TDerror*valueGrad
        self.__critic_weights = self.__critic_weights + self.__learn_rate*self.__td_error*np.array(self.valueGradient(state))

    def resetBigI(self,BigI):
        self.__big_i = BigI
    
    def updateBigI(self):
        self.__big_i = self.__big_i * self.__discount_factor