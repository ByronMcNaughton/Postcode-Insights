# Postcode Info
---
### Api
https://ggvfog559k.execute-api.us-east-1.amazonaws.com/GETDATA?co12zq
### Site
http://xander-final-project.s3-website-us-east-1.amazonaws.com

---
Program includes:
- Database (mysql)
- AWS Lambda Function (Python 3.9)
- AWS API Gateway
- AWS Code Pipeline
- Front End (HTML, CSS, JQuery)

This project takes data regarding a given postcode from three public API's and combines them to present to the end user in a readable format\
The site is both desktop and mobile friendly (To an extent)

## API Documentation
[Postcodes.io](https:/https:/postcodes.io)\
[Planit](https://www.planit.org.uk/api)\
[Data Police](https://data.police.uk/)

## Info
- Code Pipeline from Github to S3
- Website hosted on S3
- Single Lambda Function
- API Gateway for Lambda Function
- JQuery to handle API Call and website modification

## Posible Improvements
- Handle posible errors
  - SQL Errors
  - API Errors
- Could definitely be more functional (In the programming sense)
- Better Database structure (Im also not sure if storing entire dictionarys(as text) in one cell is good practice)
- When searching on the website the first time, if an invalid postcode/error occurs it is caught and relayed to the user, on re-searching without refreshing errors are not displayed\
\
In regards to API Errors, the plan was:
1) Catch Error
2) Have a field in the DB that stores if there was an error with the query
3) Finish as normal and display the data it does have
4) Display an error in relevant section
5) Wait x Seconds and re-run the search
    - Possibly a second lambda is triggered, which checked the db, checks if the api is down, and tries to query and update again
6) Update info for user if available
