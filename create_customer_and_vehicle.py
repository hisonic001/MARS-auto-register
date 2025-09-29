import datetime
from playwright.sync_api import expect, TimeoutError
from login import click_in_main_frame # 'click_in_main_frame'을 사용하기 위해 추가

def process_customer_form(page, customer_data):
    """(원본 버전) 고객 정보 양식을 채웁니다."""
    customer_name = customer_data.get('이름') or "김고객"
    address = customer_data.get('주소') or "속초"
    phone_number = customer_data.get('휴대폰 번호') or "010-1234-5678"
    print(f"-> '{customer_name}' 고객 정보 처리 중...")
    
    main_frame = page.frame_locator("iframe[title=\"Main Content\"]")
    
    main_frame.get_by_role("textbox", name="이름", exact=True).fill(customer_name)
    main_frame.get_by_role("textbox", name="주소").fill(address)
    main_frame.get_by_role("textbox", name="휴대폰 번호").fill(str(phone_number))
    print("✅ 텍스트 정보 입력 완료.")
    
    print("-> 동의 항목 처리 중...")
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
        
    print("✅ 동의 항목 처리 완료.")
    return True

def process_vehicle_form(page, vehicle_data):
    """차량 정보 양식을 채웁니다."""
    license_plate = vehicle_data.get('번호판 번호', '번호판 없음')
    print(f"-> '{license_plate}' 차량 정보 처리 중...")
    
    main_frame = page.frame_locator("iframe[title=\"Main Content\"]")
    vehicle_section_header = main_frame.get_by_role("button", name="차량")
    
    if vehicle_section_header.get_attribute("aria-expanded") == "false":
        print("-> '차량' 섹션을 확장합니다...")
        vehicle_section_header.click()
        main_frame.get_by_role("textbox", name="번호판 번호").wait_for(timeout=5000)
    
    print("-> 차량 정보 입력 중...")
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
    
    print("✅ 차량 정보 입력 완료.")
    main_frame.locator(".task-dialog-content").click(position={'x': 5, 'y': 5})
    return True

def create_customer_and_vehicle(page, data_row):
    """고객과 차량 정보를 생성하고, 최종 '확인' 버튼을 클릭하여 저장합니다."""
    customer_name = data_row.get('이름') or "김고객"
    print(f"--- '{customer_name}' 고객 전체 프로세스 시작 ---")

    try:
        if not process_customer_form(page, data_row):
            return False
        if not process_vehicle_form(page, data_row):
            return False

        print("-> 중복 데이터 오류가 있는지 확인합니다...")
        main_frame = page.frame_locator("iframe[title=\"Main Content\"]")
        error_message_locator = main_frame.locator(".ms-nav-validationmessage-error")

        try:
            # 오류 메시지가 나타날 때까지 최대 3초만 기다려봅니다.
            error_message_locator.wait_for(state="visible", timeout=3000)
            error_text = error_message_locator.inner_text()
            print(f"  - ⚠️ 유효성 검사 오류 발견: '{error_text}'")
            page.pause() # 오류 확인을 위해 일시정지

        except TimeoutError:
            print("  - ✅ 오류 없음. 정상적으로 저장된 것으로 보입니다.")
            # 성공 후 다음 단계로 넘어가기 전, 페이지가 안정화될 시간을 줍니다.
            page.wait_for_timeout(2000)
                # --- 이 부분이 새로 추가되었습니다 ---
        # 최종 '확인' 버튼을 클릭하여 저장합니다.
        if not click_in_main_frame(page, role="button", name="확인", description="고객/차량 정보 최종 저장"):
            return False
        # --- 여기까지 추가 ---
        print(f"--- '{customer_name}' 고객 전체 프로세스 완료 ---")
        return True

    except Exception as e:
        print(f"⚠️ '{customer_name}' 고객 생성 중 오류 발생: {e}")
        page.pause()
        return False