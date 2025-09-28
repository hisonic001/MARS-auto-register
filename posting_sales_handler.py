# posting_handler.py

from playwright.sync_api import expect

def post_sales_order(page, main_frame):
    """
    '전기' 프로세스를 진행하고, 최종 확인 버튼을 누르기 직전에 스크립트를 일시정지합니다.
    """
    print("-> '전기' 프로세스를 시작합니다...")
    try:
        # 1. '전기' 메뉴 항목을 클릭합니다.
        main_frame.get_by_role("menuitem", name="전기").click()
        print("  - '전기' 메뉴 클릭 완료.")

        # 2. 나타나는 '전기...' 하위 메뉴를 클릭합니다.
        post_submenu_button = main_frame.get_by_role("menuitem", name="전기...")
        expect(post_submenu_button).to_be_visible(timeout=5000)
        post_submenu_button.click()
        print("  - '전기...' 하위 메뉴 클릭 완료.")

        # 3. 마지막 확인 창이 뜨면, '확인' 버튼을 누르기 직전에 멈춥니다.
        final_confirm_button = main_frame.get_by_role("button", name="확인")
        expect(final_confirm_button).to_be_visible(timeout=5000)
        print("  - 최종 '확인' 버튼을 찾았습니다.")
        
        print("\n" + "="*50)
        print("--- 🛑 최종 저장 직전에 스크립트를 일시정지합니다. ---")
        print("--- 💡 모든 정보가 올바른지 확인하세요. ---")
        print("--- 💡 계속 진행하려면 Inspector의 'Resume(▶️)' 버튼을 누르세요. ---")
        print("="*50 + "\n")
        
        page.pause() # <<-- 여기서 멈춥니다!

        # 사용자가 수동으로 'Resume'을 눌러야만 아래 코드가 실행됩니다.
        final_confirm_button.click()
        print("  - 최종 '확인' 버튼 클릭 완료.")
        
        return True

    except Exception as e:
        print(f"⚠️ '전기' 프로세스 중 오류가 발생했습니다: {e}")
        page.pause()
        return False