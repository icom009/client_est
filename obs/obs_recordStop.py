#!/usr/bin/env python
# coding: utf-8

# In[1]:


import obsws_python as obs

# WebSocket 설정
WEBSOCKET_HOST = "localhost"
WEBSOCKET_PORT = 4455
WEBSOCKET_PASSWORD = "gsD35D5WctVDY6lH"

def start_recording():
    """OBS WebSocket으로 녹화 시작"""
    try:
        # WebSocket 연결
        ws = obs.ReqClient(host=WEBSOCKET_HOST, port=WEBSOCKET_PORT, password=WEBSOCKET_PASSWORD, timeout=3)
        print("OBS WebSocket에 연결되었습니다.")

        # 녹화 시작
        ws.stop_record()
        print("녹화를 시작했습니다.")
        
        # WebSocket 연결 종료
        ws.disconnect()
        print("WebSocket 연결을 종료했습니다.")
    except Exception as e:
        print(f"녹화 시작 실패 또는 WebSocket 연결 오류: {e}")

if __name__ == "__main__":
    start_recording()


# In[ ]:




