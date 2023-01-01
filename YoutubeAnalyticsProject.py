from googleapiclient.discovery import build
import pandas as pd
import seaborn as sns
import plotly.express as px
import plotly.io as pio
import isodate
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# NLP
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
nltk.download('stopwords')
nltk.download('punkt')
from wordcloud import WordCloud


pio.renderers.default='browser'


#Warikoo "UCRzYN32xtBf3Yxsx5BvJWJw"
#Dhruv Rathee "UC-CSyyi47VX1lD9zyeABW3w"
#Sandeep Maheshwari "UCBqFKDipsnzvJdt6UT0lMIg"
analysis_of="Dhruv Rathee"

api_key='AIzaSyBsdQarSZl9ak1l7p-GLOceQQEcvx1Jr9I'
channel_ids=["UC-CSyyi47VX1lD9zyeABW3w"]
youtube = build('youtube', 'v3', developerKey=api_key)

#FUNCTIONS

#CHANNEL_STATS
def get_channel_stats(youtube, channel_ids):
    all_data = []
    request = youtube.channels().list(
                part='snippet,contentDetails,statistics',
                id=','.join(channel_ids))
    response = request.execute() 
    

    for i in range(len(response['items'])):
        data = dict(Channel_name = response['items'][i]['snippet']['title'],
                    Subscribers = response['items'][i]['statistics']['subscriberCount'],
                    Views = response['items'][i]['statistics']['viewCount'],
                    Total_videos = response['items'][i]['statistics']['videoCount'],
                    playlist_id = response['items'][i]['contentDetails']['relatedPlaylists']['uploads'])
        all_data.append(data)

    
    return all_data


#GETTING VIDEO IDS
def get_video_ids(youtube, playlist_id):
    
    request = youtube.playlistItems().list(
                part='contentDetails',
                playlistId = playlist_id,
                maxResults = 50)
    response = request.execute()
    
    video_ids = []
    
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
                        playlistId = playlist_id,
                        maxResults = 50,
                        pageToken = next_page_token)
            response = request.execute()
    
            for i in range(len(response['items'])):
                video_ids.append(response['items'][i]['contentDetails']['videoId'])
            
            next_page_token = response.get('nextPageToken')
        
    return video_ids

#GETTING VIDEO DETAILS
def get_video_details(youtube, video_ids):
    all_video_stats = []
    
    for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
                    part='snippet,statistics,contentDetails',
                    id=','.join(video_ids[i:i+50]))
        response = request.execute()
        
        
    
        for video in response['items']:
            video_stats = dict(Title = video['snippet']['title'],
                               Published_date = video['snippet']['publishedAt'],
                               Views = video['statistics']['viewCount'],
                               Likes = video['statistics']['likeCount'],
                               Duration=video['contentDetails']['duration']
                               #Dislikes = video['statistics']['dislikeCount'],
                               #Comments = video['statistics']['commentCount']
                               )
            all_video_stats.append(video_stats)
            

    return all_video_stats



channel_statistics = get_channel_stats(youtube, channel_ids)
channel_data = pd.DataFrame(channel_statistics)
channel_data['Subscribers'] = pd.to_numeric(channel_data['Subscribers'])
channel_data['Views'] = pd.to_numeric(channel_data['Views'])
channel_data['Total_videos'] = pd.to_numeric(channel_data['Total_videos'])



playlist_id = channel_data.loc[channel_data['Channel_name']==analysis_of, 'playlist_id'].iloc[0]




video_ids = get_video_ids(youtube, playlist_id)



video_details = get_video_details(youtube, video_ids)
video_data = pd.DataFrame(video_details)
video_data['Published_date'] = pd.to_datetime(video_data['Published_date']).dt.date
video_data['Views'] = pd.to_numeric(video_data['Views'])
video_data['Likes'] = pd.to_numeric(video_data['Likes'])
#video_data['Dislikes'] = pd.to_numeric(video_data['Dislikes'])
#video_data['Comments'] = pd.to_numeric(video_data['Comments'])
video_data['Views'] = pd.to_numeric(video_data['Views'])

video_data['DurationSecs']=video_data['Duration'].apply(lambda x: isodate.parse_duration(x))
video_data['DurationSecs']=video_data['DurationSecs'].astype('timedelta64[s]')
video_data['time'] = video_data['Published_date'].apply(lambda x: pd.to_datetime(x).value/10**18)





#GRAPHS

#TOP10
top10_videos = video_data.sort_values(by='Likes', ascending=False).head(10)
ax1 = sns.barplot(x='Likes', y='Title', data=top10_videos)

top10_videos = video_data.sort_values(by='Views', ascending=False).head(10)
ax1 = sns.barplot(x='Views', y='Title', data=top10_videos)

fig = px.line(video_data, x='Published_date', y="Views")
fig.show()


#MONTH WISE UPLOADS
video_data['Month'] = pd.to_datetime(video_data['Published_date']).dt.strftime('%b')
videos_per_month = video_data.groupby('Month', as_index=False).size()
sort_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
             'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
videos_per_month.index = pd.CategoricalIndex(videos_per_month['Month'], categories=sort_order, ordered=True)
videos_per_month = videos_per_month.sort_index()
ax2 = sns.barplot(x='Month', y='size', data=videos_per_month)

#WEEK WISE UPLOADS
video_data['publish_Day'] = video_data['Published_date'].apply(lambda x: x.strftime("%A")) 
day_df = pd.DataFrame(video_data['publish_Day'].value_counts())
weekdays = [ 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
day_df = day_df.reindex(weekdays)
ax = day_df.reset_index().plot.bar(x='index', y='publish_Day', rot=0)

#CORRELATIONS
print(video_data.corr())
sns.lmplot(x='DurationSecs',y='Views',data=video_data)

#WORD CLOUD
stop_words = set(stopwords.words('english'))
video_data['title_no_stopwords'] = video_data['Title'].apply(lambda x: [item for item in str(x).split() if item not in stop_words])

all_words = list([a for b in video_data['title_no_stopwords'].tolist() for a in b])
all_words_str = ' '.join(all_words) 

def plot_cloud(wordcloud):
    plt.figure(figsize=(30, 20))
    plt.imshow(wordcloud) 
    plt.axis("off");

wordcloud = WordCloud(width = 2000, height = 1000, random_state=1, background_color='black', 
                      colormap='viridis', collocations=False).generate(all_words_str)
plot_cloud(wordcloud)






