

a = ['04503', '04504']
for i in range(1, 38):
	if i < 10:
		a.append('0460'+str(i))
	else:
		a.append('046'+str(i))
a.extend(['04702','04801','04901','04902','04903','04904','04905'])
print a
print len(a)