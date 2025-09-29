# test_sales_handler_with_login.py

import os
import pandas as pd
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# 테스트에 필요한 모든 함수를 가져옵니다.
from login import login
from sales_handler import create_new_sale, fill_sales_table
from posting_sales_handler import post_sales_order

# --- 설정 ---
load_dotenv(override=True)
my_id = os.environ.get("MARS_ID")
my_password = os.environ.get("MARS_PASSWORD")


if __name__ == "__main__":
    # --- 테스트를 위한 고정 데이터 ---
    # 실제 엑셀 파일에서 테스트하고 싶은 고객 데이터 한 줄을 여기에 붙여넣으세요.
    test_customer_data = {
        '이름': '이현숙',
        '주행거리': 720000,
        '날짜': '2025-09-29' # 날짜는 YYYY-MM-DD 형식으로
    }
    test_sales_items_list = [
        {'유형': '상품', '번호': '000207', '수량': 4, '단가': 642000},
        {'유형': '상품', '번호': '200111', '수량': 2, '단가': 20000},
        {'유형': '자원', '번호': 'S001/1150', '수량': 1, '단가': 40000},
        {'유형': '자원', '번호': 'S001/1181', '수량': 1, '단가': 40000}

    ]
    test_sales_df = pd.DataFrame(test_sales_items_list)
    # --- 테스트 데이터 끝 ---

    browser = None
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            page.set_default_timeout(30000)

            # 1. 로그인 실행
            if login(page, my_id, my_password):
                
                # 2. 로그인 직후 스크립트 일시정지
                print("\n" + "="*50)
                print("--- 🛑 로그인 성공! 스크립트를 일시정지합니다. ---")
                print("--- 💡 브라우저에서 직접 테스트하고 싶은 고객을 찾아서 [고객 상세 정보 페이지]로 이동해주세요.")
                print("--- 💡 페이지 준비가 완료되면, Playwright Inspector 창의 'Resume(▶️)' 버튼을 누르세요.")
                print("="*50 + "\n")
                page.pause() # <<-- 여기서 멈춥니다!

                # 3. 사용자가 Resume을 누르면, 여기부터 코드가 다시 실행됩니다.
                print("\n▶️ 스크립트를 다시 시작합니다. 판매 내역 입력을 테스트합니다...")

                # 4. 문제가 되는 판매 내역 관련 함수들을 순서대로 호출
                sale_success = create_new_sale(page, test_customer_data)
                
                if sale_success:
                    main_frame = page.frame_locator("iframe[title=\"Main Content\"]")
                    table_fill_success = fill_sales_table(page, test_sales_df)
                    if table_fill_success:
                        # 판매 전표 발행까지 테스트하려면 아래 주석을 해제하세요.
                        # post_sales_order(page, main_frame)
                        pass

                print("\n테스트 완료. 최종 확인을 위해 브라우저를 다시 일시정지합니다.")
                page.pause()

    except Exception as e:
        print(f"❌ 테스트 실행 중 예외가 발생했습니다: {e}")
    finally:
        if browser:
            print("브라우저를 닫습니다.")
            browser.close()