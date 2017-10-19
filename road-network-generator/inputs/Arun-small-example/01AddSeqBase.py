import sys, os
import pdb
#sys.path=os.getcwd()
infilename='Base_poly.csv'
outfilename='Base.csv'

def editline(curline, lastline):
   curline=curline.replace('"', "")
   curline=curline.replace("\n","")
   l1=curline.split(",")
   l1.insert(1,l1[0])
   l0=lastline.split(",")
   curline = ",".join(l1)
   #pdb.set_trace()
   if l0[0] == l1[0]:
      curline+=","+str(int(l0[4])+1)
   else:
      curline+=",1"
      
   return curline

def main():

   #open files
   infile=open(infilename,"r")
   outfile=open(outfilename, "w")
   outfile.write("shapeid,ID,x,y,seq\n")

   #first link
   #infile.readline()
   aline=infile.readline()
   line0=aline
   line0=line0.replace('"', "")
   line0=line0.replace("\n",",1")
   line0=line0.split(',')
   line0.insert(1,line0[0])
   line0 = ",".join(line0)
   print line0
   
   for aline in infile.readlines():
      newline=editline(aline,line0)
      line0=newline
      outfile.write(newline+"\n")

main()
