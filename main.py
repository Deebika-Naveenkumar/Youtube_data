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
# connecting to mysql database
myconnection = pymysql.connect(host="127.0.0.1", user="root", passwd="1234")

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

# function to get channel details:
def get_channel_details(youtube, channel_id):
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
def get_channel_videos(youtube, channel_id):
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

# function to get video details:
def get_video_details(youtube, v_ids):
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
        if 'viewCount' in response['items'][0]["statistics"]:
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

# function to get comment details: 
def get_video_comments(youtube, video_ids):
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
                
# create database in mysql
myconnection.cursor().execute("""CREATE DATABASE IF NOT EXISTS YOUTUBE""")

# create channel table in mysql
myconnection.cursor().execute("""CREATE TABLE IF NOT EXISTS YOUTUBE.CHANNEL
        (
        channel_id varchar(100) primary key,
        channel_name text,
        channel_description text,
        number_of_subscribers int,
        views int,
        number_of_videos int,
        playlist_id text,
        published_date timestamp
        )""")

# changing the datatypes from int to bigint
myconnection.cursor().execute("""
    ALTER TABLE YOUTUBE.CHANNEL
    MODIFY COLUMN views bigint,
    MODIFY COLUMN number_of_subscribers bigint,
    MODIFY COLUMN number_of_videos bigint
""")

# create videos table in mysql
myconnection.cursor().execute("""CREATE TABLE IF NOT EXISTS YOUTUBE.VIDEOS
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
            )""")

# changing the datatypes from int to bigint
myconnection.cursor().execute("""
    ALTER TABLE YOUTUBE.VIDEOS
    MODIFY COLUMN viewCount bigint,
    MODIFY COLUMN likeCount bigint,                        
    MODIFY COLUMN commentCount bigint
""")

# create comments table in mysql
myconnection.cursor().execute("""CREATE TABLE IF NOT EXISTS YOUTUBE.COMMENTS
                (
                video_id text,
                comment_id varchar(100) primary key,
                comment_desc text,
                comment_author text,
                comment_published_date timestamp
                )""")

# option menu in streamlit
with st.sidebar:
    selected = option_menu(
        menu_title = "Menu",
        options = ["Home", "Questions"],
        icons = ["house-door"],
        menu_icon = ["emoji-smile"],
        default_index = 0
    )

# Home menu of Streamlit
if selected == "Home":
    st.title(":blue[YOUTUBE DATA HARVESTING AND WAREHOUSING USING SQL AND STREAMLIT]")
    c_id = st.sidebar.text_input("Enter channel id:")  

    # display channel data and migrate to sql
    col1,col2 = st.columns(2)
    
    with col1:
        if st.sidebar.button("Get channel data"):
            if c_id:
                try:
                    channel_df = pd.DataFrame(get_channel_details(youtube,c_id))
                    st.dataframe(channel_df)
                    
                except Exception as e:
                    st.sidebar.warning("Please enter a valid channel id")
            else:
                st.sidebar.warning("Please enter a channel id")

    with col2:
        if st.sidebar.button("Move channel data to SQL"):
            channel_df = pd.DataFrame(get_channel_details(youtube,c_id))
            len1 = ",".join(["%s"] * len(channel_df.columns))
            sql = f"INSERT INTO YOUTUBE.CHANNEL VALUES ({len1})"
            try:
                for i in range(len(channel_df)):
                    myconnection.cursor().execute(sql,tuple(channel_df.iloc[i]))
                    myconnection.commit()
                st.sidebar.success("Channel Data moved to SQL successfully")
            except Exception as e:
                st.sidebar.error("Data Already Exists!")

    # display videos data and migrate to sql
    col3,col4 = st.columns(2)

    with col3:
        if st.sidebar.button("Get video data"):
            video_ids = get_channel_videos(youtube, c_id)
            video_df = pd.DataFrame(get_video_details(youtube, video_ids))
            st.dataframe(video_df)
            
    with col4:
        if st.sidebar.button("Move videos data to SQL"):
            video_ids = get_channel_videos(youtube, c_id)
            video_df = pd.DataFrame(get_video_details(youtube, video_ids))
            len2 = ",".join(["%s"] * len(video_df.columns))
            sql = f"INSERT INTO YOUTUBE.VIDEOS VALUES ({len2})"
            try:
                for i in range(len(video_df)):
                    myconnection.cursor().execute(sql, tuple(video_df.iloc[i]))
                    myconnection.commit()
                st.sidebar.success("Videos Data moved to SQL successfully")
            except:
                    st.sidebar.error("Data Already Exists!")
        
    # display comments data and migrate to sql
    col5,col6=st.columns(2)

    with col5:
        if st.sidebar.button("Get comments data"):
            video_ids = get_channel_videos(youtube, c_id)
            comment_df = get_video_comments(youtube,video_ids)
            st.write(pd.DataFrame(comment_df))
           
    with col6:
        if st.sidebar.button("Move comments data to SQL"):
            video_ids = get_channel_videos(youtube, c_id)
            comment_df = pd.DataFrame(get_video_comments(youtube,video_ids))
            len3 = ",".join(["%s"] * len(comment_df.columns))
            sql = f"INSERT INTO YOUTUBE.COMMENTS VALUES ({len3})"
 
            try:
                for i in range(len(comment_df)):
                    myconnection.cursor().execute(sql, tuple(comment_df.iloc[i]))
                    myconnection.commit()
                st.sidebar.success("Data moved to SQL successfully")
            except:
                st.sidebar.error("Data Already Exists!")

# On selecting Questions menu
elif selected == "Questions":
    quest_1 = "What are the names of all the videos and their corresponding channels?"
    quest_2 = "Which channels have the most number of videos, and how many videos do they have?"
    quest_3 = "What are the top 10 most viewed videos and their respective channels?"
    quest_4 = "How many comments were made on each video, and what are their corresponding video names?"
    quest_5 = "Which videos have the highest number of likes, and what are their corresponding channel names?"
    quest_6 = "What is the total number of likes and dislikes for each video, and what are their corresponding video names?"
    quest_7 = "What is the total number of views for each channel, and what are their corresponding channel names?"
    quest_8 = "What are the names of all the channels that have published videos in the year2022?"
    quest_9 = "What is the average duration of all videos in each channel, and what are their corresponding channel names?"
    quest_10 = "Which videos have the highest number of comments, and what are their corresponding channel names?"

    question=st.selectbox("Select any question",["Select any question",quest_1,quest_2,quest_3,quest_4,quest_5,quest_6,quest_7,quest_8,quest_9,quest_10])
    
    if question==quest_1:
        st.write(pd.read_sql_query("SELECT v_title as Video_name,c_name as Channel_name FROM youtube.videos",myconnection))
        df_1 = pd.read_sql_query("SELECT * FROM youtube.channel",myconnection)
        fig1 = px.pie(df_1,names='channel_name',values='number_of_videos',hole=0.5,title="Video Count in each Channel")
        st.plotly_chart(fig1)
        
    elif question == quest_2:
        st.write(pd.read_sql_query("SELECT channel_name as Channel_name, number_of_videos as Video_count FROM youtube.channel where number_of_videos in (select max(number_of_videos) from youtube.channel)",myconnection))
        df_2 = pd.read_sql_query("SELECT * FROM youtube.channel",myconnection)
        fig2 = px.bar(df_2,x='channel_name',y='number_of_videos',color='views',title="Channel vs Video Count")
        fig2.update_layout(title_x=0.3)
        st.plotly_chart(fig2)

    elif question == quest_3:
        df_3 = pd.read_sql_query("SELECT v_id as Video_Id,v_title as Video_title, c_name as Channel_name,viewCount as View_count FROM youtube.videos order by viewCount desc limit 10",myconnection)
        st.write(df_3)
        fig3 = px.bar(df_3,x='Video_Id',y='View_count',hover_name="Video_title",color="Channel_name",title="Top 10 videos vs View Count")
        fig3.update_layout(title_x=0.3)
        st.plotly_chart(fig3)

    elif question == quest_4:
        st.write(pd.read_sql_query("SELECT v_title as Video_names,commentCount as Number_of_comments FROM youtube.videos",myconnection))
        df_4 = pd.read_sql_query("SELECT c_name as Channel_name, avg(viewCount) as View_Count_AVG,sum(commentCount) as Overall_Comment_Count from youtube.videos group by c_name",myconnection)
        fig4 = px.bar(df_4,x='Channel_name',y='Overall_Comment_Count',color="View_Count_AVG",title="Channel and their overall comment count")
        fig4.update_layout(title_x=0.3)
        st.plotly_chart(fig4)

    elif question == quest_5:
        st.write(pd.read_sql_query("SELECT v_title as Video_names,c_name as Channel_name FROM youtube.videos where likeCount in (SELECT max(likeCount) FROM youtube.videos)",myconnection)) 
        df_5 = pd.read_sql_query("SELECT * FROM youtube.videos order by likeCount desc limit 10;",myconnection)
        fig5 = px.pie(df_5,names='v_id',values='likeCount',hover_name="v_title",title="Like Count of top 10 videos")
        st.plotly_chart(fig5)

    elif question == quest_6:
        st.write(pd.read_sql_query("SELECT v_title as Video_name,likeCount as Number_of_likes,dislikeCount as Number_of_dislikes FROM youtube.videos",myconnection)) 
        df_6 = pd.read_sql_query("SELECT c_name as Channel_name,sum(likeCount) as Overall_Like_Count from youtube.videos group by c_name",myconnection)
        fig6 = px.line(df_6,x='Channel_name',y='Overall_Like_Count',title="Like Count of all the channels")
        fig6.update_layout(title_x=0.3)
        st.plotly_chart(fig6)
    
    elif question == quest_7:
        st.write(pd.read_sql_query("SELECT  channel_id as Channel_id,channel_name as Channel_name,views as View_count FROM youtube.channel",myconnection))
        df_7 = pd.read_sql_query("SELECT * FROM youtube.channel",myconnection)
        fig7 = px.bar(df_7,x='channel_name',y='views',title="View Count of all the channels",color="number_of_videos",hover_name="number_of_subscribers")
        fig7.update_layout(title_x=0.3)
        st.plotly_chart(fig7)
    
    elif question == quest_8:
        st.write(pd.read_sql_query("SELECT distinct c_name as Channel_name FROM youtube.videos where year(pub_date)=2022",myconnection))
        df_8 = pd.read_sql_query("SELECT * FROM youtube.videos where year(pub_date)=2022",myconnection)
        fig8 = px.bar(df_8,x='c_id',y='viewCount',title="Channel View Count in 2022",color="c_name")
        fig8.update_layout(title_x=0.3)
        st.plotly_chart(fig8)
    
    elif question == quest_9:
        df_9 = pd.read_sql_query("SELECT c_name as Channel_name,avg(durationinsec) as Average_duration_seconds FROM youtube.videos group by c_name",myconnection)
        st.write(df_9)
        fig9 = px.pie(df_9,names='Channel_name',values='Average_duration_seconds',hole=0.5,title="Channel name and its average duration in seconds")
        st.plotly_chart(fig9)

    elif question == quest_10:
        st.write(pd.read_sql_query("SELECT v_title as Video_name,c_name as Channel_name,commentCount as Number_of_comments FROM youtube.videos where commentCount in (SELECT max(commentCount) FROM youtube.videos)",myconnection))
        df_10 = pd.read_sql_query("SELECT * from youtube.videos",myconnection)
        fig10 = px.scatter(df_10,x="viewCount",y="commentCount",color="c_name",title="View Count vs Comment Count",labels={'viewCount': 'View Count', 'commentCount': 'Comment Count'})
        fig10.update_layout(title_x=0.3)
        st.plotly_chart(fig10)
