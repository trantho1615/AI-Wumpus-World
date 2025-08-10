from environment import Environment
from agent import KBWumpusAgent
from agent import RandomWumpusAgent

def run_random_agent():
    env = Environment(size=4, num_wumpus=1, pit_prob=0.2)
    agent = RandomWumpusAgent(env)

    steps = 0
    while not agent.done and steps < 50:
        percepts = env.get_percepts(agent.position, bump=getattr(agent, "bump", False))
        agent.perceive(percepts)
        percepts["bump"] = getattr(agent, "bump", False)
        percepts["scream"] = env.scream

        action = agent.choose_action()
        print(f"[Step {steps}] Action: {action}")

        env.apply_action(agent, action)
        
        if action == "move":
            agent.update_position_on_move()

        env.print_state(agent)
        steps += 1


def run_game():
    env = Environment(size=4, num_wumpus=1, pit_prob=0.2)
    agent = KBWumpusAgent(env)

    steps = 0

    # Open the file for writing logs
    with open("game_log.txt", "w") as log_file:
        while not agent.done and steps < 50:
            percepts = env.get_percepts(agent.position, bump=getattr(agent, "bump", False))
            agent.perceive(percepts)

            percepts["bump"] = getattr(agent, "bump", False)
            percepts["scream"] = env.scream

            action = agent.choose_action()

            # Create the log string
            log_str = (
                f"[Step {steps}] Action: {action}, "
                f"Position: {agent.position}, "
                f"Direction: {agent.direction}, "
                f"Has Gold: {agent.has_gold}, "
                f"Scream: {percepts.get('scream', False)}, "
                f"Bump: {percepts.get('bump', False)}"
            )

            print(log_str)
            log_file.write(log_str + "\n")

            env.apply_action(agent, action)
            env.print_state(agent)
            steps += 1


if __name__ == "__main__":
    run_game()