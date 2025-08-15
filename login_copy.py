import os
from playwright.sync_api import TimeoutError

def _should_pause():
    return os.getenv("PAUSE_ON_ERROR") == "1"

def login(page, user_id, password):
    """로그인: 성공 지표 대기로 안정화, 실패 시 예외 발생"""
    mars_login_url = os.getenv("MARS_URL") or "https://mars.tyremore.co.kr/MARS/SignIn?ReturnUrl=%2FMARS%2F%3Ftenant%3D61168583"
    print("로그인 페이지로 이동합니다...")
    page.goto(mars_login_url, wait_until="domcontentloaded")

    print("아이디와 비밀번호를 입력합니다...")
    page.locator("input#UserName").fill(user_id)
    page.locator("input#Password").fill(password)

    print("로그인을 시도합니다...")
    page.locator("button#submitButton").click()

    print("로그인 성공 지표 대기 중...")
    try:
        # 1) 메인 프레임이 로드되고
        main_frame = page.frame_locator('iframe[title="Main Content"]')
        # 2) 대시보드/메뉴 중 핵심 요소 하나가 나타나는지 확인 (텍스트는 현장에 맞게 조정 가능)
        main_frame.get_by_role("button", name="고객 정보 검색", exact=False).wait_for(timeout=20000)
        print("✅ 로그인 성공으로 판단했습니다.")
    except TimeoutError as e:
        shot = page.screenshot(path="runs/login_failed.png", full_page=True)
        print(f"❌ 로그인 실패: {e}. 스크린샷 저장: {shot}")
        if _should_pause():
            page.pause()
        raise

def click_in_main_frame(page, role, name, description="", exact=False):
    """접근성(role/name) 기반 클릭 헬퍼 (메인 iframe 내)"""
    if not description:
        description = f"'{name}' {role}"
    print(f"🚀 작업 시작: {description} 클릭")
    try:
        main_frame = page.frame_locator('iframe[title="Main Content"]')
        main_frame.get_by_role(role, name=name, exact=exact).click(timeout=15000)
        print(f"✅ 클릭 성공: {description}")
        page.wait_for_timeout(700)
        return True
    except Exception as e:
        shot = page.screenshot(path="runs/click_error.png", full_page=True)
        print(f"⚠️ {description} 클릭 중 오류: {e} (shot:{shot})")
        if _should_pause():
            page.pause()
        return False
