### From Data to MultiLevelIPF
1. Get aggregate data (Baltimore_affs)
  remove Estimate male, female (B010001)
2. run prepareHH

3. Get sample data
4. prepareIND

5. MultiLevelIPF (run for each county with all samples):
  run compute_all.R
  input
    household totals for each county
    samples (all together)
  output:
    weights for each county

6. Generate population for each county
  generate_pop.py

Check some statistics:
  statistics_original.py for original cities
  statistics.py for synthesized cities


### From sample weights (MultiLevelIPF output) to population tables.
From land use prepare SAL address points with population size based on county populations.
For each county, shuffle address points and assign households.
1. localize_population.py

Prepare simmobility category tables. Scripts in /Autosprawl_syn_population.
