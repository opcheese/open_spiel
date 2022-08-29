# Copyright 2019 DeepMind Technologies Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Example use of the C++ MCCFR algorithms on Kuhn Poker.

This examples calls the underlying C++ implementations via the Python bindings.
Note that there are some pure Python implementations of some of these algorithms
in python/algorithms as well.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import pickle
import random
import pyspiel
import open_spiel.python.games.ma_autobattler_tree_meta
from open_spiel.python.algorithms import external_sampling_mccfr_no_meta
from open_spiel.python.algorithms import exploitability
import os
import ray
from minio import Minio
runtime_env = {"pip": ["minio","python-dotenv"]}
ray.init(address="auto",runtime_env=runtime_env)

# FLAGS = flags.FLAGS

# flags.DEFINE_enum(
#     "sampling",
#     "external",
#     ["external", "outcome"],
#     "Sampling for the MCCFR solver",
# )
# flags.DEFINE_integer("iterations", 50, "Number of iterations")
# flags.DEFINE_string("game", "kuhn_poker", "Name of the game")
# flags.DEFINE_integer("players", 2, "Number of players")


itertaions = 10000
key_step = 500
path = "/tmp/"

def run_iterations(game, solver, start_iteration=0):
  """Run iterations of MCCFR."""
  for i in range(int(itertaions)):
    #print(i)
    solver.iteration()

    # if i%key_step == 0 and i!=0 :
    #   print("here")
    #   policy = solver.average_policy()
    #   print("here1")
    #   exploitability_val = 0
    #   #exploitability_val = exploitability.exploitability(game, policy)
    #   print("here2")

    # We also compute NashConv to highlight an important API feature:
    # when using Monte Carlo sampling, the policy
    # may not have a table entry for every info state.
    # Therefore, when calling nash_conv, ensure the third argument,
    # "use_state_get_policy" is set to True
    # See https://github.com/deepmind/open_spiel/issues/500
    # nash_conv = exploitability.nash_conv(game, policy, False,True)
    # print("here3")

    # print("Iteration {} nashconv: {:.6f} exploitability: {:.6f}".format(
    #     start_iteration + i, nash_conv, exploitability_val))

@ray.remote
def calcul(a, b):
    print(a, b)
    client = Minio(
        "91.206.15.133:9000",secure=False,
        access_key="spieluser",
        secret_key="qaz1QAZ!",
    )
    sampling = "external"

    game = open_spiel.python.games.ma_autobattler_tree_meta.MaAutobattlerGameTreeMeta()

    if sampling == "external":
      solver = external_sampling_mccfr_no_meta.ExternalSamplingSolverNoMeta(
          game,  range(a, b), external_sampling_mccfr_no_meta.AverageType.SIMPLE)
    elif sampling == "outcome":
      solver = pyspiel.OutcomeSamplingMCCFRSolver(game)

    run_iterations(game, solver)

    print("Persisting the model...")
    fileName = "tree_meta{}-{}".format(a,b)
    with open(path+fileName, "wb") as file:
      pickle.dump(solver, file, pickle.HIGHEST_PROTOCOL)   
    client.fput_object(
        "treemeta", fileName, path+ fileName,
    )


def main(_):
  client = Minio(
        "91.206.15.133:9000",secure=False,
        access_key="spieluser",
        secret_key="qaz1QAZ!",
    )
  found = client.bucket_exists("treemeta")
  if not found:
        client.make_bucket("treemeta")
  else:
        print("Bucket 'treemeta' already exists")
  
  pids = []
  old = 0

  ranges = [(3744,3888),(3888,4032),(4464,4608),(4752,4896),(4896,5040)]
  for rang in ranges:
    for i in range(rang[0],rang[1]):

      # rn_v = random.randint(0, 30)
      # if rn_v!=1:
      #   continue
      # if i%20==0:
      #   continue
      pid = calcul.remote(old,i)
      pids.append(pid)
      old = i
  ray.get(pids)

  


if __name__ == "__main__":
  main("1")
