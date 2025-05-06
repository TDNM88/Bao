from flask import Flask, render_template, request, redirect, url_for, flash, session
import feedparser
from bs4 import BeautifulSoup
import requests
import schedule
import time
import threading
from datetime import datetime
import json
import os
import random
import openrouter  # Hypothetical OpenRouter client library

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a secure key

# Danh sách nguồn RSS thể thao tiếng Việt
RSS_FEEDS = [
    "https://vnexpress.net/rss/the-thao.rss",
    "https://thanhnien.vn/rss/the-thao.rss",
    "https://tuoitre.vn/rss/the-thao.rss"
]

# SEO Configuration file
SEO_CONFIG_FILE = 'seo_config.json'

# Default SEO settings
DEFAULT_SEO_CONFIG = {
    "keywords": ["thể thao", "bóng đá", "bóng rổ", "Việt Nam", "quốc tế"],
    "title_length": {"min": 50, "max": 60},
    "description_length": {"min": 120, "max": 160},
    "content_headings": True,
    "keyword_density": 0.02  # 2% keyword density
}

# Initialize SEO config
if not os.path.exists(SEO_CONFIG_FILE):
    with open(SEO_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(DEFAULT_SEO_CONFIG, f, ensure_ascii=False, indent=4)

# Load SEO config
def load_seo_config():
    with open(SEO_CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

# Save SEO config
def save_seo_config(config):
    with open(SEO_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

# OpenRouter API setup (hypothetical)
openrouter.api_key = 'your-openrouter-api-key'  # Replace with actual API key

def optimize_for_seo(article):
    seo_config = load_seo_config()
    keywords = seo_config['keywords']
    prompt = f"""
    Rewrite the following article to be SEO-friendly based on these rules:
    - Include keywords: {', '.join(keywords)}
    - Title length: {seo_config['title_length']['min']}-{seo_config['title_length']['max']} characters
    - Description length: {seo_config['description_length']['min']}-{seo_config['description_length']['max']} characters
    - Add headings (H2, H3) if enabled: {seo_config['content_headings']}
    - Maintain keyword density: {seo_config['keyword_density']*100}%
    - Keep the tone professional and engaging
    - Preserve the original meaning and facts

    Title: {article['title']}
    Description: {article['description']}
    Content: {article['content']}
    """

    try:
        response = openrouter.Completion.create(
            model="meta-llama/llama-4-maverick:free",
            prompt=prompt,
            max_tokens=1500
        )
        optimized_content = response.choices[0].text.strip()
        # Parse response (assuming it returns structured text with delimiters)
        sections = optimized_content.split('---')
        if len(sections) >= 3:
            article['title'] = sections[0].strip()
            article['description'] = sections[1].strip()
            article['content'] = sections[2].strip()
        return article
    except Exception as e:
        print(f"Error optimizing article {article['title']}: {e}")
        return article

# Dữ liệu mẫu (unchanged, included for context)
SAMPLE_ARTICLES = [...]  # Keep existing SAMPLE_ARTICLES
FOOTBALL_ARTICLES = [...]  # Keep existing FOOTBALL_ARTICLES
BASKETBALL_ARTICLES = [...]  # Keep existing BASKETBALL_ARTICLES
OTHER_SPORTS_ARTICLES = [...]  # Keep existing OTHER_SPORTS_ARTICLES
INTERNATIONAL_ARTICLES = [...]  # Keep existing INTERNATIONAL_ARTICLES

# Lưu trữ bài viết tiêu điểm và bài viết mới
featured_articles = []
all_articles = []

# Tạo ID duy nhất cho mỗi bài viết
def generate_id():
    return str(random.randint(1000, 9999))

def fetch_articles():
    global all_articles
    new_articles = []
    
    if not all_articles:
        all_articles = SAMPLE_ARTICLES.copy()
    
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:3]:
                title = entry.title
                link = entry.link
                pub_date = entry.published if 'published' in entry else datetime.now().strftime('%d/%m/%Y')
                
                if any(article['title'] == title for article in all_articles):
                    continue
                
                try:
                    response = requests.get(link, timeout=5)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    description = soup.find('meta', {'name': 'description'})
                    if not description:
                        description = soup.find('meta', {'property': 'og:description'})
                    description = description['content'] if description else 'Không có mô tả'
                    
                    image = soup.find('meta', {'property': 'og:image'})
                    if not image:
                        image = soup.find('meta', {'name': 'twitter:image'})
                    image = image['content'] if image else 'https://via.placeholder.com/300'
                    
                    content_div = None
                    for selector in ['.fck_detail', '.article-content', '.cms-body', '.article-body']:
                        content_div = soup.select_one(selector)
                        if content_div:
                            break
                    
                    content = content_div.get_text(strip=True) if content_div else description
                    
                    category = 'football'
                    if any(keyword in title.lower() for keyword in ['bóng rổ', 'nba', 'basketball']):
                        category = 'basketball'
                    elif any(keyword in title.lower() for keyword in ['quần vợt', 'tennis', 'cầu lông', 'bơi lội', 'điền kinh']):
                        category = 'other'
                    elif any(keyword in title.lower() for keyword in ['world cup', 'olympic', 'thế giới', 'quốc tế']):
                        category = 'international'
                    
                    article_id = generate_id()
                    article = {
                        'id': article_id,
                        'title': title,
                        'link': link,
                        'description': description[:200] + '...' if len(description) > 200 else description,
                        'image': image,
                        'pub_date': pub_date,
                        'source': feed.feed.title,
                        'content': content,
                        'category': category
                    }
                    # Optimize article for SEO
                    article = optimize_for_seo(article)
                    new_articles.append(article)
                except Exception as e:
                    print(f"Lỗi khi xử lý bài viết {title}: {e}")
        except Exception as e:
            print(f"Lỗi khi lấy dữ liệu từ {feed_url}: {e}")
    
    all_articles = new_articles + all_articles
    all_articles = all_articles[:30]
    
    try:
        with open('articles.json', 'w', encoding='utf-8') as f:
            json.dump(all_articles, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Lỗi khi lưu bài viết: {e}")

def update_featured():
    global featured_articles, all_articles
    if all_articles:
        featured_articles = all_articles[:3]
        print(f"Cập nhật tiêu điểm: {featured_articles[0]['title']}")

def schedule_tasks():
    global all_articles
    try:
        if os.path.exists('articles.json'):
            with open('articles.json', 'r', encoding='utf-8') as f:
                all_articles = json.load(f)
    except Exception as e:
        print(f"Lỗi khi đọc file articles.json: {e}")
    
    if not all_articles:
        all_articles = SAMPLE_ARTICLES.copy()
    
    update_featured()
    
    schedule.every(10).minutes.do(fetch_articles)
    schedule.every(10).minutes.do(update_featured)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

def start_scheduler():
    scheduler_thread = threading.Thread(target=schedule_tasks)
    scheduler_thread.daemon = True
    scheduler_thread.start()

# Admin Authentication Middleware
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session:
            flash('Vui lòng đăng nhập để truy cập trang quản trị.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        # Replace with a secure authentication mechanism
        if password == 'admin123':  # Hardcoded for simplicity
            session['admin'] = True
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Mật khẩu không đúng.', 'error')
    return render_template('login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    flash('Đã đăng xuất.', 'success')
    return redirect(url_for('index'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    seo_config = load_seo_config()
    return render_template('admin.html', articles=all_articles, rss_feeds=RSS_FEEDS, seo_config=seo_config)

@app.route('/admin/article/add', methods=['GET', 'POST'])
@admin_required
def add_article():
    if request.method == 'POST':
        article = {
            'id': generate_id(),
            'title': request.form.get('title'),
            'link': request.form.get('link'),
            'description': request.form.get('description'),
            'image': request.form.get('image'),
            'pub_date': request.form.get('pub_date') or datetime.now().strftime('%d/%m/%Y'),
            'source': request.form.get('source'),
            'content': request.form.get('content'),
            'category': request.form.get('category')
        }
        article = optimize_for_seo(article)
        all_articles.insert(0, article)
        with open('articles.json', 'w', encoding='utf-8') as f:
            json.dump(all_articles, f, ensure_ascii=False, indent=4)
        flash('Thêm bài viết thành công!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin.html', action='add_article')

@app.route('/admin/article/edit/<article_id>', methods=['GET', 'POST'])
@admin_required
def edit_article(article_id):
    article = next((a for a in all_articles if a['id'] == article_id), None)
    if not article:
        flash('Bài viết không tồn tại.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        article['title'] = request.form.get('title')
        article['link'] = request.form.get('link')
        article['description'] = request.form.get('description')
        article['image'] = request.form.get('image')
        article['pub_date'] = request.form.get('pub_date')
        article['source'] = request.form.get('source')
        article['content'] = request.form.get('content')
        article['category'] = request.form.get('category')
        article = optimize_for_seo(article)
        with open('articles.json', 'w', encoding='utf-8') as f:
            json.dump(all_articles, f, ensure_ascii=False, indent=4)
        flash('Sửa bài viết thành công!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin.html', action='edit_article', article=article)

@app.route('/admin/article/delete/<article_id>')
@admin_required
def delete_article(article_id):
    global all_articles
    all_articles = [a for a in all_articles if a['id'] != article_id]
    with open('articles.json', 'w', encoding='utf-8') as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=4)
    flash('Xóa bài viết thành công!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/rss/add', methods=['POST'])
@admin_required
def add_rss_feed():
    rss_url = request.form.get('rss_url')
    if rss_url and rss_url not in RSS_FEEDS:
        RSS_FEEDS.append(rss_url)
        flash('Thêm nguồn RSS thành công!', 'success')
    else:
        flash('Nguồn RSS đã tồn tại hoặc không hợp lệ.', 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/rss/delete/<path:rss_url>')
@admin_required
def delete_rss_feed(rss_url):
    if rss_url in RSS_FEEDS:
        RSS_FEEDS.remove(rss_url)
        flash('Xóa nguồn RSS thành công!', 'success')
    else:
        flash('Nguồn RSS không tồn tại.', 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/seo', methods=['GET', 'POST'])
@admin_required
def update_seo_config():
    if request.method == 'POST':
        seo_config = {
            "keywords": request.form.get('keywords').split(','),
            "title_length": {
                "min": int(request.form.get('title_min', 50)),
                "max": int(request.form.get('title_max', 60))
            },
            "description_length": {
                "min": int(request.form.get('description_min', 120)),
                "max": int(request.form.get('description_max', 160))
            },
            "content_headings": request.form.get('content_headings') == 'on',
            "keyword_density": float(request.form.get('keyword_density', 0.02))
        }
        save_seo_config(seo_config)
        flash('Cập nhật cài đặt SEO thành công!', 'success')
        return redirect(url_for('admin_dashboard'))
    seo_config = load_seo_config()
    return render_template('admin.html', action='seo_config', seo_config=seo_config)

# Existing routes (unchanged)
@app.route('/')
def index():
    return render_template('index.html', featured=featured_articles, articles=all_articles)

@app.route('/football')
def football():
    football_articles = [article for article in all_articles if article.get('category') == 'football']
    if len(football_articles) < 6:
        football_articles = football_articles + [article for article in FOOTBALL_ARTICLES if article['id'] not in [a['id'] for a in football_articles]]
    return render_template('category.html', 
                          category_name="Bóng đá", 
                          featured=football_articles[:3], 
                          articles=football_articles, 
                          icon="fas fa-futbol")

@app.route('/basketball')
def basketball():
    basketball_articles = [article for article in all_articles if article.get('category') == 'basketball']
    if len(basketball_articles) < 6:
        basketball_articles = basketball_articles + [article for article in BASKETBALL_ARTICLES if article['id'] not in [a['id'] for a in basketball_articles]]
    return render_template('category.html', 
                          category_name="Bóng rổ", 
                          featured=basketball_articles[:3], 
                          articles=basketball_articles, 
                          icon="fas fa-basketball-ball")

@app.route('/other')
def other_sports():
    other_articles = [article for article in all_articles if article.get('category') == 'other']
    if len(other_articles) < 6:
        other_articles = other_articles + [article for article in OTHER_SPORTS_ARTICLES if article['id'] not in [a['id'] for a in other_articles]]
    return render_template('category.html', 
                          category_name="Thể thao khác", 
                          featured=other_articles[:3], 
                          articles=other_articles, 
                          icon="fas fa-table-tennis")

@app.route('/international')
def international():
    international_articles = [article for article in all_articles if article.get('category') == 'international']
    if len(international_articles) < 6:
        international_articles = international_articles + [article for article in INTERNATIONAL_ARTICLES if article['id'] not in [a['id'] for a in international_articles]]
    return render_template('category.html', 
                          category_name="Quốc tế", 
                          featured=international_articles[:3], 
                          articles=international_articles, 
                          icon="fas fa-globe")

@app.route('/article/<article_id>')
def article_detail(article_id):
    article = next((article for article in all_articles if article['id'] == article_id), None)
    if not article:
        for article_list in [FOOTBALL_ARTICLES, BASKETBALL_ARTICLES, OTHER_SPORTS_ARTICLES, INTERNATIONAL_ARTICLES]:
            article = next((article for article in article_list if article['id'] == article_id), None)
            if article:
                break
    
    if not article:
        return redirect(url_for('index'))
    
    category = article.get('category', 'football')
    related_articles = [a for a in all_articles if a.get('category') == category and a['id'] != article_id][:3]
    
    if len(related_articles) < 3:
        if category == 'football':
            sample_list = FOOTBALL_ARTICLES
        elif category == 'basketball':
            sample_list = BASKETBALL_ARTICLES
        elif category == 'other':
            sample_list = OTHER_SPORTS_ARTICLES
        else:
            sample_list = INTERNATIONAL_ARTICLES
            
        for a in sample_list:
            if a['id'] != article_id and a['id'] not in [r['id'] for r in related_articles]:
                related_articles.append(a)
                if len(related_articles) >= 3:
                    break
    
    return render_template('article.html', article=article, related=related_articles)

@app.route('/search')
def search():
    query = request.args.get('q', '').lower()
    if not query:
        return redirect(url_for('index'))
    
    results = [article for article in all_articles if query in article['title'].lower() or query in article['description'].lower()]
    
    if not results:
        for article_list in [FOOTBALL_ARTICLES, BASKETBALL_ARTICLES, OTHER_SPORTS_ARTICLES, INTERNATIONAL_ARTICLES]:
            for article in article_list:
                if query in article['title'].lower() or query in article['description'].lower():
                    if article['id'] not in [r['id'] for r in results]:
                        results.append(article)
    
    return render_template('search.html', results=results, query=query)

if __name__ == '__main__':
    start_scheduler()
    app.run(debug=True)
