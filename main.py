import os
import time
from dotenv import load_dotenv
from supabase import create_client, Client
from fetcher import fetcher 
from classification import gemini_classify, ClassificationResponse
import email.utils

load_dotenv()

# 初始化 Supabase
url: str = os.environ.get("SUPABASE_URL") or ''
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or ''
supabase: Client = create_client(url, key)

def run_task():
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
        classification : ClassificationResponse = gemini_classify(ann.get('title'), ann.get('description', ""))
        
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
        }).execute()
        print(f"已存入: {ann['title']}，分類結果: {classification}")
        time.sleep(5)

# 定時任務邏輯
if __name__ == "__main__":
    while True:
        run_task()
        
        print("等待 30 分鐘後再次執行...")
        time.sleep(1800) # 30分鐘 = 1800秒