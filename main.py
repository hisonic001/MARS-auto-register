import os
import pandas as pd
from playwright.sync_api import sync_playwright
from login import login, click_in_main_frame
from create_customer_and_vehicle import create_customer_and_vehicle 

my_id = os.environ.get("MARS_ID")
my_password = os.environ.get("MARS_PASSWORD")

if __name__ == "__main__":
    if not my_id or not my_password:
        print("환경 변수가 설정되지 않았습니다.")
    else:
        browser = None
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=False)
                page = browser.new_page()

                if login(page, my_id, my_password):
                    click_in_main_frame(page, role="button", name="확인", description="초기 팝업 닫기")
                    
                    print("📂 엑셀 파일에서 고객 데이터를 읽어옵니다...")
                    # dtype 옵션으로 '휴대폰 번호'를 문자열로 읽어옵니다.
                    df = pd.read_excel("customers.xlsx", dtype={'휴대폰 번호': str}).fillna('')

                    for index, row in df.iterrows():
                        # --- 루프 시작 시 항상 동일한 시작 페이지에 있는지 확인하고 이동 ---
                        click_in_main_frame(page, role="button", name="고객 정보 검색", description="고객 정보 검색 메뉴 이동")
                        click_in_main_frame(page, role="menuitem", name="연락처/고객/차량을 생성합니다", description="고객 생성 폼 열기")
                        click_in_main_frame(page, role="button", name="코드, 오름차순 순서로 정렬됨 CASH-B2C", description="CASH-B2C 정렬 버튼", exact=True)
                        # -----------------------------------------------------------------
                        
                        # create_customer_and_vehicle.py에서 가져온 통합 함수를 호출합니다.
                        success = create_customer_and_vehicle(page, row.to_dict())
                        
                        if not success:
                            print(f"-> '{row.get('이름', '')}' 처리 중 문제가 있어 다음 데이터로 넘어갑니다.")
                            continue
                        
                        print(f"--- '{row.get('이름') or '김고객'}' 고객의 모든 정보 처리 완료 ---")

                    print("🎉 모든 고객 데이터 처리를 완료했습니다!")
                    page.pause()

        except Exception as e:
            print(f"❌ 스크립트 실행 중 오류가 발생했습니다: {e}")
        finally:
            if browser:
                print("브라우저를 닫습니다.")
                browser.close()
