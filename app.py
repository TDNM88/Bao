from flask import Flask, render_template
import feedparser
from bs4 import BeautifulSoup
import requests
import schedule
import time
import threading
from datetime import datetime

app = Flask(__name__)

# Danh sách nguồn RSS thể thao tiếng Việt
RSS_FEEDS = [
    "https://vnexpress.net/rss/the-thao.rss",
    "https://thanhnien.vn/rss/the-thao.rss",
    "https://tuoitre.vn/rss/the-thao.rss"
]

# Lưu trữ bài viết tiêu điểm và bài viết mới
featured_articles = []
all_articles = []

def fetch_articles():
    global all_articles
    new_articles = []
    
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:  # Lấy 5 bài mới nhất từ mỗi nguồn
                title = entry.title
                link = entry.link
                pub_date = entry.published if 'published' in entry else 'N/A'
                
                # Lấy mô tả và hình ảnh từ nội dung bài viết
                response = requests.get(link)
                soup = BeautifulSoup(response.content, 'html.parser')
                description = soup.find('meta', {'name': 'description'})
                description = description['content'] if description else 'Không có mô tả'
                
                image = soup.find('meta', {'property': 'og:image'})
                image = image['content'] if image else 'https://via.placeholder.com/300'
                
                new_articles.append({
                    'title': title,
                    'link': link,
                    'description': description,
                    'image': image,
                    'pub_date': pub_date,
                    'source': feed.feed.title
                })
        except Exception as e:
            print(f"Lỗi khi lấy dữ liệu từ {feed_url}: {e}")
    
    all_articles = new_articles[:20]  # Giới hạn 20 bài mới nhất

def update_featured():
    global featured_articles, all_articles
    if all_articles:
        # Chọn bài mới nhất làm tiêu điểm
        featured_articles = [all_articles[0]]  # Lấy bài đầu tiên
        print(f"Cập nhật tiêu điểm: {featured_articles[0]['title']}")

# Lên lịch cập nhật bài viết mỗi 10 phút
def schedule_tasks():
    fetch_articles()  # Lấy bài ngay khi khởi động
    update_featured()  # Cập nhật tiêu điểm ban đầu
    
    schedule.every(10).minutes.do(fetch_articles)  # Cập nhật bài mới
    schedule.every(10).minutes.do(update_featured)  # Cập nhật tiêu điểm
    
    while True:
        schedule.run_pending()
        time.sleep(60)

# Chạy scheduler trong thread riêng
def start_scheduler():
    scheduler_thread = threading.Thread(target=schedule_tasks)
    scheduler_thread.daemon = True
    scheduler_thread.start()

@app.route('/')
def index():
    return render_template('index.html', featured=featured_articles, articles=all_articles)

if __name__ == '__main__':
    start_scheduler()
    app.run(debug=True)
