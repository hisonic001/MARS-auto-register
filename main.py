# main.py

import os
import pandas as pd
from playwright.sync_api import sync_playwright
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
    """
    엑셀의 한 행에서 '작업1_번호', '작업1_유형' 등 실제 컬럼명을 사용하여 DataFrame을 생성합니다.
    """
    sales_list = []
    # 엑셀 파일에 최대 10개까지의 품목이 있다고 가정하고 반복합니다.
    for i in range(1, 11):
        item_col = f'작업{i}_번호'
        
        # '작업{i}_번호' 컬럼에 값이 있는 경우에만 데이터를 추가합니다.
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
                    
                    print("📂 엑셀 파일(customers.xlsm)을 읽어옵니다...")
                    df = pd.read_excel(EXCEL_FILE, sheet_name="고객정보", engine="openpyxl", dtype=str).fillna('')
                    
                    for index, customer_row in df.iterrows():
                        customer_data = customer_row.to_dict()
                        if '날짜' in customer_data and customer_data['날짜']:
                            # Timestamp가 아닌 문자열로 읽혔을 수 있으므로 처리 방식을 단순화합니다.
                            pass
                        else:
                            customer_data['날짜'] = datetime.now().strftime('%Y-%m-%d')
                        
                        customer_name = customer_data.get('이름', '정보 없음')
                        print(f"\n======== 🚀 '{customer_name}' 고객 전체 프로세스 시작 ========")
                        
                        click_in_main_frame(page, role="button", name="고객 정보 검색", description="고객 정보 검색 메뉴 이동")
                        click_in_main_frame(page, role="menuitem", name="연락처/고객/차량을 생성합니다", description="고객 생성 폼 열기")
                        click_in_main_frame(page, role="button", name="코드, 오름차순 순서로 정렬됨 CASH-B2C", description="CASH-B2C 정렬 버튼", exact=True)
                        
                        customer_success = create_customer_and_vehicle(page, customer_data)
                        
                        if not customer_success:
                            print(f"-> ⚠️ '{customer_name}' 고객 생성 중 문제 발생. 다음 데이터로 넘어갑니다.")
                            continue
                        
                        sales_items_df = create_sales_df_from_row(customer_row)
                        
                        if sales_items_df.empty:
                            print(f"-> '{customer_name}' 고객의 판매 내역이 없어 다음으로 넘어갑니다.")
                            continue
                            
                        print("-> 생성된 판매 내역 데이터프레임:")
                        print(sales_items_df)
                        
                        sale_success = create_new_sale(page, customer_data)
                        
                        if sale_success:
                            # fill_sales_table은 page 객체만 필요로 합니다.
                            table_fill_success = fill_sales_table(page, sales_items_df)
                            if table_fill_success:
                                # post_sales_order는 page와 main_frame을 모두 필요로 합니다.
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