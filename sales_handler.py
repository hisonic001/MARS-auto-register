# sales_handler.py

import datetime
from playwright.sync_api import expect, TimeoutError

def create_new_sale(page, sales_data):
    """
    판매 내역 양식으로 이동하고, 주행거리/날짜 등 기본 정보를 먼저 입력합니다.
    """
    print("🚀 신규 판매 내역 등록을 시작합니다...")
    try:
        main_frame = page.frame_locator("iframe[title=\"Main Content\"]")
        
        main_frame.get_by_role("menuitem", name="판매 내역").click()
        new_sale_button = main_frame.get_by_role("menuitem", name="신규")
        expect(new_sale_button).to_be_visible(timeout=5000)
        new_sale_button.click()
        new_sales_order_button = main_frame.get_by_role("menuitem", name="신규 매출 주문")
        expect(new_sales_order_button).to_be_visible(timeout=5000)
        new_sales_order_button.click()
        print("✅ 신규 판매 내역 양식을 성공적으로 열었습니다.")

        try:
            more_button = main_frame.get_by_role("button", name="일반, 더 보기")
            more_button.click(timeout=2000)
            print("-> '더 보기' 버튼을 클릭하여 추가 정보를 표시합니다.")
            page.wait_for_timeout(500)
        except TimeoutError:
            print("-> '더 보기' 버튼이 없거나 이미 확장된 상태입니다.")

        mileage_field = main_frame.get_by_role("textbox", name="현재 주행거리")
        mileage_field.wait_for(state="visible", timeout=5000)
        print("-> 주행거리 및 날짜 정보를 입력합니다...")
        
        current_mileage = sales_data.get('주행거리')
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        document_date = sales_data.get('날짜') or today_str
        
        if current_mileage:
            mileage_field.fill(str(current_mileage))
        
        main_frame.get_by_role("combobox", name="문서 날짜").fill(str(document_date))
        main_frame.get_by_role("combobox", name="완료 일자").fill(str(document_date))
        
        print("✅ 주행거리 및 날짜 정보 입력 완료.")
        return True
        
    except Exception as e:
        print(f"⚠️ 판매 내역 기본 정보 입력 중 오류 발생: {e}")
        page.pause()
        return False

# sales_handler.py

def fill_sales_table(page, main_frame, sales_items_df):
    """
    자동 완성 대기 없이, 엑셀 데이터로 모든 값을 직접 입력하는 최종 버전
    """
    print("-> 판매 내역 표에 작업 내용을 입력합니다...")
    try:
        grid = main_frame.locator("#bxh").get_by_role("grid")
        js_code = "(element, value) => { element.value = value; element.dispatchEvent(new Event('change', { bubbles: true })); }"

        expect(grid.locator("tr.real-current")).to_be_visible(timeout=10000)
        print("-> 표가 입력 가능한 상태입니다.")

        for index, item_row in sales_items_df.iterrows():
            print(f"-> {index + 1}번째 작업 아이템을 처리합니다...")

            if index > 0:
                print(f"  - {index + 1}번째 행을 활성화하기 위해 행 머리글을 클릭합니다...")
                main_frame.get_by_role("rowheader").nth(index).click()
                page.wait_for_timeout(500)

            current_row = grid.locator("tr.real-current")
            current_row.scroll_into_view_if_needed()
            
            work_type = item_row.get("유형")
            work_number = item_row.get("번호")
            work_qty = item_row.get("수량")
            work_price = item_row.get("단가")
            
            # 1. 유형 선택
            current_row.get_by_role("combobox", name="유형").select_option(label=work_type)
            print(f"  - 유형: '{work_type}' 선택")

            # 2. 번호 입력
            if work_number:
                number_input = current_row.get_by_role("combobox", name="번호", exact=True)
                number_input.fill(str(work_number))
                print(f"  - 번호: '{work_number}' 입력")
                number_input.press("Tab")
                print(f"  - '번호' 입력 후 Tab 실행")
            
            # --- 여기가 핵심 수정 부분입니다 ---
            # 3. 자동 완성 기다리지 않고 바로 다음 단계 진행
            print("  - 자동 완성 대기 없이, 바로 데이터 입력을 시작합니다.")
            page.wait_for_timeout(500) # 안정성을 위한 최소한의 대기
            # --- 수정 끝 ---
            
            current_row = grid.locator("tr.real-current") # 안전을 위해 현재 행 다시 찾기

            # 4. 수량 입력
            if work_qty:
                qty_input = current_row.get_by_label("수량", exact=True)
                qty_input.evaluate(js_code, str(work_qty))
                print(f"  - 수량: '{work_qty}'으로 수정")
                qty_input.press("Enter")
                print("  - '수량' 입력 후 Enter 실행")

            # 5. 단가 입력
            if work_price:
                price_input = current_row.get_by_label("단가 부가세 포함")
                price_input.evaluate(js_code, str(work_price))
                print(f"  - 단가: '{work_price}'으로 수정")
        
        return True
    except Exception as e:
        print(f"⚠️ 표에 데이터를 입력하는 중 심각한 오류 발생: {e}")
        page.pause()
        return False