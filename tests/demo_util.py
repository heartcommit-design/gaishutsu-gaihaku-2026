"""テスト用のデモデータ（すべて架空）を入れる・消す共通の小道具。

本番用のアプリ（index.html）には「デモデータを入れる／消す」が無い。テストは tests/demo_data.js を
ページに読み込み（アプリからは読み込まれない・sw.js のキャッシュにも入らない）、その demoIn()／demoOut() で入れる・消す。
中身は試す用 2.4.1 のデモと同じ：東1病棟の患者54人・外出・外泊中7人・予定19件・帰院済み10件・架空の職員30人。

- demo_in(pg) / demo_out(pg)：sync_api のページ用
- demo_in_async(pg) / demo_out_async(pg)：async_api のページ用
もとのボタンの押し方（設定タブを開いてから押す）に合わせ、既定では先に設定タブを開く（settings=False で開かない）。
入れ終わると、もとと同じくトースト「デモデータを入れました（…）」が出て「外出・外泊中」タブに切り替わる。
ページを読み込み直すと demo_data.js も消えるので、毎回まだ無ければ読み込む。
"""
import os

DEMO_JS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'demo_data.js')
_HAS = "typeof window.demoIn==='function'"
_TAB = 'nav button[data-tab=settings]'


def _load(pg):
    if not pg.evaluate(_HAS):
        pg.add_script_tag(path=DEMO_JS)


def demo_in(pg, settings=True, wait=300):
    _load(pg)
    if settings:
        pg.click(_TAB)
    pg.evaluate('demoIn()')
    if wait:
        pg.wait_for_timeout(wait)


def demo_out(pg, settings=True, wait=300):
    _load(pg)
    if settings:
        pg.click(_TAB)
    pg.evaluate('demoOut()')
    if wait:
        pg.wait_for_timeout(wait)


async def _load_async(pg):
    if not await pg.evaluate(_HAS):
        await pg.add_script_tag(path=DEMO_JS)


async def demo_in_async(pg, settings=True, wait=300):
    await _load_async(pg)
    if settings:
        await pg.click(_TAB)
    await pg.evaluate('demoIn()')
    if wait:
        await pg.wait_for_timeout(wait)


async def demo_out_async(pg, settings=True, wait=300):
    await _load_async(pg)
    if settings:
        await pg.click(_TAB)
    await pg.evaluate('demoOut()')
    if wait:
        await pg.wait_for_timeout(wait)
