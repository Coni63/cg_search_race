import glob
import random
import numpy as np


from ai import Agent, Adapter
from game import GameManager, Renderer


files = glob.glob("testcases/**json")

"""
renderer = None
renderer = Renderer()
game = GameManager(renderer=renderer)
game.set_testcase(random.choice(files))
input("")
"""

if __name__ == '__main__':
    game = GameManager(renderer=None)
    n_games = 300
    agent = Agent(n_actions=2,
                  batch_size=5,
                  alpha=0.0003,
                  n_epochs=4,
                  input_dims=5)

    best_score = 0
    score_history = []
    learn_iters = 0
    avg_score = 0
    n_steps = 0
    N = 20

    for i in range(n_games):
        pod, checkpoints = game.set_testcase(random.choice(files))
        observation = Adapter.game_to_state(pod, checkpoints)
        done = False
        score = 0
        while not done:
            output, prob, val = agent.choose_action(observation)
            action = Adapter.prediction_to_action(output)
            pod, reward, done = game.step(action)
            observation_ = Adapter.game_to_state(pod, checkpoints)
            n_steps += 1
            score += reward
            agent.store_transition(observation, action, prob, val, reward, done)
            if n_steps % N == 0:
                agent.learn()
                learn_iters += 1
            observation = observation_
        score_history.append(score)
        avg_score = np.mean(score_history[-100:])

        if avg_score > best_score:
            best_score = avg_score
            agent.save_models()

        print(f'episode {i} - score {score:1f} - avg {avg_score:.1f} - time_steps {n_steps} - learning_steps {learn_iters}')
