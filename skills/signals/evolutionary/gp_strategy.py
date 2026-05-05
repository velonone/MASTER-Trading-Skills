"""
Genetic Programming Alpha Evolution
====================================
Evolves trading rule expression trees where fitness is risk-adjusted
return (Sharpe ratio). Uses DEAP framework.

Reference: Koza (1992); Chen & Navet (2007)
"""

from typing import Callable, List

import numpy as np


class GeneticProgrammingAlpha:
    """Skeleton for GP-derived strategy discovery."""

    name = "genetic_programming_alpha"
    description = "Evolves trading rules via genetic programming"
    version = "1.0.0"

    def __init__(self, population_size: int = 300, generations: int = 50, seed: int = 42):
        self.population_size = population_size
        self.generations = generations
        self.seed = seed

    def evolve(
        self,
        data: np.ndarray,
        feature_names: List[str],
        fitness_fn: Callable | None = None,
    ) -> dict:
        """
        Args:
            data: Array of shape (n_samples, n_features + 1) where last column is forward return.
            feature_names: Names for each feature column.
            fitness_fn: Optional custom fitness callable.

        Returns:
            Dict with best_individual, sharpe, and expression string.
        """
        try:
            from deap import base, creator, tools, algorithms, gp
        except ImportError as exc:
            raise ImportError("Install DEAP: pip install deap") from exc

        np.random.seed(self.seed)

        n_features = len(feature_names)
        pset = gp.PrimitiveSet("MAIN", n_features)
        pset.addPrimitive(np.add, 2)
        pset.addPrimitive(np.subtract, 2)
        pset.addPrimitive(np.multiply, 2)
        pset.addPrimitive(lambda x: np.divide(x, np.abs(x) + 1e-10), 1, name="safe_inv")
        pset.addPrimitive(np.tanh, 1)
        pset.addPrimitive(np.maximum, 2, name="max2")
        pset.addPrimitive(np.minimum, 2, name="min2")
        pset.addEphemeralConstant("rand", lambda: np.random.uniform(-1, 1))
        pset.renameArguments(**{f"ARG{i}": name for i, name in enumerate(feature_names)})

        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax)

        toolbox = base.Toolbox()
        toolbox.register("expr", gp.genHalfAndHalf, pset=pset, min_=1, max_=3)
        toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        toolbox.register("compile", gp.compile, pset=pset)

        def _sharpe_fitness(individual):
            func = toolbox.compile(expr=individual)
            signals = np.array([func(*row[:-1]) for row in data])
            positions = np.sign(signals)
            returns = positions[:-1] * data[1:, -1]
            if np.std(returns) < 1e-10:
                return (-100.0,)
            sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252)
            return (max(sharpe, -100.0),)

        toolbox.register("evaluate", fitness_fn if fitness_fn else _sharpe_fitness)
        toolbox.register("select", tools.selTournament, tournsize=3)
        toolbox.register("mate", gp.cxOnePoint)
        toolbox.register("expr_mut", gp.genFull, min_=0, max_=2)
        toolbox.register("mutate", gp.mutUniform, expr=toolbox.expr_mut, pset=pset)

        pop = toolbox.population(n=self.population_size)
        hof = tools.HallOfFame(1)

        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean)
        stats.register("max", np.max)

        algorithms.eaSimple(
            pop, toolbox, cxpb=0.5, mutpb=0.2, ngen=self.generations,
            stats=stats, halloffame=hof, verbose=False,
        )

        best = hof[0]
        best_sharpe = _sharpe_fitness(best)[0]

        return {
            "best_sharpe": round(float(best_sharpe), 4),
            "best_expression": str(best),
            "population_size": self.population_size,
            "generations": self.generations,
            "compiled_function": toolbox.compile(expr=best),
        }
