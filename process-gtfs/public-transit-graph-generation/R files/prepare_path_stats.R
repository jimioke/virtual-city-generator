# Prepare_pathstats.R
#------update mainDir, folderDir, date for a different version
mainDir<-"~/" #"C:/Users/Rui/Documents/"
datafolderDir<-"SimMobility Demo/"
RfolderDir<-"SimMobility Demo/R files/"
date<-"07Apr15"

simPT_Pathset<-fread(str_c(mainDir, datafolderDir, "simPT_Pathset.csv"), header=TRUE, sep=",")
OD<-fread(str_c(mainDir, datafolderDir, "sampleOD_21Mar15.csv"), header=TRUE)

simPT_Pathset[TotalDistanceKms<=3.2, TotalCost:=0.77]
simPT_Pathset[TotalDistanceKms>3.2 & TotalDistanceKms<=4.2, TotalCost:=0.87]
simPT_Pathset[TotalDistanceKms>4.2 & TotalDistanceKms<=5.2, TotalCost:=0.98]
simPT_Pathset[TotalDistanceKms>5.2 & TotalDistanceKms<=6.2, TotalCost:=1.08]
simPT_Pathset[TotalDistanceKms>6.2 & TotalDistanceKms<=7.2, TotalCost:=1.16]
simPT_Pathset[TotalDistanceKms>7.2 & TotalDistanceKms<=8.2, TotalCost:=1.23]
simPT_Pathset[TotalDistanceKms>8.2 & TotalDistanceKms<=9.2, TotalCost:=1.29]
simPT_Pathset[TotalDistanceKms>9.2 & TotalDistanceKms<=10.2, TotalCost:=1.33]
simPT_Pathset[TotalDistanceKms>10.2 & TotalDistanceKms<=11.2, TotalCost:=1.37]
simPT_Pathset[TotalDistanceKms>11.2 & TotalDistanceKms<=12.2, TotalCost:=1.41]
simPT_Pathset[TotalDistanceKms>12.2 & TotalDistanceKms<=13.2, TotalCost:=1.45]
simPT_Pathset[TotalDistanceKms>13.2 & TotalDistanceKms<=14.2, TotalCost:=1.49]
simPT_Pathset[TotalDistanceKms>14.2 & TotalDistanceKms<=15.2, TotalCost:=1.53]
simPT_Pathset[TotalDistanceKms>15.2 & TotalDistanceKms<=16.2, TotalCost:=1.57]
simPT_Pathset[TotalDistanceKms>16.2 & TotalDistanceKms<=17.2, TotalCost:=1.61]
simPT_Pathset[TotalDistanceKms>17.2 & TotalDistanceKms<=18.2, TotalCost:=1.65]
simPT_Pathset[TotalDistanceKms>18.2 & TotalDistanceKms<=19.2, TotalCost:=1.69]
simPT_Pathset[TotalDistanceKms>19.2 & TotalDistanceKms<=20.2, TotalCost:=1.72]
simPT_Pathset[TotalDistanceKms>20.2 & TotalDistanceKms<=21.2, TotalCost:=1.75]
simPT_Pathset[TotalDistanceKms>21.2 & TotalDistanceKms<=22.2, TotalCost:=1.78]
simPT_Pathset[TotalDistanceKms>22.2 & TotalDistanceKms<=23.2, TotalCost:=1.81]
simPT_Pathset[TotalDistanceKms>23.2 & TotalDistanceKms<=24.2, TotalCost:=1.83]
simPT_Pathset[TotalDistanceKms>24.2 & TotalDistanceKms<=25.2, TotalCost:=1.85]
simPT_Pathset[TotalDistanceKms>25.2 & TotalDistanceKms<=26.2, TotalCost:=1.87]
simPT_Pathset[TotalDistanceKms>26.2 & TotalDistanceKms<=27.2, TotalCost:=1.88]
simPT_Pathset[TotalDistanceKms>27.2 & TotalDistanceKms<=28.2, TotalCost:=1.89]
simPT_Pathset[TotalDistanceKms>28.2 & TotalDistanceKms<=29.2, TotalCost:=1.90]
simPT_Pathset[TotalDistanceKms>29.2 & TotalDistanceKms<=30.2, TotalCost:=1.91]
simPT_Pathset[TotalDistanceKms>30.0 & TotalDistanceKms<=31.2, TotalCost:=1.92]
simPT_Pathset[TotalDistanceKms>31.2 & TotalDistanceKms<=32.2, TotalCost:=1.93]
simPT_Pathset[TotalDistanceKms>32.2 & TotalDistanceKms<=33.2, TotalCost:=1.94]
simPT_Pathset[TotalDistanceKms>33.2 & TotalDistanceKms<=34.2, TotalCost:=1.95]
simPT_Pathset[TotalDistanceKms>34.2 & TotalDistanceKms<=35.2, TotalCost:=1.96]
simPT_Pathset[TotalDistanceKms>35.2 & TotalDistanceKms<=36.2, TotalCost:=1.97]
simPT_Pathset[TotalDistanceKms>36.2 & TotalDistanceKms<=37.2, TotalCost:=1.98]
simPT_Pathset[TotalDistanceKms>37.2 & TotalDistanceKms<=38.2, TotalCost:=1.99]
simPT_Pathset[TotalDistanceKms>38.2 & TotalDistanceKms<=39.2, TotalCost:=2.00]
simPT_Pathset[TotalDistanceKms>39.2 & TotalDistanceKms<=40.2, TotalCost:=2.01]
simPT_Pathset[TotalDistanceKms>40.2, TotalCost:=2.02]


beta_in_vehicle = -0.35
beta_walk = -0.65
beta_wait = -0.46
beta_no_txf= -4.31
beta_cost = -0.16
beta_path_size = 0.8

param<-matrix(c(beta_in_vehicle,beta_walk,beta_wait, beta_no_txf, beta_cost,beta_path_size)
              ,ncol=1)

simPT_Pathset[,total_in_vehicle_time:=Total_In_Vehicle_Travel_Time_Secs/60]
simPT_Pathset[,total_walk_time:=Total_walking_time/60]
simPT_Pathset[,total_wait_time:=Total_waiting_time/60]
simPT_Pathset[, total_no_txf:=Total_Number_of_transfers]
simPT_Pathset[, total_path_size:=logb(PathSize)]
simPT_Pathset[, total_cost:=TotalCost]

attr_list<-c("total_in_vehicle_time"
            ,"total_walk_time"
            ,"total_wait_time"
            ,"total_no_txf"
            ,"total_path_size"
            ,"total_cost")

temp<-simPSlogit_V1(param,simPT_Pathset, attr_list)

write.csv(temp,str_c(mainDir, datafolderDir, "simPT_Pathset_withP.csv"), row.names=FALSE)
