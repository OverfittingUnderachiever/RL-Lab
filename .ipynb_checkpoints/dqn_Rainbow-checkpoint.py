{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {
    "nbgrader": {
     "grade": false,
     "grade_id": "cell-4ef3965059d37f2e",
     "locked": true,
     "schema_version": 3,
     "solution": false,
     "task": false
    }
   },
   "source": [
    "# DQN + Rainbow\n",
    "By Henry Frey, Vanessa Stöckl, Seif Saleh, Yi-Chieh Lin\n",
    "\n",
    "RL lab homework DQN notebook used as base: Prof. Joschka Bödecker, Julien Brosseit"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {
    "nbgrader": {
     "grade": false,
     "grade_id": "cell-dcf2e438bf23416e",
     "locked": true,
     "schema_version": 3,
     "solution": false,
     "task": false
    }
   },
   "source": [
    "## 0 Setup\n",
    "These are the same packages as in the last exercise:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {
    "nbgrader": {
     "grade": false,
     "grade_id": "cell-df50e80428bfd961",
     "locked": true,
     "schema_version": 3,
     "solution": false,
     "task": false
    }
   },
   "outputs": [],
   "source": [
    "!pip install torch torchvision torchaudio\n",
    "!pip install gymnasium==0.29.1\n",
    "!pip install minatar==1.0.15\n",
    "!pip install matplotlib\n",
    "!pip install imageio"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {
    "nbgrader": {
     "grade": false,
     "grade_id": "cell-56f2e20fd1046476",
     "locked": true,
     "schema_version": 3,
     "solution": false,
     "task": false
    }
   },
   "outputs": [],
   "source": [
    "# Imports\n",
    "import torch\n",
    "import torch.nn as nn\n",
    "import torch.optim as optim\n",
    "import torch.nn.functional as F\n",
    "\n",
    "import copy\n",
    "import numpy as np\n",
    "import pandas as pd\n",
    "import random\n",
    "from PIL import Image\n",
    "import gymnasium as gym\n",
    "import matplotlib.pyplot as plt\n",
    "from typing import Callable\n",
    "from collections import namedtuple\n",
    "import itertools"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {
    "nbgrader": {
     "grade": false,
     "grade_id": "cell-0a59a0023deaf069",
     "locked": true,
     "schema_version": 3,
     "solution": false,
     "task": false
    }
   },
   "source": [
    "## 1 Deep Q-Networks\n",
    "Remember, in Q-learning, we have the following update:\n",
    "\n",
    "$Q(s,a) \\leftarrow Q(s,a) + \\alpha (r + \\gamma \\max_{a'}Q(s', a') - Q(s, a))$\n",
    "\n",
    "with discount factor $\\gamma$, learning rate $\\alpha$, reward $r$, sampled state $s$, sampled next state $s'$ and sampled action $a$. Instead of a table, we will now use a neural network to represent the Q-function $Q(s, a; \\theta)$, where $\\theta$ are the parameters of the neural network. In order to learn the Q-function, we minimize the Mean Squared Error loss between our current estimate and our TD target using Stochastic gradient descent (SGD):\n",
    "\n",
    "$ L(\\theta) = \\mathop{{}\\mathbb{E}}_{(s, a, r, s') \\sim D}([r + \\gamma \\max_{a'}Q(s', a'; \\theta') - Q(s, a; \\theta)]^2 )$  \n",
    "\n",
    "where D is a dataset of sampled transitions and $\\theta'$ are old parameters. This is very similar to how we train in a supervised learning setting!\n",
    "\n"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {
    "nbgrader": {
     "grade": false,
     "grade_id": "cell-17ce9540304ffb57",
     "locked": true,
     "schema_version": 3,
     "solution": false,
     "task": false
    }
   },
   "source": [
    "## 1.1 Q-Network\n",
    "\n",
    "Since we are representing our Q-function as a deep neural network, we will first define it using PyTorch. Then we will define the epsilon greedy policy and introduce how to decay the epsilon over time.\n",
    "\n",
    "---\n",
    "\n",
    "\n",
    "In the DQN paper, the network structure used is described as follows (although we have changed the hyperparameters!):\n",
    "> The input to the neural network consists [..] [of] an 10 × 10 × n image [...]. The first hidden layer convolves 16 5 × 5\n",
    "> filters with stride 1 with the input image and applies a rectifier nonlinearity. The second \n",
    "> hidden layer convolves 32 3 × 3 filters with stride 1, again followed by a rectifier nonlinearity. The\n",
    "> final hidden layer is fully-connected and consists of 128 rectifier units. The output layer is a fully-\n",
    "> connected linear layer with a single output for each valid action."
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "<span style=\"color:orange\">**DQN**</span>"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 3,
   "metadata": {
    "nbgrader": {
     "grade": false,
     "grade_id": "cell-be61a701fe523b29",
     "locked": false,
     "schema_version": 3,
     "solution": true,
     "task": false
    }
   },
   "outputs": [],
   "source": [
    "class DQN(nn.Module):\n",
    "    def __init__(self, obs_shape: torch.Size, num_actions: int):\n",
    "        \"\"\"\n",
    "        Initialize the DQN network.\n",
    "        \n",
    "        :param obs_shape: Shape of the observation space\n",
    "        :param num_actions: Number of actions\n",
    "        \"\"\"\n",
    "\n",
    "        # obs_shape is the shape of a single observation -> use this information to define the dimensions of the layers\n",
    "        super(DQN, self).__init__()\n",
    "\n",
    "        # TODO: Your code here\n",
    "        ### BEGIN SOLUTION\n",
    "        self.conv1 = nn.Conv2d(obs_shape[-1], 16, stride=1, kernel_size=5)\n",
    "        self.conv2 = nn.Conv2d(16, 32, stride=1, kernel_size=3)\n",
    "        \n",
    "        self.fc1 = nn.Linear(32 * 4 * 4, 128)\n",
    "        self.fc2 = nn.Linear(128, num_actions)\n",
    "\n",
    "        self.relu = nn.ReLU()\n",
    "        ### END SOLUTION\n",
    "\n",
    "\n",
    "    def forward(self, x: torch.Tensor) -> torch.Tensor:\n",
    "        # TODO: Your code here\n",
    "        ### BEGIN SOLUTION\n",
    "        x = x.permute(0, 3, 1, 2)\n",
    "\n",
    "        x = self.relu(self.conv1(x))\n",
    "        x = self.relu(self.conv2(x))\n",
    "\n",
    "        x = torch.flatten(x, 1) # flatten the intermediate result such that it can serve as input for the first linear layer\n",
    "\n",
    "        # Final layer consists of 128 \"rectifier\" units meaning a ReLU activation\n",
    "        x = self.relu(self.fc1(x))\n",
    "        out = self.fc2(x)\n",
    "        return out\n",
    "        ### END SOLUTION\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 4,
   "metadata": {
    "nbgrader": {
     "grade": true,
     "grade_id": "cell-24c6c6109bb92421",
     "locked": true,
     "points": 3,
     "schema_version": 3,
     "solution": false,
     "task": false
    }
   },
   "outputs": [],
   "source": [
    "# Test\n",
    "\n",
    "# Create dummy input\n",
    "x_dummy = torch.randn(1, 10, 10, 4)\n",
    "dqn = DQN(x_dummy.shape, 4)\n",
    "\n",
    "assert dqn(x_dummy).shape == (1, 4), f\"Expected output shape (1, 4) but got {dqn(x_dummy).shape}\"\n",
    "### BEGIN HIDDEN TESTS\n",
    "# Check whether the network has two conv layers and two linear\n",
    "assert len([m for m in dqn.modules() if isinstance(m, nn.Conv2d)]) == 2, \"Expected 2 Conv2d layers\"\n",
    "assert len([m for m in dqn.modules() if isinstance(m, nn.Linear)]) == 2, \"Expected 2 Linear layers\"\n",
    "### END HIDDEN TESTS\n"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {
    "nbgrader": {
     "grade": false,
     "grade_id": "cell-553b6fd9513de2d4",
     "locked": true,
     "schema_version": 3,
     "solution": false,
     "task": false
    }
   },
   "source": [
    "We import the epsilon greedy policy from our previous exercise. Note that we made some changes because Q is a network and epsilon is no longer fixed. "
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "\n",
    "<span style=\"color:orange\">**Policy**</span>"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {
    "nbgrader": {
     "grade": false,
     "grade_id": "cell-14bdfcbb4e00c5ac",
     "locked": true,
     "schema_version": 3,
     "solution": false,
     "task": false
    }
   },
   "outputs": [],
   "source": [
    "def make_epsilon_greedy_policy(Q: nn.Module, num_actions: int):\n",
    "    \"\"\"\n",
    "    Creates an epsilon-greedy policy based on a given Q-function and epsilon. Taken from last exercise with changes.\n",
    "\n",
    "    :param Q: The DQN network.\n",
    "    :param num_actions: Number of actions in the environment.\n",
    "\n",
    "    :returns: A function that takes the observation as an argument and returns the greedy action in form of an int.\n",
    "    \"\"\"\n",
    "\n",
    "    def policy_fn(obs: torch.Tensor, epsilon: float = 0.0):\n",
    "        \"\"\"This function takes in the observation and returns an action.\"\"\"\n",
    "        if np.random.uniform() < epsilon:\n",
    "            return np.random.randint(0, num_actions)\n",
    "        \n",
    "        # For action selection, we do not need a gradient and so we call \".detach()\"\n",
    "        return Q(obs).argmax().detach().numpy()\n",
    "\n",
    "    return policy_fn"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 6,
   "metadata": {
    "nbgrader": {
     "grade": false,
     "grade_id": "cell-5e7b907fe8f217fe",
     "locked": false,
     "schema_version": 3,
     "solution": true,
     "task": false
    }
   },
   "outputs": [],
   "source": [
    "def linear_epsilon_decay(eps_start: float, eps_end: float, current_timestep: int, duration: int) -> float:\n",
    "    \"\"\"\n",
    "    Linear decay of epsilon.\n",
    "\n",
    "    :param eps_start: The initial epsilon value.\n",
    "    :param eps_end: The final epsilon value.\n",
    "    :param current_timestep: The current timestep.\n",
    "    :param duration: The duration of the schedule (in timesteps). So when schedule_duration == current_timestep, eps_end should be reached\n",
    "\n",
    "    :returns: The current epsilon.\n",
    "    \"\"\"\n",
    "\n",
    "    # TODO: Your code here\n",
    "    ### BEGIN SOLUTION\n",
    "    ratio = min(1.0, current_timestep / duration)\n",
    "    return (eps_start - eps_end) * (1 - ratio) + eps_end\n",
    "    ### END SOLUTION\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {
    "nbgrader": {
     "grade": true,
     "grade_id": "cell-0129c9192c53e1bc",
     "locked": true,
     "points": 1.5,
     "schema_version": 3,
     "solution": false,
     "task": false
    }
   },
   "outputs": [],
   "source": [
    "import matplotlib.pyplot as plt\n",
    "\n",
    "eps_start = 1.0\n",
    "eps_end = 0.2\n",
    "schedule_duration = 1000\n",
    "\n",
    "eps_values = [linear_epsilon_decay(eps_start, eps_end, t, 600) for t in range(schedule_duration)]\n",
    "\n",
    "plt.plot(range(schedule_duration), eps_values)\n",
    "plt.xlabel('Time Step')\n",
    "plt.ylabel('Epsilon')\n",
    "plt.title('Linear Epsilon Decay')\n",
    "plt.show()\n",
    "### BEGIN HIDDEN TESTS\n",
    "assert eps_values[0] == eps_start, \"Expected eps_values[0] to be eps_start\"\n",
    "assert eps_values[-1] == eps_end, \"Expected eps_values[-1] to be eps_end\"\n",
    "assert len(eps_values) == schedule_duration, \"Expected eps_values to have length schedule_duration\"\n",
    "assert np.abs(eps_values[300] - 0.6) < 1e-10, \"Expected eps_values[600] to be 0.6\"\n",
    "assert eps_values[600] == 0.2, \"Expected eps_values[600] to be 0.6\"\n",
    "### END HIDDEN TESTS\n"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {
    "nbgrader": {
     "grade": false,
     "grade_id": "cell-a2d6542500aadffa",
     "locked": true,
     "schema_version": 3,
     "solution": false,
     "task": false
    }
   },
   "source": [
    "## 1.2 Target Network and Replay Buffer\n",
    "As described before, the main idea behind DQN is simple, we just minimize the MSE between the TD-target and the current estimate using the transitions we sampled. However, there are two problems that make the method very unstable:\n",
    "\n",
    "1. **Non-stationary target**: The TD-target uses an estimate from our Q-network. Unlike supervised learning, this target is not fixed, and whenever we update our network parameters, the target changes as well.\n",
    "2. Sampled transitions are **correlated** (each transition depends on the last transition if both are from the same episode). Samples are not independent.\n",
    "\n",
    "DQNs addresses both problems by using\n",
    "\n",
    "1. **Target networks:**\n",
    "An older set of network parameters is stored to compute the TD target, so they change less frequently and this improves stability. We call this network the target network. Its parameters are updated every few iterations.\n",
    "2. **Experience Replay:**\n",
    "A buffer where all transitions are stored and randomly sampled to make the data distribution more stationary. The buffer has a fixed size and new samples overwrite old ones.\n",
    "\n",
    "First we look at the target network:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {
    "nbgrader": {
     "grade": false,
     "grade_id": "cell-f848f9de7481eee5",
     "locked": true,
     "schema_version": 3,
     "solution": false,
     "task": false
    }
   },
   "outputs": [],
   "source": [
    "test_input = torch.tensor([1, 2, 3, 4], dtype=torch.float32)\n",
    "\n",
    "# Given a neural network\n",
    "net = nn.Sequential(\n",
    "    nn.Linear(4, 3),\n",
    "    nn.ReLU(), \n",
    "    nn.Linear(3, 1)\n",
    ")\n",
    "print(f\"Prediction (Before): {net(test_input)}\\n\")\n",
    "\n",
    "# We can get its parameters with .state_dict(). A dictionary containing all the parameters.\n",
    "# Note: It contains even more than parameters, but that is not relevant for us.\n",
    "params = copy.deepcopy(net.state_dict())\n",
    "\n",
    "print(\"Parameters:\")\n",
    "for key, value in params.items():\n",
    "    print(f\"- Parameter {key}:\\n{value}\")\n",
    "\n",
    "# Set weight matrix of first layer to zero\n",
    "net[0].weight.data.fill_(0.0)\n",
    "print(f\"\\nPrediction (After change): {net(test_input)}\\n\")\n",
    "\n",
    "# Load the old parameters\n",
    "net.load_state_dict(params)\n",
    "print(f\"Prediction (After reload): {net(test_input)}\\n\")\n"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {
    "nbgrader": {
     "grade": false,
     "grade_id": "cell-8b52826232517bbf",
     "locked": true,
     "schema_version": 3,
     "solution": false,
     "task": false
    }
   },
   "source": [
    "So we can save and load old parameters of our network using ``.state_dict()`` and ``.load_state_dict(..)`` respectively.\n",
    "\n",
    "---\n",
    "<span style=\"color:orange\">**Replay Buffer**</span>\n",
    "\n",
    "The replay buffer stores transitions of the form $(s, a, r, s')$ with $s$ as the current state, the action $a$, the reward $r$, and the next state $s'$. The buffer can perform two operations:\n",
    "- **store**: During sampling we observe transitions and store them with ``buffer.store(...)``. However, the buffer only has a fixed size\n",
    "(as we cannot store an infinte amount of data). When reaching it, the oldest samples are overwritten first.\n",
    "- **sample**: For training, we want to sample a batch of transitions from our buffer via ``buffer.sample(...)``. The transitions are sampled uniformly and with replacement i.e. the same transition can be sampled more than once.\n",
    "\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 9,
   "metadata": {
    "nbgrader": {
     "grade": true,
     "grade_id": "cell-e9eeb3fa39ba4c44",
     "locked": false,
     "points": 4,
     "schema_version": 3,
     "solution": true,
     "task": false
    }
   },
   "outputs": [],
   "source": [
    "class ReplayBuffer:\n",
    "    def __init__(self, max_size: int):\n",
    "        \"\"\"\n",
    "        Create the replay buffer.\n",
    "\n",
    "        :param max_size: Maximum number of transitions in the buffer.\n",
    "        \"\"\"\n",
    "        self.data = []\n",
    "        self.max_size = max_size\n",
    "        self.position = 0\n",
    "\n",
    "    def __len__(self) -> int:\n",
    "        \"\"\"Returns how many transitions are currently in the buffer.\"\"\"\n",
    "        # TODO: Your code here\n",
    "        ### BEGIN SOLUTION\n",
    "        return len(self.data)\n",
    "        ### END SOLUTION\n",
    "\n",
    "    def store(self, obs: torch.Tensor, action: torch.Tensor, reward: torch.Tensor, next_obs: torch.Tensor, terminated: torch.Tensor):\n",
    "        \"\"\"\n",
    "        Adds a new transition to the buffer. When the buffer is full, overwrite the oldest transition.\n",
    "\n",
    "        :param obs: The current observation.\n",
    "        :param action: The action.\n",
    "        :param reward: The reward.\n",
    "        :param next_obs: The next observation.\n",
    "        :param terminated: Whether the episode terminated.\n",
    "        \"\"\"\n",
    "        # TODO: Your code here\n",
    "        ### BEGIN SOLUTION\n",
    "        if len(self.data) < self.max_size:\n",
    "            self.data.append((obs, action, reward, next_obs, terminated))\n",
    "        else:\n",
    "            self.data[self.position] = (obs, action, reward, next_obs, terminated)   \n",
    "        self.position = (self.position + 1) % self.max_size   \n",
    "        ### END SOLUTION      \n",
    "\n",
    "    def sample(self, batch_size: int) -> torch.Tensor:\n",
    "        \"\"\"\n",
    "        Sample a batch of transitions uniformly and with replacement. The respective elements e.g. states, actions, rewards etc. are stacked\n",
    "\n",
    "        :param batch_size: The batch size.\n",
    "        :returns: A tuple of tensors (obs_batch, action_batch, reward_batch, next_obs_batch, terminated_batch), where each tensors is stacked.\n",
    "        \"\"\"\n",
    "        # TODO: Your code here\n",
    "        ### BEGIN SOLUTION\n",
    "        return [torch.stack(b) for b in zip(*random.choices(self.data, k=batch_size))]\n",
    "        ### END SOLUTION"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {
    "nbgrader": {
     "grade": false,
     "grade_id": "cell-c93921fe09c62bb1",
     "locked": true,
     "schema_version": 3,
     "solution": false,
     "task": false
    }
   },
   "source": [
    "## 1.3 Algorithm\n",
    "In this section, we will first look at the update of the DQN and then implement the entire algorithm.\n",
    "\n",
    "---\n",
    "<span style=\"color:orange\">**DQN Update**</span>\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 10,
   "metadata": {
    "nbgrader": {
     "grade": true,
     "grade_id": "cell-581cb139fd50e0f1",
     "locked": false,
     "points": 3,
     "schema_version": 3,
     "solution": true,
     "task": false
    }
   },
   "outputs": [],
   "source": [
    "def update_dqn(\n",
    "        q: nn.Module,\n",
    "        q_target: nn.Module,\n",
    "        optimizer: optim.Optimizer,\n",
    "        gamma: float,\n",
    "        obs: torch.Tensor,\n",
    "        act: torch.Tensor,\n",
    "        rew: torch.Tensor,\n",
    "        next_obs: torch.Tensor,\n",
    "        tm: torch.Tensor,\n",
    "    ):\n",
    "    \"\"\"\n",
    "    Update the DQN network for one optimizer step.\n",
    "\n",
    "    :param q: The DQN network.\n",
    "    :param q_target: The target DQN network.\n",
    "    :param optimizer: The optimizer.\n",
    "    :param gamma: The discount factor.\n",
    "    :param obs: Batch of current observations.\n",
    "    :param act: Batch of actions.\n",
    "    :param rew: Batch of rewards.\n",
    "    :param next_obs: Batch of next observations.\n",
    "    :param tm: Batch of termination flags.\n",
    "\n",
    "    \"\"\"\n",
    "    # TODO: Zero out the gradient\n",
    "    ### BEGIN SOLUTION\n",
    "    optimizer.zero_grad()\n",
    "    ### END SOLUTION\n",
    "\n",
    "    # TODO: Calculate the TD-Target\n",
    "    with torch.no_grad():\n",
    "        ### BEGIN SOLUTION\n",
    "        td_target = rew + gamma * q_target(next_obs).max(dim=1)[0] * (1 - tm.float())\n",
    "        ### END SOLUTION\n",
    "\n",
    "    # TODO: Calculate the loss. Hint: Pytorch has the \".gather()\" function, which collects values along a specified axis using some specified indexes\n",
    "    ### BEGIN SOLUTION\n",
    "    loss = F.mse_loss(q(obs).gather(1, act.unsqueeze(1)), td_target.unsqueeze(1))\n",
    "    ### END SOLUTION\n",
    "\n",
    "    # TODO: Backpropagate the loss and step the optimizer\n",
    "    ### BEGIN SOLUTION\n",
    "    loss.backward()\n",
    "    optimizer.step()\n",
    "    ### END SOLUTION\n"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {
    "nbgrader": {
     "grade": false,
     "grade_id": "cell-cf10276597ca39e3",
     "locked": true,
     "schema_version": 3,
     "solution": false,
     "task": false
    }
   },
   "source": [
    "We are now putting it all together. This implementation is very similar to the Q-learning one. Note that we have not specified an environment yet! Our algorithm remains relatively flexible.\n",
    "\n",
    "---\n",
    "<span style=\"color:orange\">**DQN Agent**</span>\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 11,
   "metadata": {
    "nbgrader": {
     "grade": true,
     "grade_id": "cell-ea9e6a4c5d20b294",
     "locked": false,
     "points": 3.5,
     "schema_version": 3,
     "solution": true,
     "task": false
    }
   },
   "outputs": [],
   "source": [
    "EpisodeStats = namedtuple(\"Stats\", [\"episode_lengths\", \"episode_rewards\"])\n",
    "\n",
    "\n",
    "class DQNAgent:\n",
    "    def __init__(self,\n",
    "            env,\n",
    "            gamma=0.99,\n",
    "            lr=0.001, \n",
    "            batch_size=64,\n",
    "            eps_start=1.0,\n",
    "            eps_end=0.1,\n",
    "            schedule_duration=10_000,\n",
    "            update_freq=100,\n",
    "            maxlen=100_000,\n",
    "        ):\n",
    "        \"\"\"\n",
    "        Initialize the DQN agent.\n",
    "\n",
    "        :param env: The environment.\n",
    "        :param gamma: The discount factor.\n",
    "        :param lr: The learning rate.\n",
    "        :param batch_size: Mini batch size.\n",
    "        :param eps_start: The initial epsilon value.\n",
    "        :param eps_end: The final epsilon value.\n",
    "        :param schedule_duration: The duration of the schedule (in timesteps).\n",
    "        :param update_freq: How often to update the Q target.\n",
    "        :param max_size: Maximum number of transitions in the buffer.\n",
    "        \"\"\"\n",
    "\n",
    "        self.env = env\n",
    "        self.gamma = gamma\n",
    "        self.batch_size = batch_size\n",
    "        self.eps_start = eps_start\n",
    "        self.eps_end = eps_end\n",
    "        self.schedule_duration = schedule_duration\n",
    "        self.update_freq = update_freq\n",
    "\n",
    "        # TODO: Initialize the Replay Buffer\n",
    "        ### BEGIN SOLUTION\n",
    "        self.buffer = ReplayBuffer(maxlen)\n",
    "        ### END SOLUTION\n",
    "\n",
    "        # TODO: Initialize the Deep Q-Network. Hint: Remember observation_space and action_space\n",
    "        ### BEGIN SOLUTION\n",
    "        self.q = DQN(env.observation_space.shape, env.action_space.n)\n",
    "        ### END SOLUTION\n",
    "\n",
    "        # TODO: Initialize the second Q-Network, the target network. Load the parameters of the first one into the second\n",
    "        ### BEGIN SOLUTION\n",
    "        self.q_target = DQN(env.observation_space.shape, env.action_space.n)\n",
    "        self.q_target.load_state_dict(self.q.state_dict())\n",
    "        ### END SOLUTION\n",
    "\n",
    "        # TODO: Create an ADAM optimizer for the Q-network\n",
    "        ### BEGIN SOLUTION\n",
    "        self.optimizer = optim.Adam(self.q.parameters(), lr=lr)\n",
    "        ### END SOLUTION\n",
    "\n",
    "        self.policy = make_epsilon_greedy_policy(self.q, env.action_space.n)\n",
    "\n",
    "\n",
    "    def train(self, num_episodes: int) -> EpisodeStats:\n",
    "        \"\"\"\n",
    "        Train the DQN agent.\n",
    "\n",
    "        :param num_episodes: Number of episodes to train.\n",
    "        :returns: The episode statistics.\n",
    "        \"\"\"\n",
    "        # Keeps track of useful statistics\n",
    "        stats = EpisodeStats(\n",
    "            episode_lengths=np.zeros(num_episodes),\n",
    "            episode_rewards=np.zeros(num_episodes),\n",
    "        )\n",
    "        current_timestep = 0\n",
    "        epsilon = self.eps_start\n",
    "\n",
    "        for i_episode in range(num_episodes):\n",
    "            # Print out which episode we're on, useful for debugging.\n",
    "            if (i_episode + 1) % 100 == 0:\n",
    "                print(f'Episode {i_episode + 1} of {num_episodes}  Time Step: {current_timestep}  Epsilon: {epsilon:.3f}')\n",
    "\n",
    "            # Reset the environment and get initial observation\n",
    "            obs, _ = self.env.reset()\n",
    "            \n",
    "            for episode_time in itertools.count():\n",
    "                # TODO: Get current epsilon value\n",
    "                ### BEGIN SOLUTION\n",
    "                epsilon = linear_epsilon_decay(self.eps_start, self.eps_end, current_timestep, self.schedule_duration)\n",
    "                ### END SOLUTION\n",
    "\n",
    "                # Choose action and execute\n",
    "                action = self.policy(torch.as_tensor(obs).unsqueeze(0).float(), epsilon=epsilon)\n",
    "                next_obs, reward, terminated, truncated, _ = self.env.step(action)\n",
    "\n",
    "                # Update statistics\n",
    "                stats.episode_rewards[i_episode] += reward\n",
    "                stats.episode_lengths[i_episode] += 1\n",
    "\n",
    "                # TODO: Store sample in the replay buffer\n",
    "                ### BEGIN SOLUTION\n",
    "                self.buffer.store(\n",
    "                    torch.as_tensor(obs, dtype=torch.float32),\n",
    "                    torch.as_tensor(action),\n",
    "                    torch.as_tensor(reward, dtype=torch.float32),\n",
    "                    torch.as_tensor(next_obs, dtype=torch.float32),\n",
    "                    torch.as_tensor(terminated)\n",
    "                )\n",
    "                ### END SOLUTION\n",
    "\n",
    "                # TODO: Sample a mini batch from the replay buffer\n",
    "                ### BEGIN SOLUTION\n",
    "                obs_batch, act_batch, rew_batch, next_obs_batch, tm_batch = self.buffer.sample(self.batch_size)\n",
    "                ### END SOLUTION\n",
    "                \n",
    "                # Update the Q network\n",
    "                update_dqn(\n",
    "                    self.q,\n",
    "                    self.q_target,\n",
    "                    self.optimizer,\n",
    "                    self.gamma, \n",
    "                    obs_batch.float(),\n",
    "                    act_batch, \n",
    "                    rew_batch.float(),\n",
    "                    next_obs_batch.float(),\n",
    "                    tm_batch\n",
    "                )\n",
    "\n",
    "                # Update the current Q target\n",
    "                if current_timestep % self.update_freq == 0:\n",
    "                    self.q_target.load_state_dict(self.q.state_dict())\n",
    "                current_timestep += 1\n",
    "\n",
    "                # Check whether the episode is finished\n",
    "                if terminated or truncated or episode_time >= 500:\n",
    "                    break\n",
    "                obs = next_obs\n",
    "        return stats"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {
    "nbgrader": {
     "grade": false,
     "grade_id": "cell-b4beb2ffa5f81b01",
     "locked": true,
     "schema_version": 3,
     "solution": false,
     "task": false
    }
   },
   "source": [
    "## 1.4 Training\n",
    "Now, we want to run our algorithm on a task in [MinAtar](https://github.com/kenjyoung/MinAtar). You are free to choose any environment you like, however, we recommend Breakout-v1 as the other environments may need different hyperparameters and more training time. The following game ID's are available: SpaceInvaders-v1, Breakout-v1, Seaquest-v1, Asterix-v1 and Freeway-v1.\n",
    "Note, that the training can take several minutes."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {
    "nbgrader": {
     "grade": false,
     "grade_id": "cell-a177045dee6d0c56",
     "locked": true,
     "schema_version": 3,
     "solution": false,
     "task": false
    }
   },
   "outputs": [],
   "source": [
    "# Choose your environment\n",
    "env = gym.make('MinAtar/Breakout-v1', render_mode=\"rgb_array\")\n",
    "\n",
    "# Print observation and action space infos\n",
    "print(f\"Training on {env.spec.id}\")\n",
    "print(f\"Observation space: {env.observation_space}\")\n",
    "print(f\"Action space: {env.action_space}\\n\")\n",
    "\n",
    "# Hyperparameters, Hint: Change as you see fit\n",
    "LR = 0.001\n",
    "BATCH_SIZE = 8\n",
    "REPLAY_BUFFER_SIZE = 100_000\n",
    "UPDATE_FREQ = 100\n",
    "EPS_START = 0.5\n",
    "EPS_END = 0.05\n",
    "SCHEDULE_DURATION = 15_000\n",
    "NUM_EPISODES = 1_000\n",
    "DISCOUNT_FACTOR = 0.99\n",
    "\n",
    "# Train DQN\n",
    "agent = DQNAgent(\n",
    "    env, \n",
    "    gamma=DISCOUNT_FACTOR,\n",
    "    lr=LR,\n",
    "    batch_size=BATCH_SIZE,\n",
    "    eps_start=EPS_START,\n",
    "    eps_end=EPS_END,\n",
    "    schedule_duration=SCHEDULE_DURATION,\n",
    "    update_freq=UPDATE_FREQ,\n",
    "    maxlen=REPLAY_BUFFER_SIZE,\n",
    ")\n",
    "stats = agent.train(NUM_EPISODES)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {
    "nbgrader": {
     "grade": false,
     "grade_id": "cell-93e358e0c1874f78",
     "locked": true,
     "schema_version": 3,
     "solution": false,
     "task": false
    }
   },
   "source": [
    "# 1.5 Results\n",
    "\n",
    "Like in the last exercise, we will look at the resulting episode reward."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {
    "nbgrader": {
     "grade": false,
     "grade_id": "cell-c4ea19ae05671a23",
     "locked": true,
     "schema_version": 3,
     "solution": false,
     "task": false
    }
   },
   "outputs": [],
   "source": [
    "smoothing_window=20\n",
    "fig, axes = plt.subplots(1, 2, figsize=(10, 5), tight_layout=True)\n",
    "\n",
    "# Plot the episode length over time\n",
    "ax = axes[0]\n",
    "ax.plot(stats.episode_lengths)\n",
    "ax.set_xlabel(\"Episode\")\n",
    "ax.set_ylabel(\"Episode Length\")\n",
    "ax.set_title(\"Episode Length over Time\") \n",
    "\n",
    "# Plot the episode reward over time\n",
    "ax = axes[1]\n",
    "rewards_smoothed = pd.Series(stats.episode_rewards).rolling(smoothing_window, min_periods=smoothing_window).mean()\n",
    "ax.plot(rewards_smoothed)\n",
    "ax.set_xlabel(\"Episode\")\n",
    "ax.set_ylabel(\"Episode Reward (Smoothed)\")\n",
    "ax.set_title(f\"Episode Reward over Time\\n(Smoothed over window size {smoothing_window})\")\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {
    "nbgrader": {
     "grade": false,
     "grade_id": "cell-8ba78bd035a21bc1",
     "locked": true,
     "schema_version": 3,
     "solution": false,
     "task": false
    }
   },
   "source": [
    "Lastly, let us see what the learned policy does in action."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {
    "nbgrader": {
     "grade": false,
     "grade_id": "cell-dbcfd10b74c6d50e",
     "locked": true,
     "schema_version": 3,
     "solution": false,
     "task": false
    }
   },
   "outputs": [],
   "source": [
    "from IPython.display import Image as IImage\n",
    "\n",
    "def save_rgb_animation(rgb_arrays, filename, duration=50):\n",
    "    \"\"\"Save an animated GIF from a list of RGB arrays.\"\"\"\n",
    "    # Create a list to hold each frame\n",
    "    frames = []\n",
    "\n",
    "    # Convert RGB arrays to PIL Image objects\n",
    "    for rgb_array in rgb_arrays:\n",
    "        rgb_array = (rgb_array*255).astype(np.uint8)\n",
    "        rgb_array = rgb_array.repeat(48, axis=0).repeat(48, axis=1)\n",
    "        img = Image.fromarray(rgb_array)\n",
    "        frames.append(img)\n",
    "\n",
    "    # Save the frames as an animated GIF\n",
    "    frames[0].save(filename, save_all=True, append_images=frames[1:], duration=duration, loop=0)\n",
    "\n",
    "def rendered_rollout(policy, env, max_steps=1_000):\n",
    "    \"\"\"Rollout for one episode while saving all rendered images.\"\"\"\n",
    "    obs, _ = env.reset()\n",
    "    imgs = [env.render()]\n",
    "\n",
    "    for _ in range(max_steps):\n",
    "        action = policy(torch.as_tensor(obs, dtype=torch.float32).unsqueeze(0))\n",
    "        obs, _, terminated, truncated, _ = env.step(action)\n",
    "        imgs.append(env.render())\n",
    "        \n",
    "        if terminated or truncated:\n",
    "            break\n",
    "\n",
    "    return imgs\n",
    "\n",
    "policy = make_epsilon_greedy_policy(agent.q, num_actions=env.action_space.n)\n",
    "imgs = rendered_rollout(policy, env)\n",
    "save_rgb_animation(imgs, \"trained.gif\")\n",
    "IImage(filename=\"trained.gif\")"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3 (ipykernel)",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.11.3"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
