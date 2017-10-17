from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt


map = Basemap(projection='cyl')
map.fillcontinents(color = 'grey')

plt.show()

