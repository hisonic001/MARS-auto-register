# main.py

import os
import re
import pandas as pd
from playwright.sync_api import sync_playwright, expect, TimeoutError
from dotenv import load_dotenv
from datetime import datetime

# 각 모듈에서 필요한 함수들을 모두 가져옵니다.
from login import login, click_in_main_frame
from create_customer_and_vehicle import create_customer_and_vehicle
from sales_handler import create_new_sale, fill_sales_table
from posting_sales_handler import post_sales_order

# --- 설정 ---
load_dotenv(override=True)
my_id = os.environ.get("MARS_ID")
my_password = os.environ.get("MARS_PASSWORD")
SITE_URL = "https://mars.tyremore.co.kr/MARS/"
EXCEL_FILE = 'customers.xlsm'

def create_sales_df_from_row(customer_row: pd.Series) -> pd.DataFrame:
    sales_list = []
    for i in range(1, 11):
        item_col = f'작업{i}_번호'
        if item_col in customer_row and pd.notna(customer_row[item_col]) and customer_row[item_col] != '':
            sales_list.append({
                '유형': customer_row.get(f'작업{i}_유형', '상품'),
                '번호': customer_row[item_col],
                '수량': customer_row.get(f'작업{i}_수량', 1),
                '단가': customer_row.get(f'작업{i}_단가', 0)
            })
    return pd.DataFrame(sales_list)

if __name__ == "__main__":
    if not my_id or not my_password:
        print("⚠️ MARS_ID 또는 MARS_PASSWORD 환경 변수가 설정되지 않았습니다.")
    else:
        browser = None
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=False)
                context = browser.new_context()
                page = context.new_page()
                page.set_default_timeout(30000)

                if login(page, my_id, my_password):
                    click_in_main_frame(page, role="button", name="확인", description="초기 팝업 닫기")
                    
                    df = pd.read_excel(EXCEL_FILE, sheet_name="고객정보", engine="openpyxl", dtype=str).fillna('')
                    
                    for index, customer_row in df.iterrows():
                        customer_data = customer_row.to_dict()
                        if '날짜' in customer_data and customer_data['날짜']:
                            pass
                        else:
                            customer_data['날짜'] = datetime.now().strftime('%Y-%m-%d')
                        
                        customer_name = customer_data.get('이름')
                        license_plate = customer_data.get('번호판 번호')
                        print(f"\n======== 🚀 '{customer_name}' ({license_plate}) 고객 전체 프로세스 시작 ========")
                        
                        click_in_main_frame(page, role="button", name="고객 정보 검색", description="고객 정보 검색 메뉴 이동")
                        
                        # --- ▼▼▼▼▼ 최종 로직 수정 ▼▼▼▼▼ ---
                        print(f"-> 번호판 '{license_plate}'으로 기존 고객인지 검색합니다...")
                        main_frame = page.frame_locator("iframe[title=\"Main Content\"]")
                        customer_already_exists = False
                        customer_success = False

                        try:
                            search_box = main_frame.get_by_role("textbox", name="이름/번호판 번호")
                            expect(search_box).to_be_visible(timeout=5000)
                            search_box.fill(license_plate)
                            search_box.press("Enter")
                            print(f"  - 검색 실행 완료. 결과 렌더링을 기다립니다...")
                            page.wait_for_timeout(3000) # 검색 결과가 렌더링될 시간을 충분히 줍니다.

                            # [핵심 수정] '(결과 없음)' 메시지가 보이는지만으로 판단합니다.
                            not_found_locator = main_frame.get_by_text("(이 보기에 표시할 내용이 없음)", exact=True)

                            if not_found_locator.is_visible():
                                print("-> 검색 결과: '(결과 없음)' 메시지가 표시됨. 신규 고객입니다.")
                                customer_already_exists = False
                            else:
                                print("-> 검색 결과: '(결과 없음)' 메시지가 없음. 이미 등록된 고객입니다.")
                                customer_already_exists = True
                        
                        except Exception as e:
                            print(f"⚠️ 번호판 검색 중 오류 발생: {e}. 신규 고객으로 간주하고 진행합니다.")
                            customer_already_exists = False

                        # 분기 처리
                        if not customer_already_exists:
                            print("-> 신규 고객 생성 절차를 시작합니다.")
                            click_in_main_frame(page, role="menuitem", name="연락처/고객/차량을 생성합니다", description="고객 생성 폼 열기")
                            click_in_main_frame(page, role="button", name="코드, 오름차순 순서로 정렬됨 CASH-B2C", description="CASH-B2C 정렬 버튼", exact=True)
                            customer_success = create_customer_and_vehicle(page, customer_data)
                        else:
                            try:
                                print("-> 등록된 고객 페이지로 자동 이동되었습니다. 다음 단계 준비를 위해 대기합니다...")
                                expect(main_frame.get_by_role("menuitem", name="판매 내역")).to_be_visible(timeout=10000)
                                print("✅ 고객 상세 페이지가 준비되었습니다.")
                                customer_success = True
                            except Exception as e:
                                print(f"⚠️ 등록된 고객 페이지로 이동 후 대기 중 오류 발생: {e}. 이 고객 데이터를 건너뜁니다.")
                                customer_success = False
                        # --- ▲▲▲▲▲ 최종 로직 수정 끝 ▲▲▲▲▲ ---

                        if not customer_success:
                            print(f"-> ⚠️ '{customer_name}' 고객 처리 중 문제 발생. 다음 데이터로 넘어갑니다.")
                            page.goto(SITE_URL)
                            continue
                        
                        sales_items_df = create_sales_df_from_row(customer_row)
                        
                        if sales_items_df.empty:
                            print(f"-> '{customer_name}' 고객의 판매 내역이 없어 다음으로 넘어갑니다.")
                            if customer_already_exists:
                                print(f"======== ✅ '{customer_name}' 고객 프로세스 완료 (신규 판매 없음) ========")
                                continue
                            
                        print("-> 생성된 판매 내역 데이터프레임:")
                        print(sales_items_df)
                        
                        sale_success = create_new_sale(page, customer_data)
                        
                        if sale_success:
                            table_fill_success = fill_sales_table(page, sales_items_df)
                            if table_fill_success:
                                main_frame = page.frame_locator("iframe[title=\"Main Content\"]")
                                post_sales_order(page, main_frame)
                        
                        print(f"======== ✅ '{customer_name}' 고객 전체 프로세스 완료 ========")

                    print("\n🎉 모든 고객 데이터 처리를 완료했습니다!")
                    page.pause()
        except Exception as e:
            print(f"❌ 스크립트 실행 중 예외가 발생했습니다: {e}")
        finally:
            if browser:
                print("브라우저를 닫습니다.")
                browser.close()