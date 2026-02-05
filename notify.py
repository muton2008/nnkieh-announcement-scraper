import requests
import json
import os, dotenv
dotenv.load_dotenv()

def send_line_broadcast(title, link, description):
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    # 這裡抓取所有 target ID
    target_ids = [os.getenv(k) for k in os.environ if k.startswith("LINE_TARGET_ID_")]
    
    if not token or not target_ids:
        print("⚠️ 缺少配置，無法發送 LINE 訊息")
        return

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    short_description = description[:150] + "..." if len(description) > 150 else description

    flex_message_content = {
        "type": "flex",
        "altText": f"校園公告：{title}",
        "contents": {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text", 
                        "text": "School Notification", 
                        "size": "xs", 
                        "color": "#FFFFFFB3",
                        "weight": "bold"
                    },
                    {
                        "type": "text", 
                        "text": "南科實中公告", 
                        "weight": "bold", 
                        "size": "lg", 
                        "color": "#FFFFFF"
                    }
                ],
                "backgroundColor": "#6B8E23",
                "paddingAll": "15px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text", 
                        "text": title, 
                        "weight": "bold", 
                        "size": "md", 
                        "wrap": True, 
                        "color": "#444444"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "lg",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "text",
                                "text": short_description,
                                "size": "sm",
                                "color": "#777777",
                                "wrap": True,
                                "maxLines": 4
                            }
                        ]
                    }
                ],
                "paddingAll": "15px",
                "backgroundColor": "#FAFAFA"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "uri", 
                            "label": "查看詳細內容", 
                            "uri": link
                        },
                        "style": "link", #primary
                        "height": "sm",
                        "color": "#6B8E23"
                    }
                ],
                "paddingAll": "5px"
            }
        }
    }

    for target_id in target_ids:
        url = "https://api.line.me/v2/bot/message/push"
        single_target_payload = {
            "to": target_id,
            "messages": [flex_message_content]
        }

        try:
            response = requests.post(url, headers=headers, json=single_target_payload, timeout=10)
            if response.status_code == 200:
                print(f"✅ 成功發送 {title[:25]} 至 ID: {target_id}")
            else:
                print(f"❌ Flex Message 發送失敗 ({target_id}): {response.text}")
        except Exception as e:
            print(f"❌ Flex Message 連線 ID {target_id} 時發生異常: {e}")
if __name__ == "__main__":
    # 測試用範例
    send_line_broadcast("測試公告標題", "https://example.com/announcement/123", "這是一個測試理由") 