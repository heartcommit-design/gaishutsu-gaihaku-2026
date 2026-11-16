"""3.0.0（本番用）の画面写真：空の状態（データなし）の「外出・外泊中」「予定」「＋ 新規登録」と「設定」（デモの欄が無いこと）。
iPad 横 1180×820・iPad 縦 1024×1366、1倍（新規登録は下の固定の登録バーが正しい位置に写るよう、画面の大きさで撮る。設定は全体）。時計は 2026/11/16(月) 10:00（日本時間）に固定（明るい配色）。
docs/screens_v3.0.0/ に書き出す。各画面で横にはみ出していないことも確かめる。
"""
import os
from playwright.sync_api import sync_playwright
from v200_util import jst

HERE = os.path.dirname(os.path.abspath(__file__)); APP = os.path.dirname(HERE)
DST = os.path.join(APP, 'docs', 'screens_v3.0.0'); os.makedirs(DST, exist_ok=True)
URL = 'file://' + APP + '/index.html'


def main():
    errs = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for lbl, w, h in (('yoko', 1180, 820), ('tate', 1024, 1366)):
            ctx = b.new_context(viewport={'width': w, 'height': h}, timezone_id='Asia/Tokyo', device_scale_factor=1, has_touch=True)
            pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.clock.set_fixed_time(jst(2026, 11, 16, 10, 0))
            pg.goto(URL); pg.wait_for_timeout(700); pg.click('#startOv'); pg.wait_for_timeout(400)
            for tab, name, full in (('active', 'gaishutsu_chu', False), ('plan', 'yotei', False), ('new', 'shinki', False), ('settings', 'settei', True)):
                pg.click(f'nav button[data-tab={tab}]'); pg.wait_for_timeout(500)
                pg.evaluate('window.scrollTo(0,0)'); pg.wait_for_timeout(150)
                sw = pg.evaluate('[document.documentElement.scrollWidth,document.documentElement.clientWidth]')
                assert sw[0] <= sw[1], (lbl, tab, '横にはみ出し', sw)
                pg.screenshot(path=os.path.join(DST, f'{name}_{lbl}.png'), full_page=full)
            ctx.close()
        b.close()
    print('errors', errs)
    assert not errs


if __name__ == '__main__':
    main()
