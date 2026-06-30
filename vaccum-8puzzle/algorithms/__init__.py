from algorithms.bfs1 import search as bfs1
from algorithms.bfs2 import search as bfs2
from algorithms.dfs1 import search as dfs1
from algorithms.dfs2 import search as dfs2
from algorithms.ucs import search as ucs
from algorithms.greedy import search as greedy
from algorithms.astar import search as astar
from algorithms.ids import search as ids
from algorithms.idastar import search as idastar
from algorithms.hill_simple import search as hill_simple
from algorithms.hill_steepest import search as hill_steepest
from algorithms.hill_stochastic import search as hill_stochastic
from algorithms.hill_random_restart import search as hill_random_restart
from algorithms.local_beam import search as local_beam
from algorithms.simulated_annealing import search as simulated_annealing
from algorithms.and_or_graph_search import search as and_or_graph_search

ALGORITHMS = {
    "BFS1": bfs1,
    "BFS2": bfs2,
    "DFS1": dfs1,
    "DFS2": dfs2,
    "UCS": ucs,
    "GREEDY": greedy,
    "ASTAR": astar,
    "IDS": ids,
    "IDA*": idastar,
    "HILL_SIMPLE": hill_simple,
    "HILL_STEEPEST": hill_steepest,
    "HILL_STOCHASTIC": hill_stochastic,
    "HILL_RANDOM_RESTART": hill_random_restart,
    "LOCAL_BEAM": local_beam,
    "SIMULATED_ANNEALING": simulated_annealing,
    "AND_OR_GRAPH_SEARCH": and_or_graph_search,
}
