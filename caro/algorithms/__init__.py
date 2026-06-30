from algorithms.caro_adversarial import (
    alpha_beta_search,
    expectimax_search,
    minimax_search,
)


ALGORITHMS = {
    "MINIMAX": minimax_search,
    "ALPHA_BETA": alpha_beta_search,
    "EXPECTIMAX": expectimax_search,
}
