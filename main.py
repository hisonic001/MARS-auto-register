import os
import pandas as pd
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

from login import login, click_in_main_frame
from create_customer_and_vehicle import create_customer_and_vehicle
from sales_handler import create_new_sale, fill_sales_table
from posting_sales_handler import post_sales_order

# .env 파일에서 환경 변수 읽어오기
load_dotenv(override=True)
my_id = os.environ.get("MARS_ID")
my_password = os.environ.get("MARS_PASSWORD")

if __name__ == "__main__":
    if not my_id or not my_password:
        print("⚠️ MARS_ID 또는 MARS_PASSWORD 환경 변수가 설정되지 않았습니다.")
    else:
        browser = None
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=False)
                page = browser.new_page()

                if login(page, my_id, my_password):
                    click_in_main_frame(page, role="button", name="확인", description="초기 팝업 닫기")
                    
                    print("📂 엑셀 파일들을 읽어옵니다...")
                    # 고객 정보 파일과 판매 내역 파일을 각각 읽어옵니다.
                    customers_df = pd.read_excel("customers.xlsm", sheet_name="고객정보").fillna('')
                    sales_df = pd.read_excel("sales_table.xlsx").fillna('') # 판매 내역 파일 이름

                    # 고객 정보 파일을 한 줄씩 처리합니다.
                    for index, customer_row in customers_df.iterrows():
                        customer_data = customer_row.to_dict()
                        customer_name = customer_data.get('이름', '정보 없음')
                        print(f"\n======== 🚀 '{customer_name}' 고객 전체 프로세스 시작 ========")

                        # 1. 고객 생성 페이지로 이동
                        click_in_main_frame(page, role="button", name="고객 정보 검색", description="고객 정보 검색 메뉴 이동")
                        click_in_main_frame(page, role="menuitem", name="연락처/고객/차량을 생성합니다", description="고객 생성 폼 열기")
                        click_in_main_frame(page, role="button", name="코드, 오름차순 순서로 정렬됨 CASH-B2C", description="CASH-B2C 정렬 버튼", exact=True)
                        
                        # 2. 고객 및 차량 정보 생성
                        customer_success = create_customer_and_vehicle(page, customer_data)
                        
                        if not customer_success:
                            print(f"-> ⚠️ '{customer_name}' 고객 생성 중 문제 발생. 다음 데이터로 넘어갑니다.")
                            continue
                        
                        # 3. 현재 고객의 판매 내역만 필터링
                        customer_sales_items = sales_df[sales_df['고객이름'] == customer_name].reset_index(drop=True)

                        if customer_sales_items.empty:
                            print(f"-> '{customer_name}' 고객의 판매 내역이 없어 다음으로 넘어갑니다.")
                            continue

                        # 4. 판매 내역 생성 페이지로 이동 및 표 채우기
                        sale_success = create_new_sale(page, customer_data)
                        if sale_success:
                            main_frame = page.frame_locator("iframe[title=\"Main Content\"]")
                            table_fill_success = fill_sales_table(page, main_frame, customer_sales_items)

                            # 5. 표 채우기가 성공하면 '전기' 프로세스 시작
                            if table_fill_success:
                                print("-> 판매 내역 입력 완료. '전기'를 시작합니다.")
                                post_success = post_sales_order(page, main_frame)
                                if not post_success:
                                    print(f"-> ⚠️ '{customer_name}' 고객의 전기 처리 중 문제 발생.")
                        
                        print(f"======== ✅ '{customer_name}' 고객 전체 프로세스 완료 ========")

                    print("\n🎉 모든 고객 데이터 처리를 완료했습니다!")
                    page.pause()

        except Exception as e:
            print(f"❌ 스크립트 실행 중 예외가 발생했습니다: {e}")
        finally:
            if browser:
                print("브라우저를 닫습니다.")
                browser.close()