from flask import Flask
from pororo import Pororo
import pandas as pd
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pymysql 

app = Flask(__name__)

/////////////////////추가된부분
host_name = "findmap-first-db.c2jag33neij8.ap-northeast-2.rds.amazonaws.com"
user_name = "admin"
password = "mypassword"
db_name = "findmap-first-db"


userid = 0    ### node 로부터 user ID 를 받아야됨

db = pymysql.connect(
    host = host_name,
    port = 3306,
    user = user_name,
    passwd = password,
    db = db_name,
    charset = 'utf8'
)

SQL = "select st.userIdx, st.keywordidx , count(st.keywordidx) as rating from SearchTB st "  ///논의 해봐야할 부분
///////////////////////////

##rating_path = './'
##ratings_df = pd.read_csv(os.path.join(rating_path, 'ratings.csv'), encoding='utf-8')

df  = pd.read_sql(SQL,db, encoding ='utf-8')

train_df, test_df = train_test_split(df, test_size=0.2, random_state=1234)

def cos_matrix(a, b):
    cos_values = cosine_similarity(a.values, b.values)
    cos_df = pd.DataFrame(data=cos_values, columns = a.index.values, index=a.index)
    return cos_df

print(train_df.shape)
print(test_df.shape)

sparse_matrix = train_df.groupby('keywordidx').apply(lambda x: pd.Series(x['rating'].values, index=x['userIdx'])).unstack()
sparse_matrix.index.name = 'keywordidx'

sparse_matrix_withsearch = sparse_matrix.apply(lambda x: x.fillna(x.mean()), axis=1)
search_cos_df = cos_matrix(sparse_matrix_withsearch, sparse_matrix_withsearch)

userId_grouped = train_df.groupby('userIdx')
search_prediction_ = pd.DataFrame(index=list(userId_grouped.indices.keys()), columns=sparse_matrix_withsearch.index)


for userId, group in userId_grouped:
    
    user_sim = search_cos_df.loc[group['keywordidx']]
    user_rating = group['rating']
    sim_sum = user_sim.sum(axis=0)

    # userId의 전체 rating predictions 
    pred_ratings = np.matmul(user_sim.T.to_numpy(), user_rating) / (sim_sum+1)
    search_prediction_.loc[userId] = pred_ratings

@app.route('/')
def recommendation():
    return search_prediction_.loc[userid].idxmax(axis = 1)


if __name__ == '__main__':
    app.run()