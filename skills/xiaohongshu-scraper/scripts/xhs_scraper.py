'''
==============================================================
  小red薯爬爬 (xiaohongshu-scraper) — 小红书数据采集工具
  📅 创建: 2026-07-23 | 🏷️ 版本: 1.0.4
  ✍️ 作者: 你的名字 (虾评 @你的ID)
  🔗 发布: https://xiaping.coze.com/skill/c41d3ccf-56be-4c9f-b30e-5f0cc943067a
  ⚠️ 本脚本仅供个人学习使用, 未经授权禁止商用转载
  🌐 兼容: Windows / macOS / Linux（Windows 自动检测默认浏览器，其他平台用 Playwright 自带 Chromium）
==============================================================
'''
import asyncio, json, os, sys, platform
from urllib.parse import quote

# Windows 才需要注册表；macOS/Linux 导入 winreg 会崩溃，必须条件导入
if sys.platform == 'win32':
    import winreg

from playwright.async_api import async_playwright

# Cookie 默认存用户主目录，可用 XHS_COOKIE_PATH 环境变量改到 E 盘等位置
COOKIE_PATH = os.environ.get('XHS_COOKIE_PATH', os.path.expanduser('~/.xhs_cookies.json'))


def detect_default_browser():
    """检测默认浏览器，返回 (engine, channel)。
    - Windows: 读注册表 UserChoice，支持 Chrome/Edge/Firefox
    - macOS/Linux: 用 Playwright 自带 Chromium（需 playwright install chromium），
      也可用 XHS_BROWSER 环境变量强制: chrome / edge / firefox
    """
    forced = os.environ.get('XHS_BROWSER', '').strip().lower()
    if forced in ('chrome', 'googlechrome'):
        return 'chromium', 'chrome'
    if forced in ('edge', 'msedge'):
        return 'chromium', 'msedge'
    if forced == 'firefox':
        return 'firefox', None
    if sys.platform != 'win32':
        # macOS/Linux：Playwright 自带 Chromium 最稳
        return 'chromium', None
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice')
        progid, _ = winreg.QueryValueEx(key, 'ProgId')
        winreg.CloseKey(key)
    except OSError:
        return 'chromium', 'msedge'  # 读不到注册表时回退 Edge
    progid = progid.lower()
    if 'chrome' in progid:
        return 'chromium', 'chrome'
    if 'firefox' in progid:
        return 'firefox', None
    return 'chromium', 'msedge'  # edge 及未知浏览器回退 Edge


async def launch_browser(p):
    """按默认浏览器启动；失败时回退 chromium 内置浏览器"""
    engine, channel = detect_default_browser()
    print(f'🌐 使用浏览器: {engine}' + (f' ({channel})' if channel else ''))
    try:
        if engine == 'firefox':
            return await p.firefox.launch(headless=False)
        return await p.chromium.launch(channel=channel, headless=False)
    except Exception as e:
        print(f'⚠️ 启动 {engine} ({channel}) 失败: {e}')
        print('   回退 Playwright 内置 Chromium...')
        return await p.chromium.launch(headless=False)


async def main():
    # 手机号：优先环境变量，否则运行时输入（不写在模块顶层，避免 import 卡住）
    # 🔒 隐私说明：手机号仅在本进程内存中使用（用于短信登录），不写入任何文件、不持久化、不对外传输
    phone = os.environ.get('XHS_PHONE', '').strip() or input('📱 请输入手机号: ').strip()

    p = await async_playwright().start()
    browser = None
    try:
        browser = await launch_browser(p)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()

        # 1) 登录页
        await page.goto('https://www.xiaohongshu.com/login', timeout=60000, wait_until='domcontentloaded')
        await page.wait_for_timeout(2000)

        # 勾同意
        agree = await page.query_selector('span.agree-icon')
        if agree: await agree.click()
        print('✅ 已勾选同意')

        # 填手机号
        phone_inp = await page.query_selector('input[placeholder="输入手机号"]')
        if phone_inp: await phone_inp.fill(phone)
        print('✅ 已填手机号')

        # 发验证码
        code_btn = await page.query_selector('span.code-button.active')
        if code_btn: await code_btn.click()
        print('📱 验证码已发送！')
        print('⏰ 请在 1 分钟内完成验证码填写与登录！两种方式任选：')
        print('   ① 把验证码发给我，我自动帮你填（或设 XHS_CODE 环境变量）')
        print('   ② 直接在当前浏览器窗口手动填写验证码并登录')
        print('   ⏳ 倒计时结束后将自动跳转搜索页检查登录状态...')

        # 等最多 60 秒（拿到 XHS_CODE 立即继续）
        code = ''
        for i in range(60):
            code = os.environ.get('XHS_CODE', '')
            if code: break
            await asyncio.sleep(1)

        if code:
            # 自动填码 + 登录
            code_inp = await page.query_selector('input[placeholder="输入验证码"]')
            if code_inp: await code_inp.fill(code)
            login_btn = await page.query_selector('button.submit')
            if login_btn: await login_btn.click()
            print('✅ 已自动填入验证码并点击登录')
            await page.wait_for_timeout(5000)
        else:
            print('⏰ 1 分钟已到，未收到验证码输入 —— 若你已在窗口手动登录将自动继续，否则请稍后重试')

        # 关键词（由使用者画像/运行时输入决定）
        keyword = os.environ.get('XHS_KEYWORD', '').strip() or input('🔍 请输入搜索关键词: ').strip()
        print(f'\n🔍 搜索: {keyword}')

        # 1 分钟后自动跳转搜索页（无论登录是否完成）
        # 🔒 关键词经 URL 编码后拼接，防止特殊字符/注入 payload 污染链接
        await page.goto(f'https://www.xiaohongshu.com/search_result?keyword={quote(keyword)}',
                       timeout=60000, wait_until='domcontentloaded')
        try: await page.wait_for_load_state('networkidle', timeout=15000)
        except: pass
        await page.wait_for_timeout(5000)

        # 登录状态检查
        if 'login' in page.url.lower() or await page.query_selector('span.agree-icon'):
            print('⚠️ 尚未登录成功（仍停留在登录页）')
            print('   👉 请在弹出的浏览器窗口中手动完成登录（1 分钟内有效），完成后会自动继续')
            print('   👉 或重试：把验证码发给我，重新运行本脚本自动填写')
            await page.wait_for_timeout(10000)  # 再给 10 秒手动操作机会
            if 'login' in page.url.lower() or await page.query_selector('span.agree-icon'):
                print('❌ 登录未完成，本次采集终止。Cookie 未保存，下次需重新登录。')
                return
        else:
            print('✅ 登录成功！')

        # 保存 Cookie（确认登录成功后才保存）
        # 🔒 敏感凭证：写入后立即收紧文件权限（POSIX 下 600 仅本人可读；Windows 提示注意保管），
        #    并提醒勿将本文件分享/提交到仓库
        cookies = await context.cookies()
        os.makedirs(os.path.dirname(COOKIE_PATH), exist_ok=True)
        with open(COOKIE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False)
        try:
            os.chmod(COOKIE_PATH, 0o600)  # POSIX 生效；Windows 忽略权限位
        except OSError:
            pass
        print(f'✅ Cookie 已保存: {COOKIE_PATH}')
        print('   🔒 该文件含登录凭证，请勿外传/提交到代码仓库；不再使用可删除')

        # 提取数据
        notes = await page.evaluate('''() => {
            const r = [], s = new Set();
            document.querySelectorAll('[data-note-id]').forEach(c => {
                const id = c.getAttribute('data-note-id');
                if (!id || id.length!==24 || s.has(id)) return;
                s.add(id);
                const t = (c.querySelector('.title, [class*="title"], h3, h4')||c).textContent?.trim()||'';
                r.push({id, title: t.substring(0,100)});
            });
            return r;
        }''')

        print(f'\n📊 共 {len(notes)} 条笔记:\n')
        for i, n in enumerate(notes[:30], 1):
            url = f'https://www.xiaohongshu.com/explore/{n["id"]}'
            print(f'{i}. {n["title"][:50]}')
            print(f'   🔗 {url}\n')

        # 保存结果到当前目录（避免写死 C 盘路径）
        out = os.path.join(os.getcwd(), 'xhs_results.json')
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)
        print(f'✅ 已保存: {out}')
    finally:
        if browser:
            await browser.close()
        await p.stop()

if __name__ == '__main__':
    asyncio.run(main())
