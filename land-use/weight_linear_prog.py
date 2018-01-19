from pulp import *
import pandas as pd

county_pop = {
3: 323655,
5:  513941,
13: 95423,
25: 146580,
27: 177327,
35: 26988,
510: 457735
}

class var:
    def __init__(self, name, lowerbound, uppedbound):
        self.name = name
        self.low = lowerbound
        self.up = uppedbound
        self.assignment = None

col_list = [
var('agricul', 0, 10),
var('commer', 0, 10),
var('highR', 240, 600),
var('lowR', 6, 60),
var('mediumR', 60, 240),
var('sparseR', 0, 6),
]

county_lu_file = 'TAZ_LU_samples/county_lu_stats.csv'
outFolder = 'weights/'

# col_list = ['agricultur', 'commercial', 'hight_resi', 'low_reside', 'medium_res', 'sparse_res']
def pop_weight(county, inFile=county_lu_file, pop_var = col_list):

    prob = LpProblem("PopulationAllocation", LpMinimize)
    county_stat = pd.read_csv(inFile)
    county_stat.index = county_stat.COUNTYFP10

    # Variables
    V = {}
    for v in pop_var:
        V[v.name] = LpVariable(v.name, v.low, v.up)

    # Objective
    prob += county_stat.get_value(county, 'agricul') * V['agricul'] + county_stat.get_value(county, 'commer')  * V['commer'] + county_stat.get_value(county, 'highR') * V['highR'] + county_stat.get_value(county, 'lowR') * V['lowR'] + county_stat.get_value(county, 'mediumR') * V['mediumR'] + county_stat.get_value(county, 'sparseR') * V['sparseR']

    # Constraints
    prob += county_stat.get_value(county, 'agricul') * V['agricul'] + county_stat.get_value(county, 'commer')  * V['commer'] + county_stat.get_value(county, 'highR') * V['highR'] + county_stat.get_value(county, 'lowR') * V['lowR'] + county_stat.get_value(county, 'mediumR') * V['mediumR'] + county_stat.get_value(county, 'sparseR') * V['sparseR'] >= county_pop[county]

    GLPK().solve(prob)
    # Solution
    solution = {}
    for v in prob.variables():
        solution[v.name] = v.varValue
        print(v.name, "=", v.varValue)
    print('county: ', county, 'opt: ', value(prob.objective), ' error: ' , value(prob.objective)- county_pop[county])
    solution['county'] = county
    solution['optimized'] = value(prob.objective)
    solution['actual'] = county_pop[county]
    solution['error'] = value(prob.objective)- county_pop[county]
    return solution

def find_all_county_pop():
    solutions = []
    for c in county_pop.keys():
        solutions.append(pop_weight(c))
    df = pd.DataFrame(solutions)
    df.to_csv(outFolder+'population_allocation.csv')
find_all_county_pop()
