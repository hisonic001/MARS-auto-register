from playwright.sync_api import TimeoutError

def login(page, user_id, password):
    # (login 함수는 변경 없음)
    mars_login_url = "https://mars.tyremore.co.kr/MARS/SignIn?ReturnUrl=%2FMARS%2F%3Ftenant%3D61168583"
    print("로그인 페이지로 이동합니다...")
    page.goto(mars_login_url)
    print("아이디와 비밀번호를 입력합니다...")
    page.locator("input#UserName").fill(user_id)
    page.locator("input#Password").fill(password)
    print("로그인을 시도합니다...")
    page.locator("button#submitButton").click()
    print("로그인 후 팝업(iframe)이 나타나는지 확인합니다...")
    try:
        iframe = page.frame_locator("iframe[title=\"Main Content\"]")
        iframe.get_by_role("button", name="확인").wait_for(timeout=15000)
        print("🎉 로그인 성공! 팝업(iframe)을 확인했습니다.")
        return True
    except Exception as e:
        print(f"⚠️ 로그인 실패! {e}")
        page.pause()
        return False
    
def click_in_main_frame(page, role, name, description="", exact=False):
    # (click_in_main_frame 함수는 변경 없음)
    if not description:
        description = f"'{name}' {role}"
    print(f"🚀 작업 시작: {description} 클릭")
    try:
        main_frame = page.frame_locator("iframe[title=\"Main Content\"]")
        element_to_click = main_frame.get_by_role(role, name=name, exact=exact)
        element_to_click.click(timeout=15000)
        print(f"✅ 클릭 성공: {description}")
        page.wait_for_timeout(1000)
        return True
    except Exception as e:
        print(f"⚠️ {description} 클릭 중 오류가 발생했습니다: {e}")
        page.pause()
        return False