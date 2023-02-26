import tensorflow.keras as keras
from tensorflow.keras.layers import Dense


class ActorNetwork(keras.Model):
    def __init__(self):
        super(ActorNetwork, self).__init__()

        self.fc1 = Dense(10, activation='relu')
        self.fc2 = Dense(10, activation='relu')
        self.fc3 = Dense(2, activation='hard_sigmoid')

    def call(self, state):
        x = self.fc1(state)
        x = self.fc2(x)
        x = self.fc3(x)

        return x


class CriticNetwork(keras.Model):
    def __init__(self):
        super(CriticNetwork, self).__init__()
        self.fc1 = Dense(10, activation='relu')
        self.fc2 = Dense(10, activation='relu')
        self.q = Dense(1, activation=None)

    def call(self, state):
        x = self.fc1(state)
        x = self.fc2(x)
        x = self.q(x)

        return x