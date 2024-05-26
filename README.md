                                                  YouTube Data Harvesting and Warehousing using SQL and Streamlit   

Project Title: YouTube Data Harvesting and Warehousing using SQL and Streamlit

Problem Statement: The problem statement is to create a Streamlit application that allows users to access and analyze data from multiple YouTube channels. 

NAME : Deebika Naveenkumar

BATCH: MDTM21

DOMAIN : Social Media (YouTube)

Lanuage & Tool used: Python, Streamlit, SQL

Introduction:

This project is a YouTube API scrapper that allows users to retrieve and analyze data from YouTube channels. It utilizes the YouTube Data API to fetch information such as channel details,video details and comments. The scrapper provides various functionalities to extract and process YouTube data for further analysis and insights.

Features:

The YouTube Data Scraper offers a range of features to help you extract and analyze data from YouTube. Some of the key features include:

Retrieve channel details: Get detailed information about YouTube channels, including subscriber count, view count, video count, and other relevant metrics.

Fetch video details: Extract data such as video title, description, duration, view count, like count, dislike count, and publish date for individual videos.

Extract comments: Retrieve comments made on YouTube videos and their details.

Data storage: Store the collected YouTube data in a database for easy retrieval and future reference.

Generate reports: Generate reports and visualizations based on the collected data and display in Streamlit application.

Technologies Used:

Python: The project is implemented using the Python programming language.

YouTube Data API: Utilizes the official YouTube Data API to interact with YouTube's platform and retrieve data through generating API key.

Streamlit: The user interface and visualization are created using the Streamlit framework, providing a seamless and interactive experience.

MySQL: A powerful open-source relational database management system used to store and manage the retrieved data.

Pandas: A powerful data manipulation and analysis library in Python. Pandas is used in the YouTube Data Scraper to handle and process data obtained from YouTube, providing various functionalities.

Process Flow:

Obtain YouTube API credentials: Visit the Google Cloud Console.

Create a new project or select an existing project.

Enable the YouTube Data API v3 for your project.

Create API credentials for youtube API v3.

Obtain API credentials:

1.Go to the Google Developers Console.

2.Create a new project or select an existing project.

3.Enable the YouTube Data API v3.

ETL Process:

Extracting Data from youtube API.

Transforming data into the required format.

Loading Data into SQL.

Application Flow:

Select Home or Questions from options menu at the sidebar.

Input the Channel id and click on Get channel data in order to retrive channel data from Youtube API.

Next click on Move channel details to SQL that will push your extracted info into the tables in SQL.

Follow the same procedure for video and comments details.

Once done, you can select the Questions menu and get a detailed analysis of the collected data for the respective questions.

Configuration:

1.Open the main.py file in the project directory.

2.Set the desired configuration options:

3.Specify your YouTube API key.

4.Choose the database connection details (MySQL).

5.Get the Youtube Channel ID from the Youtube's Home>more>About>Share channel>copy channel id

6.Provide the Youtube Channel ID in the Enter channel id box..

Usage:

1.Launch the Streamlit app: streamlit run main.py

Note: If streamlit run main.py doesnot work kindly give python -m streamlit run main_file_path.py

2.Run the main.py script

3.The app will start and open in your browser. You can explore the harvested YouTube data and visualize the results.





