#-----------------------------------------------------------------
#   Author:         Rui Hong Lin                   Date: 9/18/2024
#   Class:          <CS 341>
#   Description:    
#-----------------------------------------------------------------

import sqlite3
import matplotlib.pyplot as figure

def display_stats(dbConn):
    dbCursor = dbConn.cursor()

    # Retrieve the number of stations
    dbCursor.execute("SELECT COUNT(*) FROM Stations")
    num_stations = dbCursor.fetchone()[0]

    # Retrieve the number of stops
    dbCursor.execute("SELECT COUNT(*) FROM Stops")
    num_stops = dbCursor.fetchone()[0]

    # Retrieve the number of ride entries
    dbCursor.execute("SELECT COUNT(*) FROM Ridership")
    num_ride_entries = dbCursor.fetchone()[0]

    # Retrieve the total ridership
    dbCursor.execute("SELECT SUM(Num_Riders) FROM Ridership")
    total_ridership = dbCursor.fetchone()[0]

    # Retrieve the date range
    dbCursor.execute("SELECT SUBSTRING(MIN(Ride_Date), 1, 10), SUBSTRING(MAX(Ride_Date), 1, 10) FROM Ridership")
    date_range = dbCursor.fetchone()

    # Output the results
    print("** Welcome to CTA L analysis app **")
    print()
    print("General Statistics:")
    print("  # of stations:", num_stations)
    print("  # of stops:", num_stops)
    print("  # of ride entries:", f"{num_ride_entries:,}")
    print("  date range:", date_range[0], "-", date_range[1])
    print("  Total ridership:", f"{total_ridership:,}")
    print()

# command_loop, continues until user inputs x
def command_loop(dbConn):
    while True:
        command = input("Please enter a command (1-9, x to exit): ")

        if command == 'x':
            break
        elif command == '1':
            print()
            name = input("Enter partial station name (wildcards _ and %): ")
            retrieve_stations(dbConn, name)
        elif command == '2':
            print()
            station_name = input("Enter the name of the station you would like to analyze: ")
            get_ridership_percentage(dbConn, station_name)
        elif command == '3':
            total_weekday_ridership(dbConn)
        elif command == '4':
            print()
            color = input("Enter a line color (e.g. Red or Yellow): ").lower()
            if line_exist(dbConn, color):
                direction = input("Enter a direction (N/S/W/E): ").upper()
                get_line(dbConn, color, direction)
        elif command == '5':
            get_num_stops(dbConn)
        elif command == '6':
            print()
            station_name = input("Enter a station name (wildcards _ and %): ")
            total_ridership_yearly(dbConn, station_name)
        elif command == '7':
            print()
            station_name = input("Enter a station name (wildcards _ and %): ")
            if station_exists(dbConn, station_name):
                year = input("Enter a year: ")
                monthly_ridership(dbConn, station_name, year)
        elif command == '8':
            print()
            year = input("Year to compare against? ")
            print()
            station1 = input("Enter station 1 (wildcards _ and %): ")
            if not station_exists(dbConn, station1):
                continue
            print()
            station2 = input("Enter station 2 (wildcards _ and %): ")
            if not station_exists(dbConn, station2):
                continue
            compareRidershipFor2Stations(dbConn, station1, station2, year)
        elif command == '9':
            print()
            latitude = input("Enter a latitude: ")
            if float(latitude) < 40 or float(latitude) > 43:
                print("**Latitude entered is out of bounds...")
                print()
                continue
            longitude = input("Enter a longitude: ")
            if float(longitude) > -87 or float(longitude) < -88:
                print("**Longitude entered is out of bounds...")
                print()
                continue
            nearestStations(dbConn, latitude, longitude)
        else:
            print("**Error, unknown command, try again...")

# command 1: retrieves all stations from a partial station name
def retrieve_stations(dbConn, name):
    sql = """
            SELECT Station_ID, Station_Name as s_name FROM Stations
            WHERE s_name LIKE ?
            ORDER BY s_name asc
    """
    dbCursor = dbConn.cursor()
    dbCursor.execute(sql, (name,))
    result = dbCursor.fetchall()

    if result:
        for station_id, station_name in result:
            print(station_id, ":", station_name)
    else:
        print("**No stations found...")
    
    print()

# command 2: gets the number of riders on each category of date (Weekday, Saturday, and Sunday/holiday)
def get_ridership_percentage(dbConn, station_name):
    dbCursor = dbConn.cursor()
    dbCursor.execute("SELECT Station_ID FROM Stations WHERE Station_Name  = ?", (station_name,))
    station_id = dbCursor.fetchone()

    if not station_id:
        print("**No data found...")
        return
    
    sql = """
            SELECT Type_of_Day, SUM(Num_Riders) as total FROM Ridership
            WHERE Station_ID = ?
            GROUP BY Type_of_Day
    """

    dbCursor.execute(sql, (station_id[0],))

    weekday_ridership = 0
    saturday_ridership = 0
    sunday_ridership = 0
    total_ridership = 0

    for row in dbCursor.fetchall():
        day_type, count = row
        if day_type == 'W':
            weekday_ridership = count
        elif day_type == 'A':
            saturday_ridership = count
        elif day_type == 'U':
            sunday_ridership = count
    
    total_ridership = weekday_ridership + saturday_ridership + sunday_ridership

    if total_ridership > 0:
        weekday_per = (weekday_ridership/total_ridership) * 100
        saturday_per = (saturday_ridership/total_ridership) * 100
        sunday_per = (sunday_ridership/total_ridership) * 100
    else:
        weekday_per = saturday_per = sunday_per = 0

    print("Percentage of ridership for the", station_name, "station: ")
    print("  Weekday ridership:", f"{weekday_ridership:,}", f"({weekday_per:.2f}%)")
    print("  Saturday ridership:", f"{saturday_ridership:,}", f"({saturday_per:.2f}%)")
    print("  Sunday/holiday ridership:", f"{sunday_ridership:,}", f"({sunday_per:.2f}%)")
    print("  Total ridership:", f"{total_ridership:,}")
    print()

# command 3: gets the total ridership of each station on weekdays
def total_weekday_ridership(dbConn):
    dbCursor = dbConn.cursor()
    sql = """
            SELECT Stations.Station_Name, SUM(Num_Riders) as total FROM Ridership
            JOIN Stations ON Ridership.Station_ID = Stations.Station_ID
            WHERE Ridership.Type_of_Day = 'W'
            GROUP BY Station_Name
            ORDER BY total desc;
    """
    dbCursor.execute(sql)
    results = dbCursor.fetchall()

    total_weekday_ridership = sum(row[1] for row in results)

    print("Ridership on Weekdays for Each Station")
    for station_name, total_ridership in results:
        percentage = (total_ridership/total_weekday_ridership) * 100
        print(f"{station_name} : {total_ridership:,} ({percentage:.2f}%)")

# command 4: check if line exists
def line_exist(dbConn, color):
    dbCursor = dbConn.cursor()
    dbCursor.execute("SELECT Line_ID FROM Lines WHERE LOWER(Color) = ?", (color,))
    line_info = dbCursor.fetchone()

    # check if line exists
    if line_info is None:
        print("**No such line...")
        return False
    
    return True

# command 4: outputs the details of stops in a user-given line that follow the user-given direction
def get_line(dbConn, color, direction):
    dbCursor = dbConn.cursor()
    
    sql = """
            SELECT Stops.Stop_Name, Stops.Direction, Stops.ADA FROM Stops
            JOIN StopDetails ON Stops.Stop_ID = StopDetails.Stop_ID
            JOIN Lines ON StopDetails.Line_ID = Lines.Line_ID
            WHERE LOWER(Lines.Color) = ? AND UPPER(Stops.Direction) = ?
            ORDER BY Stops.Stop_Name asc;
    """

    dbCursor.execute(sql, (color, direction,))
    stops = dbCursor.fetchall()

    if not stops:
        print("**That line does not run in the direction chosen...")
    else:
        # Output all stops for line color in chosen direction
        for stop in stops:
            stop_name = stop[0]
            stop_dir = stop[1]
            ada = "(handicap accessible)" if stop[2] else "(not handicap accessible)"
            print(f"{stop_name} : direction = {stop_dir} {ada}")

# command 5: outputs the number of stops for each line color, separated by direction, 
# ordered by color then direction
def get_num_stops(dbConn):
    dbCursor = dbConn.cursor()
    dbCursor.execute("SELECT COUNT(*) FROM Stops")
    total = dbCursor.fetchone()
   
    sql = """
            SELECT Color, Direction, COUNT(*) FROM Lines
            JOIN StopDetails ON Lines.Line_ID = StopDetails.Line_ID
            JOIN Stops ON StopDetails.Stop_ID = Stops.Stop_ID
            GROUP BY Color, Direction
            ORDER BY Color asc, Direction asc
    """
   
    dbCursor.execute(sql)
    rows = dbCursor.fetchall()
   
    print("Number of Stops For Each Color By Direction")
    for row in rows:
        print(row[0], "going", row[1], ":", row[2], f"({row[2] / total[0] * 100:.2f}%)")

# command 6: output the total ridership for each year for that station
# in ascending order
# show an error if the station name does not exist or if there are multiple
# station names that match
def total_ridership_yearly(dbConn, station_name):
    dbCursor = dbConn.cursor()
   
    sql1 = """
            SELECT COUNT(DISTINCT Station_Name) FROM Ridership
            JOIN Stations ON Ridership.Station_ID = Stations.Station_ID
            WHERE Station_Name LIKE ?
    """

    dbCursor.execute(sql1, (station_name,))
    totalStations = dbCursor.fetchall()
   
    if totalStations[0][0] > 1:
        print("**Multiple stations found...")
        return
   
    sql2 = """
            SELECT Station_Name, strftime('%Y', Ride_Date) as year, SUM(Num_Riders) FROM Ridership
            JOIN Stations ON Ridership.Station_ID = Stations.Station_ID
            WHERE Station_Name LIKE ?
            GROUP BY year
            ORDER BY year asc
    """

    dbCursor.execute(sql2, (station_name,))
    rows = dbCursor.fetchall()
   
    if not rows:
        print("**No station found...")
        return
    
    print("Yearly Ridership at", rows[0][0])
    for row in rows:
        print(row[1], ":", f"{row[2]:,}")
    
    print()
    #Prompts user if wants data ploted, if true proceeds to plot
    choice = input("Plot? (y/n) ")
   
    if(choice == 'y'):
        x = []
        y = []
       
        for row in rows:
            x.append(row[1])
            y.append(row[2])
           
        figure.xlabel("Year")
        figure.ylabel("Number of Riders")
        figure.title("Yearly Ridership at " + rows[0][0] + " Station")
        figure.ioff()
        figure.plot(x,y)
        figure.show()
       
    print()

# command 7: Checks if station exists or if there are multiple stations of the same name
def station_exists(dbConn, station_name):
    dbCursor = dbConn.cursor()
    sql = """
            SELECT COUNT(DISTINCT Station_Name) FROM Ridership
            JOIN Stations ON Stations.Station_ID = Ridership.Station_ID
            WHERE Station_Name LIKE ?
    """

    dbCursor.execute(sql, (station_name,))
    totalStations = dbCursor.fetchall()

    if totalStations[0][0] > 1:
        print("**Multiple stations found...\n")
        return False
    
    if totalStations[0][0] == 0:
        print("**No station found...\n")
        print()
        return False
    return True

# command 7: Outputs the monthly ridership at a user-given station name
# and on a user-given year
def monthly_ridership(dbConn, station_name, year):
    dbCursor = dbConn.cursor()
   
    sql = """
            SELECT Station_Name, strftime('%m', Ride_Date) as month, SUM(Num_Riders), strftime('%Y', Ride_Date) as year 
            FROM Ridership
            JOIN Stations ON Ridership.Station_ID = Stations.Station_ID
            WHERE Station_Name LIKE ? AND year = ?
            GROUP BY month ORDER BY month asc
    """

    dbCursor.execute(sql, (station_name, year))
    rows = dbCursor.fetchall()
   
    # If no Data was found
    if not rows:
        nameQuery = """SELECT Station_Name FROM Stations
        WHERE Station_Name LIKE ?
        """
        dbCursor.execute(nameQuery, (station_name,))
        rows = dbCursor.fetchall()
        print("Monthly Ridership at", rows[0][0], "for", year)

    else:
        print("Monthly Ridership at", rows[0][0], "for", year)
        for row in rows:
            print(row[1] + "/" + row[3],":", f"{row[2]:,}")
       
    print()

    # Prompts user if they would like to plot and generates graph
    choice = input("Plot? (y/n) ")
    x = []
    y = []
    if(choice == "y"):
        for row in rows:
            x.append(row[1])
            y.append(row[2])
        figure.xlabel("Month")
        figure.ylabel("Number of Riders")
        figure.title("Monthly Ridership at "+ rows[0][0] + " (" + str(year) + ")")
       
        figure.ioff()
        figure.plot(x,y)
        figure.show()
       
    print()

# command 8: Compares 2 stations 
def plot_Comparison(dbConn, station1, station2, year):
    dbCursor = dbConn.cursor()
    x1 = []
    y1 = []
    x2 = []
    y2 = []
   
    sql1 = """
            SELECT Station_Name, DATE(Ride_Date) as date, SUM(Num_Riders), strftime('%Y', Ride_Date) as year, Stations.Station_ID
            FROM Stations
            JOIN Ridership ON Stations.Station_ID = Ridership.Station_ID
            WHERE Station_Name LIKE ? AND year = ?
            GROUP BY date
            ORDER BY date asc
    """
       
    dbCursor.execute(sql1, (station1, year))
    rows = dbCursor.fetchall()
   
    dayCounter = 1

    # Update Station1
    for row in rows:
        x1.append(dayCounter)
        y1.append(row[2])
        dayCounter += 1
       
    figure.plot(x1,y1, label = rows[0][0])
   
    sql2 = """
            SELECT Station_Name, DATE(Ride_Date) as date, SUM(Num_Riders), strftime('%Y', Ride_Date) as year, Stations.Station_ID
            FROM Stations
            JOIN Ridership ON Stations.Station_ID = Ridership.Station_ID
            WHERE Station_Name LIKE ? AND year = ?
            GROUP BY date
            ORDER BY date asc
    """
   
    dbCursor.execute(sql2, (station2, year))
    rows = dbCursor.fetchall()
   
    dayCounter = 1

    # Update Station2
    for row in rows:
        x2.append(dayCounter)
        y2.append(row[2])
        dayCounter += 1
       
    figure.plot(x2,y2, label = rows[0][0])
   
    figure.xlabel("Day")
    figure.ylabel("Number of Riders")
    figure.title("Ridership Each Day of "+ str(year))
   
    figure.ioff()
    figure.legend()
    figure.show()

# Searches to get total ridership for the first 5 days of the given year
def get_first_five(dbConn, stationName, year, num):
    dbCursor = dbConn.cursor()
   
    sql = """
            SELECT Station_Name, DATE(Ride_Date) as date, SUM(Num_Riders), strftime('%Y', Ride_Date) as year, Stations.Station_ID
            FROM Stations
            JOIN Ridership ON Stations.Station_ID = Ridership.Station_ID
            WHERE Station_Name LIKE ? AND year = ?
            GROUP BY date
            ORDER BY date asc 
            LIMIT 5;
    """
   
    dbCursor.execute(sql, (stationName, year))
    rows = dbCursor.fetchall()
   
    print("Station " + num +":", rows[0][4], rows[0][0])
   
    for row in rows:
        print(row[1], row[2])
       
# Searches to get total ridership for the last 5 days of the given year
def get_last_five(dbConn, stationName, year):
    dbCursor = dbConn.cursor()
   
    sql = """
            SELECT Station_Name, DATE(Ride_Date) as date, SUM(Num_Riders), strftime('%Y', Ride_Date) as year, Stations.Station_ID
            FROM Stations
            JOIN Ridership ON Stations.Station_ID = Ridership.Station_ID
            WHERE Station_Name LIKE ? AND year = ?
            GROUP BY date
            ORDER BY date desc 
            LIMIT 5
    """
   
    dbCursor.execute(sql, (stationName, year))
    rows = dbCursor.fetchall()
       
    #Reverse the array so we can retrieve last 5
    rows = rows[::-1]
   
    for row in rows:
        print(row[1], row[2])
       
# Prompts the user for year and the two station names to compare
# Searches the data base to print first 5 days and last 5 days of total ridership for each station
# Prompts user if they would like to plot points of days and total ridership for given year. Generates graph
def compareRidershipFor2Stations(dbConn, station1, station2, year):
    # Get first 5 days from station1
    get_first_five(dbConn, station1, year, "1")
   
    # Get the last 5 days of the year for station1
    get_last_five(dbConn, station1, year)
       
    # Station 2
    # Get first 5 days from station2
    get_first_five(dbConn, station2, year, "2")
       
    # Get the last 5 days of the year from station2
    get_last_five(dbConn, station2, year)
       
    print()
    choice = input("Plot? (y/n) ")
   
    if(choice == "y"):
        plot_Comparison(dbConn, station1, station2, year)
       
    print()

# command 9: Takes coordinates from user and prints all nearby stations within a 1 mile square boundary
def nearestStations(dbConn, latitude, longitude):
    dbCursor = dbConn.cursor()
    
    sql = """
            SELECT Station_Name as name, Latitude as lat, Longitude as long FROM Stations
            JOIN Stops ON Stations.Station_ID = Stops.Station_ID
            WHERE (lat >= ROUND(? - (1 / 69.0),3) AND lat <= ROUND(? + (1 / 69.0),3))
            AND (long >= ROUND(? - (1/51.0),3) AND long <= ROUND(? + (1/51.0),3))
            GROUP BY name, lat, long
            ORDER BY name asc, lat desc, long desc
    """
   
    dbCursor.execute(sql, (latitude, latitude, longitude, longitude))
    rows = dbCursor.fetchall()
   
    if not rows:
        print("**No stations found...")
        return
    print()

    print("List of Stations Within a Mile")
    print()
    for row in rows:
        print(row[0], ":", "("+str(row[1])+", "+str(row[2])+")")
    print()
   
    choice = input("Plot? (y/n) ")

    if(choice == "y"):
        x = []
        y = []
        image = figure.imread("chicago.png")
        xydims = [-87.9277, -87.5569, 41.7012, 42.0868]
        figure.imshow(image, extent=xydims)
        figure.title("Stations Near You")

        for row in rows:
            x.append(row[2])
            y.append(row[1])
        
        figure.plot(x,y, 'o')

        for row in rows:
            figure.annotate(row[0], (row[2],row[1]))
         
        figure.xlim([-87.9277, -87.5569])
        figure.ylim([41.7012, 42.0868])
        figure.show()
    print()

dbConn = sqlite3.connect("CTA2_L_daily_ridership.db")
display_stats(dbConn)
command_loop(dbConn)
print()

# Close the connection
dbConn.close()
