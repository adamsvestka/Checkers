from __future__ import annotations

import hide_pygame
from time import time
from multiprocessing import Pool
from multiprocessing.pool import AsyncResult

from guinea_pigs.Alfred import *
from guinea_pigs.Barbara import *
from guinea_pigs.Chuck import *
from checkers import *


def runTrial(p1, p2):
    game = Game(True)
    game.setPlayers(p1, p2, [[], []])

    while not game.victor:
        game.run()

    return game.players.index(game.victor)


if __name__ == "__main__":
    begin = time()

    p1, p2 = Chuck, Alfred

    # t = 0
    size = 100
    results = []
    with Pool(processes=size) as pool:
        hooks = [pool.apply_async(runTrial, (p2, p1)) for _ in range(size)]

        def getRes(res: AsyncResult):
            try:
                return res.get(timeout=1)
            except:
                return None
        results = [val for res in hooks if (val := getRes(res)) is not None]

    print(f"{100 * len(results) / size} % sucess, took {time() - begin} seconds")
    # print(results)
    print(sum(results) / len(results))
    print(f"{p1.__name__} beat {p2.__name__} {100 * sum(results) / len(results)} % of the time")
    # for i in range(10):
    #     print(time() - begin)
    #     t += runTrial(Alfred, Barbara)

    # print(t)
