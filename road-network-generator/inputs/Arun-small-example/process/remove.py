files = ["base_attr.csv","base_pl.csv","points.csv"]

for file in files:
    dummy = file.split(".")
    file2 = dummy[0] + "2." + dummy[1]
    with open(file,'r') as ifile:
        with open(file2,'w') as ofile:
            for aLine in ifile:
                aLine = aLine.replace('"','')
                ofile.write(aLine)
        