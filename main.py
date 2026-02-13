import os, dotenv
import time
from dotenv import load_dotenv
from supabase import create_client, Client
from fetcher import fetcher 
from classification import gemini_classify, ClassificationResponse
import email.utils
import schedule
from notify import send_line_broadcast

load_dotenv()
api_keys = [os.getenv(key) for key in os.environ if key.startswith("GEMINI_KEY")]
key_count = len(api_keys)
current_key_idx = -1
RETRY_LIMIT = 5

# 初始化 Supabase
url: str = os.environ.get("SUPABASE_URL") or ''
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or ''
supabase: Client = create_client(url, key)

def run_task():
    global current_key_idx
    print("--- 開始執行定時爬蟲任務 ---")
    
    # 1. 抓取最新公告
    fetched_items = fetcher()
    if not fetched_items:
        print("未抓取到任何公告")
        return

    # 2. 獲取資料庫中最新一筆公告的標題 (用來比對)
    response = supabase.table("announcements").select("post_id").order("publish_date", desc=True).limit(50).execute()
    existing_ids = [str(row['post_id']) for row in response.data] if response.data else []
    
    # 3. 找出新公告 (過濾掉已存在的 post_id)
    new_announcements = []
    for item in fetched_items:
        if str(item['post_id']) in existing_ids:
            # 假設 RSS 是按時間排的，遇到重複的就停止往後找
            break  
        new_announcements.append(item)
    
    if not new_announcements:
        print("沒有發現新公告。")
        return

    print(f"發現 {len(new_announcements)} 筆新公告！")

    for ann in reversed(new_announcements): # 從舊到新存入，確保時間順序
        print(f"處理公告：{ann['title']}, url: {ann['url']}")
        for attempt in range(RETRY_LIMIT):
            current_key_idx = (current_key_idx + 1) % key_count
            try:
                classification : ClassificationResponse = gemini_classify(ann.get('title'), ann.get('description', ""), api_key=api_keys[current_key_idx])
                break
            except Exception as e:
                print(f"分類失敗，嘗試次數 {attempt + 1}/{RETRY_LIMIT}，錯誤訊息：{e}")
                if "429" in str(e):
                    time.sleep(30)
                else:
                    time.sleep(8)
                continue
        else:
            classification = ClassificationResponse(category_id=-1, importance=-1, reason="分類失敗，超過重試次數")
        # 5. 寫入 Supabase
        data, count = supabase.table("announcements").insert({
            "title": ann['title'],
            "content": ann['description'],
            "category": classification.category_id,
            "importance": classification.importance,
            "reason": classification.reason,
            "publish_date": email.utils.parsedate_to_datetime(ann['published']).isoformat(),
            "link": ann['url'],
            "post_id": ann['post_id'],
            "division":ann['category']
        }).execute()
        print(f"已存入: {ann['title']}，分類結果: {classification}")
        if int(classification.importance) == 1:
            send_line_broadcast(ann['title'], ann['url'], ann['description'])
        time.sleep(5)
    else:
        print("所有新公告皆已處理完畢。")

schedule.every().hour.at(":00").do(run_task)
schedule.every().hour.at(":30").do(run_task)
print("公告分類服務已啟動，將每 30 分鐘檢查一次新公告...")
run_task()
while True:
    try:
        schedule.run_pending()
        time.sleep(1)
    except Exception as e:
        print(f"Error occurred: {e}")
