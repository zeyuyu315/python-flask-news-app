from flask import Flask, jsonify
from newsapi import NewsApiClient, newsapi_exception
from string import punctuation


api_key = '93c81ffb086941518f393857943ec936'
# api_key = '39c3ed21ae91412a83e43513d94decb7'
LIMIT = 30

# EB looks for an 'application' callable by default.
application = Flask(__name__)

# init
newsapi = NewsApiClient(api_key)

@application.route('/')
def homepage():
    return application.send_static_file("index12139.html")

@application.route('/init', methods=['GET'])
def initialize_news():
    try:
        # /v2/top-headlines
        slides_headlines = newsapi.get_top_headlines(language='en', page_size=LIMIT)
        cnn_headlines = newsapi.get_top_headlines(language='en', page_size=LIMIT, sources='cnn')
        fox_headlines = newsapi.get_top_headlines(language='en', page_size=LIMIT, sources='fox-news')
    except:
        return jsonify({'error': 'API error'})
    tasks = []
    word_cloud = {}
    # read all the stop words
    stopwords = set()
    with open('stopwords_en.txt', 'r') as file:
        for line in file:
            for word in line.split():
                stopwords.add(word)
    frequent = []
    cnn_tasks = []
    fox_tasks = []
    articles = slides_headlines['articles']
    cnn_articles = cnn_headlines['articles']
    fox_articles = fox_headlines['articles']
    for article in articles:
        title = article['title']
        if title is not None and title.strip():
            for word in title.split():
                word = word.strip(punctuation)
                if word and word.lower() not in stopwords:
                    if word not in word_cloud:
                        word_cloud[word] = 0
                    word_cloud[word] += 1
        if checkEmpty(article) and len(tasks) < 5:
                tasks.append(article)
    sorted_d = sorted(word_cloud.items() , key=lambda t : t[1])
    if len(sorted_d) > LIMIT:
        for i in range(LIMIT):
            frequent.append(sorted_d.pop())
    else:
        frequent = list(sorted_d)

    for article in cnn_articles:
        if checkEmpty(article) and len(cnn_tasks) < 4:
                cnn_tasks.append(article)
    
    for article in fox_articles:
        if checkEmpty(article) and len(fox_tasks) < 4:
                fox_tasks.append(article)
    
    return jsonify({'slides_articles': tasks, 'word_cloud': frequent, 'cnn': cnn_tasks, 'fox': fox_tasks})

# check if the returned json do not contain empty field
def checkEmpty(dict) :
        items = ['author', 'content', 'description', 'publishedAt', 'title', 'url', 'urlToImage']
        for item in items:
            if dict[item] is None or not dict[item].strip():
                return False
        if dict['source'] is None:
            return False
        else :
            # if dict['source']['id'] is None or not dict['source']['id'].strip():
            #    return False
            if dict['source']['name'] is None or not dict['source']['name'].strip():
                return False
        return True


@application.route('/sources/<string:category_type>', methods=['GET'])
def get_source(category_type):
    try: 
        # /v2/sources
        if category_type == 'all':
            sources = newsapi.get_sources(language='en', country='us')
        else:
            sources = newsapi.get_sources(language='en', country='us', category=category_type)
    except:
        return jsonify({'error': 'API error'})
    name_dict = {}
    for source in sources['sources']:
        name = source['name']
        name_id = source['id']
        if name is not None and name.strip() and name_id is not None and name_id.strip() and name not in name_dict:
            name_dict[name] = name_id
    top_dict = {k: name_dict[k] for k in list(name_dict)[:10]}
    return jsonify({'sorted_list': top_dict})


@application.route('/q=<string:q>&source=<string:source>&fromdate=<string:fromdate>&to=<string:to>', methods=['GET'])
def get_result(q, source, fromdate, to):
    try: 
        if source == 'all':
            result = newsapi.get_everything(q=q, from_param=fromdate, to=to, language='en', page_size=LIMIT, sort_by='publishedAt')
        else:
            result = newsapi.get_everything(q=q, sources=source, from_param=fromdate, to=to, language='en', page_size=LIMIT, sort_by='publishedAt')
    except newsapi_exception.NewsAPIException as e:
        return {'status': 'error', 'message': e.get_message()}
    filtered_result = []
    for article in result['articles']:
        if checkEmpty(article) and len(filtered_result) < 15:
                filtered_result.append(article)
    return jsonify({'result': filtered_result})

# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    application.run()
