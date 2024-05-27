from googleapiclient.discovery import build
from datetime import datetime as dt
from streamlit_option_menu import option_menu

import pymysql
import streamlit as st
import pandas as pd
import plotly.express as px

# Initialize YouTube API client
api_key = 'Enter valid api key'
youtube = build('youtube', 'v3', developerKey=api_key)

# Function to get a database connection
def get_connection():
    try:
        # connect to MySQL server
        connection = pymysql.connect(
            host='127.0.0.1',
            user='root',
            password='1234'
        )
        # check if the 'youtube' database exists
        with connection.cursor() as cursor:
            cursor.execute("SHOW DATABASES LIKE 'youtube'")
            result = cursor.fetchone()
            if not result:
                # Create the 'youtube' database if it doesn't exist
                cursor.execute("CREATE DATABASE IF NOT EXISTS youtube")
        # connect to the 'youtube' database
        connection = pymysql.connect(
            host='127.0.0.1',
            user='root',
            password='1234',
            database='youtube'
        )
        return connection
    
    except Exception as e:
        st.write(f"Error: {e}")
        return None

# Check if a table exists in the database
def table_exists(cursor, table_name):
    cursor.execute(f"""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = '{table_name}'
        AND table_schema = DATABASE();
    """)
    return cursor.fetchone()[0] == 1

# Create table if it doesn't exist
def create_table_if_not_exists(cursor, table_name, create_query, alter_query):
    if not table_exists(cursor, table_name):
        cursor.execute(create_query)
        cursor.execute(alter_query)
        cursor.connection.commit()

# to change the streamlit background color
def set_background_color(color):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {color};
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_background_color('#D3D3D3')

# format the duration to h:m:s:
def parse_duration(duration):
    duration_str = ""
    hours = 0
    minutes = 0
    seconds = 0

    # Remove 'PT' prefix from duration
    duration = duration[2:]

    # Check if hours, minutes and/or seconds are present in the duration string
    if "H" in duration:
        hours_index = duration.index("H")
        hours = int(duration[:hours_index])
        duration = duration[hours_index + 1:]
    if "M" in duration:
        minutes_index = duration.index("M")
        minutes = int(duration[:minutes_index])
        duration = duration[minutes_index + 1:]
    if "S" in duration:
        seconds_index = duration.index("S")
        seconds = int(duration[:seconds_index])

    if hours >= 0:
        duration_str += f"{hours}h "
    if minutes >= 0:
        duration_str += f"{minutes}m "
    if seconds >= 0:
        duration_str += f"{seconds}s"

    return duration_str.strip()

# convert h:m:s in duration to seconds:
def durationtoint(time_str):
    hours, minutes, seconds = time_str.split('h ')[0], time_str.split('h ')[1].split('m ')[0], \
        time_str.split('h ')[1].split('m ')[1][:-1]

    total_seconds = int(hours)*3600 + int(minutes)*60 + int(seconds)
    return total_seconds

# format timestamp:
def parse_time(time_stamp):
    if '.' in time_stamp:
        return dt.strptime(time_stamp,'%Y-%m-%dT%H:%M:%S.%fZ')
    else:
        return dt.strptime(time_stamp,'%Y-%m-%dT%H:%M:%SZ')

# Function to cache channel details
@st.cache_data
def get_channel_details(channel_id):
    channel_id = channel_id.strip()
    channel_data = []
    request = youtube.channels().list(
               part='snippet,statistics,contentDetails',
               id=channel_id)
    response = request.execute()
  
    data = {'channel_id': response['items'][0]['id'],
            'channel_name': response['items'][0]['snippet']['title'],
            'channel_description': response['items'][0]['snippet']['description'],
            'number_of_subscribers': int(response['items'][0]['statistics']['subscriberCount']),
            'views': int(response['items'][0]['statistics']['viewCount']),
            'number_of_videos': int(response['items'][0]['statistics']['videoCount']),
            'playlist_id': response['items'][0]['contentDetails']['relatedPlaylists']['uploads'],
            'published_date': parse_time(response['items'][0]["snippet"]["publishedAt"]).strftime('%Y-%m-%d %H:%M:%S')
            }
    channel_data.append(data)
    
    return channel_data

# to get video ids:
def get_channel_videos(channel_id):
    video_ids = []
    # get Uploads playlist id
    response = youtube.channels().list(id=channel_id, 
                                  part='contentDetails').execute()
    playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    
    request = youtube.playlistItems().list(part='contentDetails', playlistId=playlist_id, maxResults=50)
    response = request.execute()

    for i in range(len(response['items'])):
        video_ids.append(response['items'][i]['contentDetails']['videoId'])

    next_page_token = response.get('nextPageToken')
    more_pages = True

    while more_pages:
        if next_page_token is None:
            more_pages = False
        else:
            request = youtube.playlistItems().list(
                part='contentDetails',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token)
            response = request.execute()

            for i in range(len(response['items'])):
                video_ids.append(response['items'][i]['contentDetails']['videoId'])

            next_page_token = response.get('nextPageToken')

    return video_ids


# Function to cache video details
@st.cache_data
def get_video_details(v_ids):
    video_stats = []
    for i in range(0, len(v_ids)):
        response = youtube.videos().list(
                        part="snippet,contentDetails,statistics",
                        id=v_ids[i]).execute()
        
        like_count = 0
        # Check if 'likeCount' key is present in the response
        if 'likeCount' in response['items'][0]["statistics"]:
            like_count = int(response['items'][0]["statistics"]["likeCount"])
        
        comment_count = 0
        # Check if 'commentCount' key is present in the response
        if 'commentCount' in response['items'][0]["statistics"]:
            comment_count = int(response['items'][0]["statistics"]["commentCount"])
        
        view_count = 0
        # Check if viewCount key is present in the response
        if 'viewCount'  in response['items'][0]["statistics"]:
            view_count = int(response['items'][0]["statistics"]["viewCount"])

        dislike_count=0
        # Check if dislikeCount key is present in the response
        if 'dislikeCount' in response['items'][0]["statistics"]:
            dislike_count = int(response['items'][0]["statistics"]["dislikeCount"])

        data = {
            "c_id": response['items'][0]["snippet"]["channelId"],
            "c_name": response['items'][0]["snippet"]["channelTitle"],
            "v_id": response['items'][0]["id"],
            "v_title": response['items'][0]["snippet"]["title"],
            "pub_date": parse_time(response['items'][0]["snippet"]["publishedAt"]).strftime('%Y-%m-%d %H:%M:%S'),
            "duration": parse_duration(response['items'][0]["contentDetails"]["duration"]),
            "viewCount": int(response['items'][0]["statistics"]["viewCount"]),
            "likeCount": like_count, 
            "dislikeCount": dislike_count,
            "favoriteCount": int(response['items'][0]["statistics"]["favoriteCount"]),
            "commentCount": comment_count,  
            "durationinsec": durationtoint(parse_duration(response['items'][0]["contentDetails"]["duration"]))
        }
        video_stats.append(data)
    return video_stats

# Function to cache comment details retrieval
@st.cache_data
def get_video_comments(video_ids):
    all_comments = []
    videos_no_comments = []
    
    for video_id in video_ids:
        try:
            request = youtube.commentThreads().list(
                part="snippet,replies",
                videoId=video_id,
                maxResults=100
            )
            response = request.execute()
            
            if len(response['items'])>100:

                for item in response['items']:
                    data={'video_id':item['snippet']['videoId'],
                        'comment_id':item['snippet']['topLevelComment']['id'],
                        'comment_desc':item['snippet']['topLevelComment']['snippet']['textDisplay'],
                        'comment_author':item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                        'comment_published_date':parse_time(item['snippet']['topLevelComment']['snippet']['publishedAt']).strftime('%Y-%m-%d %H:%M:%S'),
                    }
                    all_comments.append(data)
            
                    if 'nextPageToken' in response:
                        request = youtube.commentThreads().list(
                        part="snippet",
                        textFormat = "plainText",
                        videoId = video_id,
                        maxResults = 100,
                        pageToken = response.get('nextPageToken')
                        )
                    else:
                        break
            else:
                for item in response['items']:
                    data={'video_id':item['snippet']['videoId'],
                        'comment_id':item['snippet']['topLevelComment']['id'],
                        'comment_desc':item['snippet']['topLevelComment']['snippet']['textDisplay'],
                        'comment_author':item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                        'comment_published_date':parse_time(item['snippet']['topLevelComment']['snippet']['publishedAt']).strftime('%Y-%m-%d %H:%M:%S'),
                    }
                    all_comments.append(data)

        except:
            videos_no_comments.append(video_id)

    if all_comments:
        return all_comments
    else:
        return "No comments available"

# create channel table in mysql
CREATE_TABLE_CHANNEL = """CREATE TABLE IF NOT EXISTS YOUTUBE.CHANNEL
        (
        channel_id varchar(100) primary key,
        channel_name text,
        channel_description text,
        number_of_subscribers int,
        views int,
        number_of_videos int,
        playlist_id text,
        published_date timestamp
        )"""

ALTER_TABLE_CHANNEL = """
    ALTER TABLE YOUTUBE.CHANNEL
    MODIFY COLUMN views bigint,
    MODIFY COLUMN number_of_subscribers bigint,
    MODIFY COLUMN number_of_videos bigint
"""
CREATE_TABLE_VIDEOS = """CREATE TABLE IF NOT EXISTS YOUTUBE.VIDEOS
            (
            c_id text,
            c_name text,
            v_id varchar(100) primary key,
            v_title text,
            pub_date timestamp,
            duration text,
            viewCount int,
            likeCount int,
            dislikeCount int,
            favoriteCount int,
            commentCount int,
            durationinsec int
            )"""

ALTER_TABLE_VIDEOS = """
    ALTER TABLE YOUTUBE.VIDEOS
    MODIFY COLUMN viewCount bigint,
    MODIFY COLUMN likeCount bigint,                        
    MODIFY COLUMN commentCount bigint
"""
CREATE_TABLE_COMMENTS = """CREATE TABLE IF NOT EXISTS YOUTUBE.COMMENTS
                (
                video_id text,
                comment_id varchar(100) primary key,
                comment_desc text,
                comment_author text,
                comment_published_date timestamp
                )"""

ALTER_TABLE_COMMENTS = "ALTER TABLE YOUTUBE.COMMENTS CHANGE comment_id comment_id VARCHAR(255)"

# Option menu in Streamlit
with st.sidebar:
    selected = option_menu(
        menu_title="Menu",
        options=["Home", "Questions"],
        icons=["house-door"],
        menu_icon="emoji-smile",
        default_index=1
    )

# Home menu of Streamlit
if selected == "Home":
    st.title(":blue[YOUTUBE DATA HARVESTING AND WAREHOUSING USING SQL AND STREAMLIT]")
    c_id = st.sidebar.text_input("Enter channel id:")

    # Display channel data and migrate to SQL
    col1, col2 = st.columns(2)
    
    with col1:
        connection = get_connection()
        cursor = connection.cursor()

        if st.sidebar.button("Get channel data"):
            if c_id:
                try:
                    # Create table if it doesn't exist
                    create_table_if_not_exists(cursor, "youtube.channel", CREATE_TABLE_CHANNEL,ALTER_TABLE_CHANNEL)
                    channel_df = pd.DataFrame(get_channel_details(c_id))
                    st.write(channel_df)
                except Exception:
                    st.sidebar.warning("Please enter valid channel id")
            else:
                st.sidebar.warning("Please enter a channel id")

        cursor.close()
        connection.close()

    with col2:
        connection = get_connection()
        cursor = connection.cursor()

        if st.sidebar.button("Move channel data to SQL"):
            # Create table if it doesn't exist
            create_table_if_not_exists(cursor, "youtube.channel", CREATE_TABLE_CHANNEL,ALTER_TABLE_CHANNEL)
            channel_df = pd.DataFrame(get_channel_details(c_id))
            len1 = ",".join(["%s"] * len(channel_df.columns))
            sql = f"INSERT INTO YOUTUBE.CHANNEL VALUES ({len1})"

            try:
                for i in range(len(channel_df)):
                   cursor.execute(sql, tuple(channel_df.iloc[i]))
                   cursor.connection.commit()
                st.sidebar.success("Channel Data moved to SQL successfully")
            except Exception:
                st.sidebar.error("Data Already Exists!")

        cursor.close()
        connection.close()

    # Display videos data and migrate to SQL
    col3, col4 = st.columns(2)

    with col3:
        connection = get_connection()
        cursor = connection.cursor()

        if st.sidebar.button("Get video data"):
            # Create table if it doesn't exist
            create_table_if_not_exists(cursor, "youtube.videos", CREATE_TABLE_VIDEOS,ALTER_TABLE_VIDEOS)
            video_ids = get_channel_videos(c_id)
            video_df = pd.DataFrame(get_video_details(video_ids))
            st.dataframe(video_df)

        cursor.close()
        connection.close()
            
    with col4:
        connection = get_connection()
        cursor = connection.cursor()

        if st.sidebar.button("Move videos data to SQL"):
            # Create table if it doesn't exist
            create_table_if_not_exists(cursor, "youtube.videos", CREATE_TABLE_VIDEOS,ALTER_TABLE_VIDEOS)
            video_ids = get_channel_videos(c_id)
            video_df = pd.DataFrame(get_video_details(video_ids))
            len2 = ",".join(["%s"] * len(video_df.columns))
            sql = f"INSERT INTO YOUTUBE.VIDEOS VALUES ({len2})"

            try:
                for i in range(len(video_df)):
                   cursor.execute(sql, tuple(video_df.iloc[i]))
                   cursor.connection.commit()
                st.sidebar.success("Videos Data moved to SQL successfully")
            except Exception:
                st.sidebar.error("Data Already Exists!")

        cursor.close()
        connection.close()

    # Display comments data and migrate to SQL
    col5, col6 = st.columns(2)

    with col5:
        connection = get_connection()
        cursor = connection.cursor()

        if st.sidebar.button("Get comments data"):
            # Create table if it doesn't exist
            create_table_if_not_exists(cursor, "youtube.comments", CREATE_TABLE_COMMENTS,ALTER_TABLE_COMMENTS)
            video_ids = get_channel_videos(c_id)
            comments = get_video_comments(video_ids)
            comment_df = pd.DataFrame(comments)
            st.write(comment_df)

        cursor.close()
        connection.close()

    with col6:
        connection = get_connection()
        cursor = connection.cursor()

        if st.sidebar.button("Move comments data to SQL"):
            # Create table if it doesn't exist
            create_table_if_not_exists(cursor, "youtube.comments", CREATE_TABLE_COMMENTS,ALTER_TABLE_COMMENTS)
            video_ids = get_channel_videos(c_id)
            comments = get_video_comments(video_ids)
            comment_df = pd.DataFrame(comments)
            len3 = ",".join(["%s"] * len(comment_df.columns))
            sql = f"INSERT INTO YOUTUBE.COMMENTS VALUES ({len3})"

            try:
                for i in range(len(comment_df)):
                    cursor.execute(sql, tuple(comment_df.iloc[i]))
                    cursor.connection.commit()
                st.sidebar.success("Comments Data moved to SQL successfully")
            except Exception:
                st.sidebar.error("Data Already Exists!")

        cursor.close()
        connection.close()

# to execute SQL queries
def execute_query(query):
    return pd.read_sql_query(query, get_connection())

# to create plots
def create_plot(df, plot_type, **kwargs):
    if plot_type == 'pie':
        fig = px.pie(df, **kwargs)
    elif plot_type == 'bar':
        fig = px.bar(df, **kwargs)
    elif plot_type == 'line':
        fig = px.line(df, **kwargs)
    elif plot_type == 'scatter':
        fig = px.scatter(df, **kwargs)
    else:
        fig = None
    if fig:
        fig.update_layout(title_x=0.3)
        st.plotly_chart(fig)

# On selecting Questions menu
if selected == "Questions":
    questions = [
        "What are the names of all the videos and their corresponding channels?",
        "Which channels have the most number of videos, and how many videos do they have?",
        "What are the top 10 most viewed videos and their respective channels?",
        "How many comments were made on each video, and what are their corresponding video names?",
        "Which videos have the highest number of likes, and what are their corresponding channel names?",
        "What is the total number of likes and dislikes for each video, and what are their corresponding video names?",
        "What is the total number of views for each channel, and what are their corresponding channel names?",
        "What are the names of all the channels that have published videos in the year 2022?",
        "What is the average duration of all videos in each channel, and what are their corresponding channel names?",
        "Which videos have the highest number of comments, and what are their corresponding channel names?"
    ]
    
    question = st.selectbox("Select any question", ["Select any question"] + questions)

    if question == questions[0]:
        df = execute_query("SELECT v_title AS Video_name, c_name AS Channel_name FROM youtube.videos")
        st.write(df)
        channel_df = execute_query("SELECT * FROM youtube.channel")
        create_plot(channel_df, 'pie', names='channel_name', values='number_of_videos', hole=0.5, title="Video Count in each Channel")
    
    elif question == questions[1]:
        df = execute_query("SELECT channel_name AS Channel_name, number_of_videos AS Video_count FROM youtube.channel WHERE number_of_videos IN (SELECT MAX(number_of_videos) FROM youtube.channel)")
        st.write(df)
        channel_df = execute_query("SELECT * FROM youtube.channel")
        create_plot(channel_df, 'bar', x='channel_name', y='number_of_videos', color='views', title="Channel vs Video Count")
    
    elif question == questions[2]:
        df = execute_query("SELECT v_id AS Video_Id, v_title AS Video_title, c_name AS Channel_name, viewCount AS View_count FROM youtube.videos ORDER BY viewCount DESC LIMIT 10")
        st.write(df)
        create_plot(df, 'bar', x='Video_Id', y='View_count', hover_name="Video_title", color="Channel_name", title="Top 10 videos vs View Count")
    
    elif question == questions[3]:
        df = execute_query("SELECT v_title AS Video_names, commentCount AS Number_of_comments FROM youtube.videos")
        st.write(df)
        channel_df = execute_query("SELECT c_name AS Channel_name, AVG(viewCount) AS View_Count_AVG, SUM(commentCount) AS Overall_Comment_Count FROM youtube.videos GROUP BY c_name")
        create_plot(channel_df, 'bar', x='Channel_name', y='Overall_Comment_Count', color="View_Count_AVG", title="Channel and their overall comment count")
    
    elif question == questions[4]:
        df = execute_query("SELECT v_title AS Video_names, c_name AS Channel_name FROM youtube.videos WHERE likeCount IN (SELECT MAX(likeCount) FROM youtube.videos)")
        st.write(df)
        top_liked_videos_df = execute_query("SELECT * FROM youtube.videos ORDER BY likeCount DESC LIMIT 10")
        create_plot(top_liked_videos_df, 'pie', names='v_id', values='likeCount', hover_name="v_title", title="Like Count of top 10 videos")
    
    elif question == questions[5]:
        df = execute_query("SELECT v_title AS Video_name, likeCount AS Number_of_likes, dislikeCount AS Number_of_dislikes FROM youtube.videos")
        st.write(df)
        channel_df = execute_query("SELECT c_name AS Channel_name, SUM(likeCount) AS Overall_Like_Count FROM youtube.videos GROUP BY c_name")
        create_plot(channel_df, 'line', x='Channel_name', y='Overall_Like_Count', title="Like Count of all the channels")
    
    elif question == questions[6]:
        df = execute_query("SELECT channel_id AS Channel_id, channel_name AS Channel_name, views AS View_count FROM youtube.channel")
        st.write(df)
        channel_df = execute_query("SELECT * FROM youtube.channel")
        create_plot(channel_df, 'bar', x='channel_name', y='views', title="View Count of all the channels", color="number_of_videos", hover_name="number_of_subscribers")
    
    elif question == questions[7]:
        df = execute_query("SELECT DISTINCT c_name AS Channel_name FROM youtube.videos WHERE YEAR(pub_date) = 2022")
        st.write(df)
        channel_2022_df = execute_query("SELECT * FROM youtube.videos WHERE YEAR(pub_date) = 2022")
        create_plot(channel_2022_df, 'bar', x='c_id', y='viewCount', title="Channel View Count in 2022", color="c_name")
    
    elif question == questions[8]:
        df = execute_query("SELECT c_name AS Channel_name, AVG(durationinsec) AS Average_duration_seconds FROM youtube.videos GROUP BY c_name")
        st.write(df)
        create_plot(df, 'pie', names='Channel_name', values='Average_duration_seconds', hole=0.5, title="Channel name and its average duration in seconds")
    
    elif question == questions[9]:
        df = execute_query("SELECT v_title AS Video_name, c_name AS Channel_name, commentCount AS Number_of_comments FROM youtube.videos WHERE commentCount IN (SELECT MAX(commentCount) FROM youtube.videos)")
        st.write(df)
        all_videos_df = execute_query("SELECT * FROM youtube.videos")
        create_plot(all_videos_df, 'scatter', x="viewCount", y="commentCount", color="c_name", title="View Count vs Comment Count", labels={'viewCount': 'View Count', 'commentCount': 'Comment Count'})

