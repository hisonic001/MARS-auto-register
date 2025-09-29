# sales_handler.py (가장 안정적이었던 코드로 복원 + ArrowDown 키 이동 적용)

import datetime
from playwright.sync_api import expect, TimeoutError, Frame, Page
import pandas as pd

# 이 함수는 성공했으므로 수정 없이 그대로 둡니다.
def create_new_sale(page: Page, sales_data: dict) -> bool:
    print("🚀 신규 판매 내역 등록을 시작합니다...")
    try:
        main_frame = page.frame_locator("iframe[title=\"Main Content\"]")
        
        print("-> '판매 내역' 메뉴로 이동합니다...")
        sales_menu = main_frame.get_by_role("menuitem", name="판매 내역")
        expect(sales_menu).to_be_visible(timeout=10000)
        sales_menu.click()

        print("-> '신규' 메뉴를 클릭합니다...")
        new_button = main_frame.get_by_role("menuitem", name="신규")
        expect(new_button).to_be_visible(timeout=5000)
        new_button.click()

        print("-> '신규 매출 주문'을 선택합니다...")
        new_sales_order_button = main_frame.get_by_role("menuitem", name="신규 매출 주문")
        expect(new_sales_order_button).to_be_visible(timeout=5000)
        new_sales_order_button.click()

        print("✅ 신규 판매 내역 양식을 성공적으로 열었습니다.")
        
        expect(main_frame.get_by_role("button", name="일반, 더 보기")).to_be_visible()

        try:
            more_button = main_frame.get_by_role("button", name="일반, 더 보기")
            if more_button.get_attribute("aria-expanded") == "false":
                more_button.click(timeout=3000)
                print("-> '더 보기' 버튼을 클릭하여 추가 정보를 표시합니다.")
                page.wait_for_timeout(500)
        except TimeoutError:
            print("-> '더 보기' 버튼이 없거나 이미 확장된 상태입니다.")

        mileage_field = main_frame.get_by_role("textbox", name="현재 주행거리")
        mileage_field.wait_for(state="visible", timeout=5000)
        print("-> 주행거리 및 날짜 정보를 입력합니다...")
        
        current_mileage = sales_data.get('주행거리')
        document_date = sales_data.get('날짜') or datetime.date.today().strftime("%Y-%m-%d")

        if current_mileage:
            mileage_field.fill(str(current_mileage))
            
        main_frame.get_by_role("combobox", name="문서 날짜").fill(str(document_date))
        completion_date_field = main_frame.get_by_role("combobox", name="완료 일자")
        completion_date_field.fill(str(document_date))
        
        print("✅ 주행거리 및 날짜 정보 입력 완료.")
        print("-> Tab 키를 눌러 표 로드를 트리거합니다...")
        completion_date_field.press("Tab")
        return True
            
    except Exception as e:
        print(f"⚠️ 판매 내역 화면으로 이동하거나 기본 정보 입력 중 오류 발생: {e}")
        page.pause()
        return False

## ==============================================================================
# ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ 가장 안정적인 로케이터로 수정했습니다 ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
def fill_sales_table(page: Page, sales_items_df: pd.DataFrame) -> bool:
    print("-> 판매 내역 표에 작업 내용을 입력합니다...")
    try:
        main_frame = page.frame_locator("iframe[title=\"Main Content\"]")
        grid_container = main_frame.locator("div[controlname='Sales Order Subform']")
        js_code = "(element, value) => { element.value = value; element.dispatchEvent(new Event('change', { bubbles: true })); }"

        print("-> 표가 나타날 때까지 기다립니다...")
        expect(grid_container).to_be_visible(timeout=15000)
        grid_container.scroll_into_view_if_needed()
        print("-> 표가 입력 가능한 상태입니다.")
        
        for index, item_row in sales_items_df.iterrows():
            print(f"-> {index + 1}번째 작업 아이템을 처리합니다...")
            
            current_row = grid_container.locator("tr.real-current")
            
            current_row.get_by_role("combobox", name="유형").select_option(label=item_row.get("유형"))
            print(f"  - 유형: '{item_row.get('유형')}' 선택")

            number_input = current_row.get_by_role("combobox", name="번호", exact=True)
            number_input.fill(str(item_row.get("번호")))
            number_input.press("Tab")
            print(f"  - 번호: '{item_row.get('번호')}' 입력 후 Tab")
            page.wait_for_timeout(1200)
            
            qty_input = current_row.get_by_label("수량", exact=True)
            qty_input.evaluate(js_code, str(item_row.get("수량")))
            qty_input.press("Enter")
            print(f"  - 수량: '{item_row.get('수량')}' 입력 후 Enter")

            price_input = current_row.get_by_label("단가 부가세 포함")
            price_input.evaluate(js_code, str(item_row.get("단가")))
            price_input.press("Enter")
            print(f"  - 단가: '{item_row.get('단가')}' 입력")

            if index < len(sales_items_df) - 1:
                print(f"  - 다음 행({index + 2})을 활성화하기 위해 항상 두 번째 행 머리글을 클릭합니다...")
                main_frame.get_by_role("rowheader").nth(index + 1).click()
                page.wait_for_timeout(500)
        return True
    except Exception as e:
        print(f"⚠️ 표에 데이터를 입력하는 중 심각한 오류 발생: {e}")
        page.pause()
        return False
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲ 가장 안정적인 로케이터로 수정했습니다 ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
# ==============================================================================