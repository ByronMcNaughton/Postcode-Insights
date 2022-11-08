import json
import requests
import pymysql
from datetime import date, timedelta, datetime
from collections import Counter

################
#
#for i in range - add if > range
#add try catch for sql
#error messages for api's, store error in root db
#comment
#
################


# How long the data is stored before updating
days_to_subtract = 1

Host = "lin-11314-6893-mysql-primary.servers.linodedb.net"
Name = "user_4"
Password = "3_9_mRu0dVKy_jJKRaqhddA2pbxyJl"
Database = "db4"


def nearest_postcodes(postcode, longitude, latitude, cur, update):
    ##calls api to get nearest postcodes, var update defines if to update or add new to db
    url = f"https://api.postcodes.io/postcodes?lon={longitude}&lat={latitude}"
    page = requests.get(url).json()

    # if the database needs updating simply delete all relevant data
    if update:
        sql = f'DELETE FROM Nearest_Postcodes WHERE postcode="{postcode}";'
        cur.execute(sql)

    # add each to database
    for local_postcode in page["result"]:
        if local_postcode["postcode"] != postcode:
            sql = f'INSERT INTO Nearest_Postcodes VALUES (NULL, "{postcode}", "{local_postcode["postcode"]}", {local_postcode["longitude"]}, {local_postcode["latitude"]});'
            cur.execute(sql)


def planning_permissions(postcode, longitude, latitude, cur, update):
    ##calls api to get planning aplications
    url = f"https://www.planit.org.uk/api/applics/json?lat={latitude}&lng={longitude}&krad=5.0&recent=30&pg_sz=5&sort=distance&compress=on"
    page = requests.get(url).json()

    print(page)
    # if the database needs updating simply delete all relevant data
    
    if update:
        sql = f'DELETE FROM Planning WHERE postcode="{postcode}";'
        cur.execute(sql)

    try:
        for application in page["records"]:
            sql = f'INSERT INTO Planning VALUES (NULL, "{postcode}", "{application["address"]}", "{application["description"]}", "{application["url"]}");'
            cur.execute(sql)
    except KeyError:
        sql = f'INSERT INTO Planning VALUES (NULL, "{postcode}", NULL, NULL, NULL);'
        cur.execute(sql)
    
    # add each to database
    



def crime_data(postcode, longitude, latitude, cur, update):
    ##calls the api to get crime data
    url = f"https://data.police.uk/api/crimes-street/all-crime?lat={latitude}&lng={longitude}"
    page = requests.get(url).json()

    # if the database needs updating simply delete all relevant data
    if update:
        sql = f'DELETE FROM Crime_Data WHERE postcode="{postcode}";'
        cur.execute(sql)

    category = []
    name = []
    status = []
    status_not_none = []
    
    #for each crime take the relevant data
    for c in page:
        category.append(c['category'])
        #same data was just "On or near", i later remove this prefix so change it to None
        if c['location']['street']['name'] != "On or near ":
            name.append(c['location']['street']['name'].replace("On or near ", ""))
        else:
            name.append("No Location")
        status.append(c['outcome_status'])

    #replace all None values
    status[:] = (value for value in status if value)
    for i in status:
        status_not_none.append(i['category'])

    name = json.dumps(Counter(name)).replace("'", "")
    name = json.loads(name)
    
    #take the 20 street names with the largest values if more than 20 exist
    if len(name) > 20:
        most_common_name = {}
        for i in range(20):
            l = max(name, key=lambda key: name[key])
            most_common_name[l] = name[l]
            name.pop(l)
    else:
        most_common_name = name
    most_common_name=json.dumps(most_common_name)
    
    category = json.dumps(Counter(category)).replace("'", "")
    category = json.loads(category)

    #sort the dictionary ish, adds them in order from largest to smallest so easier on front end
    category_sorted = {}
    
    #sort the dictionary ish, adds them in order from largest to smallest so easier on front end
    for i in range(len(category)):
        c = max(category, key=lambda key: category[key])
        category_sorted[c] = category[c]
        category.pop(c)
    category_sorted = json.dumps(category_sorted).replace("-", " ")

    #lil bit of formatting
    date = page[0]["month"] + "-01"
    status = json.dumps(Counter(status_not_none)).replace("'", "")
    status = status.replace("}", "")
    status = status + ", \"None\": "+ str(len(page)-len(status_not_none)) + "}"

    sql_insert = f"INSERT INTO Crime_Data VALUES (NULL, '{postcode}', '{category_sorted}', '{most_common_name}', '{status}', {len(page)}, '{date}');"
    cur.execute(sql_insert)


def lambda_handler(event, context):
    # get postcode passed from front end
    postcode = event["rawQueryString"]
    # call postcodes.io to verify the postcode
    url = "https://postcodes.io/postcodes/" + postcode
    page = requests.get(url)

    # if postcodes.io does not reply with a success return the response
    if page.json()["status"] != 200:
        return page.json()

    # try to connect to the db, return the error if unable to
    try:

        conn = pymysql.connect(host=Host, user=Name, password=Password, db=Database, connect_timeout=5,
                               ssl={"fake_flag_to_enable_tls": True})
        cur = conn.cursor()
    except pymysql.MySQLError as e:
        return {
            "result": 503,
            "error": json.dumps(e)
        }

    # store necessary data from postcodes.io
    postcode = page.json()["result"]["postcode"]
    longitude = page.json()["result"]["longitude"]
    latitude = page.json()["result"]["latitude"]
    pc = page.json()["result"]["parliamentary_constituency"]

    date_time = datetime.now()
    #store search
    sql = f'INSERT INTO Searches VALUES(NULL, "{postcode}", "{date_time}");'
    cur.execute(sql)
    conn.commit()

    # query the database to see if the postcode is stored
    sql_request = f'SELECT * FROM Postcode_Root WHERE postcode = "{postcode}";'

    cur.execute(sql_request)
    result = cur.fetchone()

    # store current date and expiry date of data
    curr_date = date.today()
    out_of_date = curr_date - timedelta(days=days_to_subtract)
    # if postcode is in database
    if result:
        # if data has expired call functions with update=True
        if result[1] < out_of_date:
            sql_update = f"UPDATE Postcode_Root SET date_added='{curr_date}' WHERE postcode='{postcode}';"
            cur.execute(sql_update)
            nearest_postcodes(postcode, longitude, latitude, cur, True)
            crime_data(postcode, longitude, latitude, cur, True)
            planning_permissions(postcode, longitude, latitude, cur, True)
        # if data is valid
    # if postcode is not in database call functions with update=False
    else:
        sql_insert = f'INSERT INTO Postcode_Root Values ("{postcode}", "{curr_date}");'
        cur.execute(sql_insert)
        nearest_postcodes(postcode, longitude, latitude, cur, False)
        crime_data(postcode, longitude, latitude, cur, False)
        planning_permissions(postcode, longitude, latitude, cur, False)

    # query database for data
    cur.execute(f'SELECT * FROM Postcode_Root WHERE postcode="{postcode}";')
    Postcode_Root = cur.fetchone()
    cur.execute(f'SELECT local_postcode, longitude, latitude FROM Nearest_Postcodes WHERE postcode="{postcode}";')
    Nearest_Postcodes = cur.fetchall()
    cur.execute(
        f'SELECT category, street_name, outcome_status, total_crime, crime_date FROM Crime_Data WHERE postcode="{postcode}";')
    Crime_Data = cur.fetchone()
    cur.execute(f'SELECT address, description, url FROM Planning WHERE postcode="{postcode}";')
    Planning_Data = cur.fetchall()

    # transform into dictionary
    near_pc = {}
    for p in Nearest_Postcodes:
        near_pc[p[0]] = {"longitude": p[1], "latitude": p[2]}

    plan = {}
    count = 0
    for PD in Planning_Data:
        plan[count] = {"address": PD[0], "description": PD[1], "url": PD[2]}
        count += 1

    conn.commit()
    return {
        "status": 200,
        "postcode": Postcode_Root[0],
        "parliamentary_constituency": pc,
        "nearest_postcodes": near_pc,
        "planning_data": plan,
        "total_crime": Crime_Data[3],
        "crime_date": Crime_Data[4].strftime("%m/%d/%Y").replace("/01", ""),
        "category": json.loads(Crime_Data[0]),
        "street_name": json.loads(Crime_Data[1]),
        "outcome_status": json.loads(Crime_Data[2])
    }
