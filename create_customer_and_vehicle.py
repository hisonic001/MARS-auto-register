import datetime
from playwright.sync_api import expect, TimeoutError

def process_customer_form(page, customer_data):
    """(Original Version) Fills out the customer information form."""
    customer_name = customer_data.get('이름') or "김고객"
    address = customer_data.get('주소') or "속초"
    phone_number = customer_data.get('휴대폰 번호') or "010-1234-5678"
    print(f"-> Processing customer info for '{customer_name}'...")
    
    main_frame = page.frame_locator("iframe[title=\"Main Content\"]")
    
    print("-> Entering text information...")
    main_frame.get_by_role("textbox", name="이름", exact=True).fill(customer_name)
    main_frame.get_by_role("textbox", name="주소").fill(address)
    main_frame.get_by_role("textbox", name="휴대폰 번호").fill(str(phone_number))
    print("✅ Text information entered.")
    
    print("-> Processing consent items...")
    consent_keywords = ["비즈니스 목적의 동의","마케팅 및 광고 목적의 동의","제3자 제공 및 국외 이전에 대한 동의"]
    checkbox_headers = ["이메일 접수","Accepts SMS & KAKAO 알림톡(Bizmessage)","전화 통화 수락","하드카피 허용"]
    
    for keyword in consent_keywords:
        row_locator = main_frame.get_by_role("row").filter(has_text=keyword)
        for header in checkbox_headers:
            checkbox = row_locator.get_by_role("gridcell", name=header).locator("[role=checkbox]")
            initial_state = checkbox.get_attribute("aria-checked")
            checkbox.click()
            expect(checkbox).to_have_attribute("aria-checked", str(not (initial_state == "true")).lower(), timeout=5000)
        
        signature_option_text = "수락된 동의"
        row_locator.get_by_role("combobox", name="고객 서명").select_option(label=signature_option_text)
        
    print("✅ Consent items processed.")
    return True

def process_vehicle_form(page, vehicle_data):
    """Fills out the vehicle information form."""
    license_plate = vehicle_data.get('번호판 번호', '번호판 없음')
    print(f"-> Processing vehicle info for '{license_plate}'...")
    
    main_frame = page.frame_locator("iframe[title=\"Main Content\"]")
    vehicle_section_header = main_frame.get_by_role("button", name="차량")
    
    if vehicle_section_header.get_attribute("aria-expanded") == "false":
        print("-> Expanding the 'Vehicle' section...")
        vehicle_section_header.click()
        main_frame.get_by_role("textbox", name="번호판 번호").wait_for(timeout=5000)
    
    print("-> Entering vehicle information...")
    main_frame.get_by_role("textbox", name="번호판 번호").fill(license_plate)
    main_frame.get_by_role("combobox", name="차량 종류").select_option(label=vehicle_data.get('차량 종류', ''))
    main_frame.get_by_role("combobox", name="제조사").fill(vehicle_data.get('제조사', ''))
    main_frame.get_by_role("combobox", name="모델").fill(vehicle_data.get('모델', ''))
    main_frame.get_by_role("textbox", name="차량 연도").fill(str(vehicle_data.get('차량 연도', '')))
    main_frame.get_by_role("textbox", name="주행거리", exact=True).fill(str(vehicle_data.get('주행거리', '')))
    
    today = datetime.date.today()
    current_month_day = today.strftime("-%m-%d")
    vehicle_year = str(int(vehicle_data.get('차량 연도', today.year)))
    registration_date = vehicle_year + current_month_day
    main_frame.get_by_role("combobox", name="등록 날짜").fill(registration_date)
    
    print("✅ Vehicle information entered.")
    main_frame.locator(".task-dialog-content").click(position={'x': 5, 'y': 5})
    return True

def create_customer_and_vehicle(page, data_row):
    """Orchestrates the creation of customer and vehicle, then checks for errors."""
    customer_name = data_row.get('이름') or "김고객"
    print(f"--- Starting full process for customer '{customer_name}' ---")

    try:
        if not process_customer_form(page, data_row):
            return False
        if not process_vehicle_form(page, data_row):
            return False

        # NOTE: The final "Confirm" button click is handled in the main.py logic
        # after this function returns, if needed.

        print("-> Checking for duplicate data errors after form submission...")
        main_frame = page.frame_locator("iframe[title=\"Main Content\"]")
        error_message_locator = main_frame.locator(".ms-nav-validationmessage-error")

        try:
            error_message_locator.wait_for(state="visible", timeout=3000)
            error_text = error_message_locator.inner_text()
            print(f"  - ⚠️ Validation Error Detected: '{error_text}'")
            page.pause() # Pause to allow for manual inspection

        except TimeoutError:
            print("  - ✅ No validation errors detected. Assumed success.")

        print(f"--- Full process for '{customer_name}' complete ---")
        return True

    except Exception as e:
        print(f"⚠️ An error occurred during the creation process for '{customer_name}': {e}")
        page.pause()
        return False