import pandas as pd

DATE = '31Mar18'
DATE = '17May17'
folder = DATE +'/'
def change_dwelling_time(file = folder + 'bus_journeytime_31Mar18.csv'):
    df = pd.read_csv(file)
    df['departure_time'] = df['arrival_time']
    df.to_csv(file, index=False)
# change_dwelling_time()

def test_bus():
    bus_dispatch = pd.read_csv(DATE + '/bus_journeytime_' +  DATE + '.csv')
    bus_stops = pd.read_csv(DATE + '/SimM_bus_stops_' +  DATE + '.csv')
    print('bus stops----------------------------')
    # print(bus_stops.columns)
    print('Number of bus stops ', len(bus_stops.stop_id.unique()))
    print('Bus stop CRS ', bus_stops[['stop_lat', 'stop_lon']].head(2))
    print('Bus dispatch-------------------------')
    print('Number of bus stops in dispatch' , len(bus_dispatch.stop_id.unique()))
    print('Number of trip id ', len(bus_dispatch.trip_id.unique()))
    print('Number of service id ', len(bus_dispatch.service_id.unique()))
    # print(bus_dispatch.columns)

test_bus()
def test_train():
    train_dispatch = pd.read_csv(DATE + '/weekday_train_seq_' +  DATE + '.csv')
    train_stops = pd.read_csv(DATE + '/SimM_RTS_stops_' +  DATE + '.csv')
    print(train_dispatch.columns)
    print(train_stops.columns)
