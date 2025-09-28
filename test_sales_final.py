# test_sales_final.py

import os
import pandas as pd
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

from login import login, click_in_main_frame
from create_customer_and_vehicle import create_customer_and_vehicle 
from sales_handler import create_new_sale, fill_sales_table

load_dotenv(override=True)
my_id = os.environ.get("MARS_ID")
my_password = os.environ.get("MARS_PASSWORD")

if __name__ == "__main__":
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()

        if login(page, my_id, my_password):
            click_in_main_frame(page, role="button", name="확인", description="초기 팝업 닫기")
            print("\n--- ✅ 로그인 성공. 스크립트를 일시정지합니다. ---")
            print("--- 💡 이제 브라우저에서 직접 테스트할 고객 페이지로 이동해주세요. ---")
            print("--- 💡 준비가 되면, Playwright Inspector 창의 'Resume' 버튼(▶️)을 누르세요. ---")

            page.pause()

            print("\n--- ▶️ 스크립트 재개. 판매 내역 등록을 시작합니다. ---")
            
            sample_customer_data = {
                '주행거리': 44000,
                '날짜': '2025-08-07'
            }

            # --- 이 부분이 수정되었습니다 (3개 -> 10개) ---
            sales_items_list = [
                {'고객이름': '테스트고객', '유형': '상품', '번호': '015692', '수량': 2, '단가': 290400},
                {'고객이름': '테스트고객', '유형': '자원', '번호': 'S001/1220', '수량': 1, '단가': 33000},
                {'고객이름': '테스트고객', '유형': '상품', '번호': '000181', '수량': 4, '단가': 55000},
                {'고객이름': '테스트고객', '유형': '상품', '번호': '000207', '수량': 2, '단가': 642000},
                {'고객이름': '테스트고객', '유형': '자원', '번호': 'S000/0105', '수량': 1, '단가': 5000},
                {'고객이름': '테스트고객', '유형': '자원', '번호': 'S000/0114', '수량': 1, '단가': 5000},
                {'고객이름': '테스트고객', '유형': '상품', '번호': 'W7015', '수량': 1, '단가': 15200},
                {'고객이름': '테스트고객', '유형': '상품', '번호': 'W712/94', '수량': 1, '단가': 22200},
                {'고객이름': '테스트고객', '유형': '자원', '번호': 'S001/1217', '수량': 2, '단가': 55000},
                {'고객이름': '테스트고객', '유형': '상품', '번호': '000219', '수량': 2, '단가': 917000}
            ]
            # --- 수정 끝 ---

            sample_sales_df = pd.DataFrame(sales_items_list)

            success = create_new_sale(page, sample_customer_data)
            
            if success:
                main_frame = page.frame_locator("iframe[title=\"Main Content\"]")
                fill_sales_table(page, main_frame, sample_sales_df)

            print("\n--- 🧪 테스트 완료 ---")
            page.pause()
        
        browser.close()