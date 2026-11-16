"""3.0.0：本格導入版（本番用）を作った。assert で確かめる。
- 版の2か所（index.html の APP_VERSION と sw.js の CACHE）が 3.0.0 でそろう
- IndexedDB 名は gaishutsu_kanri_honban、キャッシュ名は gaishutsu-honban-v3.0.0。
  sw.js は gaishutsu-honban- で始まる自分の古いキャッシュだけを消し、旧版（gaishutsu-v…）・試す用（gaishutsu-shisaku-v…）のキャッシュは消さない
- index.html・sw.js・manifest に「shisaku」「試作」「ハートコミット」「デモデータ」が無い。デモを作るコードも無い
- 画面（設定）に「デモデータを入れる／消す」が無い
- 空の状態で開いて JS エラーが無く、新規登録 → 帰院まで1件通る（写真は帰院で消える）
- 旧版（gaishutsu_kanri）・試す用（gaishutsu_kanri_shisaku）の名前の IndexedDB と配色の写し（localStorage）を先に作っておいても、
  本番用を開いて使った後に、それらが消えも変わりもしない
テストの中の「shisaku」は、試す用のデータに触れないことを確かめるためだけに使う（アプリ本体には無い）。
時計は 2026/11/16(月) 10:00（日本時間）から（夜だと「外出で帰院が翌日」の確認が出るため）。
"""
import os, re, json, struct, zlib, http.server, threading, functools
from playwright.sync_api import sync_playwright
from v200_util import jst

HERE = os.path.dirname(os.path.abspath(__file__)); APP = os.path.dirname(HERE)
OUT = os.path.join(HERE, 'out'); os.makedirs(OUT, exist_ok=True)
PORT = 8793
OTHER_DBS = ['gaishutsu_kanri', 'gaishutsu_kanri_shisaku']   # 旧版・試す用


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def png(path, w=60, h=80):
    raw = b''.join(b'\x00' + b'\x80\x20\x20' * w for _ in range(h))
    ch = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw)) + ch(b'IEND', b''))


# 旧版・試す用と同じ形の DB を作り、見本の記録（架空）を入れる
MAKE_DBS = """async(names)=>{for(const name of names){await new Promise((res,rej)=>{const r=indexedDB.open(name,2);
  r.onupgradeneeded=()=>{const d=r.result;['outings','tags','patients'].forEach(n=>d.createObjectStore(n,{keyPath:'id'}));['photos','settings'].forEach(n=>d.createObjectStore(n));};
  r.onsuccess=()=>{const d=r.result;const t=d.transaction(['outings','tags','patients','settings'],'readwrite');
    t.objectStore('outings').put({id:'o-'+name,name:'見本 '+name,pid:'P0009',status:'out',kind:'外出',departAt:1,dueAt:2,dueAtOriginal:2,log:[]});
    t.objectStore('tags').put({id:'T-99',status:'inuse',outingId:'o-'+name});
    t.objectStore('patients').put({id:'p-'+name,name:'見本 '+name,pid:'P0009'});
    t.objectStore('settings').put({nurses:['見本 看護師 '+name]},'main');
    t.oncomplete=()=>{d.close();res();};};r.onerror=()=>rej(r.error);});}}"""
# DB の中身をすべて読む（無ければ null。開くだけで作らないよう、先に databases() で確かめる）
DUMP_DBS = """async(names)=>{const have=(await indexedDB.databases()).map(x=>x.name);const out={};
  for(const name of names){if(!have.includes(name)){out[name]=null;continue;}
    out[name]=await new Promise(res=>{const r=indexedDB.open(name);r.onsuccess=async()=>{const d=r.result;const o={version:d.version};
      for(const s of [...d.objectStoreNames]){o[s]=await new Promise(rr=>{const q=d.transaction(s).objectStore(s).getAll();q.onsuccess=()=>rr(q.result);});}
      d.close();res(o);};});}
  return JSON.stringify(out);}"""


def main():
    html = open(os.path.join(APP, 'index.html'), encoding='utf-8').read()
    sw = open(os.path.join(APP, 'sw.js'), encoding='utf-8').read()
    man_txt = open(os.path.join(APP, 'manifest.webmanifest'), encoding='utf-8').read()
    man = json.loads(man_txt)
    # ---- 版・内部名
    assert re.search(r"APP_VERSION='([\d.]+)'", html).group(1) == '3.0.0'
    assert re.search(r"const CACHE = '([^']+)'", sw).group(1) == 'gaishutsu-honban-v3.0.0'
    assert re.search(r"const PREFIX = '([^']+)'", sw).group(1) == 'gaishutsu-honban-'
    assert "const DB_NAME='gaishutsu_kanri_honban'" in html
    assert html.count('indexedDB.open(') == 1 and 'indexedDB.open(DB_NAME' in html, '本番用の DB 以外を開いている'
    assert 'deleteDatabase' not in html and 'caches.' not in html, 'アプリ本体が DB・キャッシュを消している'
    for k in re.findall(r"(?:localStorage|sessionStorage)\.(?:getItem|setItem|removeItem)\('([^']+)'", html):
        assert 'honban' in k, k
    # 旧版・試す用の名前に触れない
    for txt, nm in ((html, 'index.html'), (sw, 'sw.js'), (man_txt, 'manifest')):
        for w in ['shisaku', '試作', 'ハートコミット', 'デモデータ', 'gaihakuA', "'gaishutsu-v", 'gaishutsu_kanri_shisaku']:
            assert w not in txt, (nm, w)
    # デモを作るコードが無い
    for w in ['demoIn', 'demoOut', 'demoNurses', 'DEMO_', '(デモ)', 'デモ', '.demo']:
        assert w not in html, ('index.html にデモの名残', w)
    # manifest は相対（リポジトリ名に依存しない）
    assert man['start_url'] == './' and man['scope'] == './' and ('id' not in man or not man['id'].startswith(('/', 'http'))), man
    assert man['name'] == '外出・外泊管理' and man['short_name'] == '外出管理', man
    # demo_data.js はアプリからもキャッシュからも読まない
    assert 'demo_data' not in html and 'demo_data' not in sw

    srv = http.server.ThreadingHTTPServer(('127.0.0.1', PORT), functools.partial(Quiet, directory=APP))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f'http://localhost:{PORT}/'
    errs = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={'width': 1180, 'height': 820}, timezone_id='Asia/Tokyo', service_workers='allow', has_touch=True)
        pg = ctx.new_page()
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
        pg.clock.install(time=jst(2026, 11, 16, 10, 0))
        # ---- 同じオリジンに、旧版・試す用の DB・キャッシュ・配色の写しと、本番用の古いキャッシュを先に作る
        pg.goto(base + 'manifest.webmanifest')
        pg.evaluate(MAKE_DBS, OTHER_DBS)
        pg.evaluate("""async()=>{for(const [k,v] of [['gaishutsu-v1.12.0','kyu'],['gaishutsu-shisaku-v2.4.1','tamesu'],['gaishutsu-honban-v2.9.9','old']])
          await (await caches.open(k)).put('/x-'+v,new Response(v));
          localStorage.setItem('gaishutsu_shisaku_theme',JSON.stringify({mode:'dark'}));localStorage.setItem('gaishutsu_theme_mihon','kyu');}""")
        before = pg.evaluate(DUMP_DBS, OTHER_DBS)
        assert all(json.loads(before)[n] for n in OTHER_DBS), before

        # ---- 本番用を空の状態で開く
        pg.goto(base); pg.wait_for_timeout(600)
        pg.evaluate("navigator.serviceWorker.ready.then(()=>true)")
        pg.reload(); pg.wait_for_timeout(900)
        assert pg.evaluate('!!navigator.serviceWorker.controller'), 'SW が動いていない'
        keys = pg.evaluate('caches.keys()')
        assert 'gaishutsu-honban-v3.0.0' in keys and 'gaishutsu-honban-v2.9.9' not in keys, keys
        assert 'gaishutsu-v1.12.0' in keys and 'gaishutsu-shisaku-v2.4.1' in keys, ('旧版・試す用のキャッシュが消された', keys)
        assert pg.evaluate("caches.open('gaishutsu-shisaku-v2.4.1').then(c=>c.match('/x-tamesu')).then(r=>r&&r.text())") == 'tamesu'
        pg.click('#startOv'); pg.wait_for_timeout(300)
        pg.evaluate("window.tone=function(){}")
        assert pg.evaluate('[DB_NAME,outings.length,patients.length]') == ['gaishutsu_kanri_honban', 0, 0], '空で始まらない（ほかの DB を読んでいる）'
        assert pg.evaluate('settings.nurses') == []
        # 試す用の配色の写し（暗い）を読まず、本番用の写しは別のキー
        assert pg.evaluate("localStorage.getItem('gaishutsu_honban_theme')") is None or 'dark' not in pg.evaluate("localStorage.getItem('gaishutsu_honban_theme')")
        # 画面にデモのボタン・文言が無い
        pg.click('nav button[data-tab=settings]'); pg.wait_for_timeout(200)
        assert pg.locator('#demoIn, #demoOut').count() == 0
        body = pg.inner_text('body')
        for w in ['デモ', '試作', 'ハートコミット']:
            assert w not in body, w
        assert '3.0.0' in pg.inner_text('#aboutPanel') and '黒田 優' in pg.inner_text('#aboutPanel')

        # ---- 新規登録（写真つき）→ 外出中 → 帰院（写真が消える）
        pg.click('nav button[data-tab=new]'); pg.wait_for_timeout(300)
        pg.fill('input[name=name]', 'テスト 太郎'); pg.fill('input[name=pid]', 'P0001')
        pg.click('#wardRadios label:has-text("東1")')
        pg.click('#depQuick [data-m="0"]'); pg.click('#dueQuick [data-h="2"]')
        pg.fill('input[name=departNurse]', '見本 看護師')
        png(OUT + '/v300_p.png'); pg.set_input_files('#photoInput', OUT + '/v300_p.png'); pg.wait_for_timeout(600)
        pg.evaluate('document.activeElement&&document.activeElement.blur()'); pg.wait_for_timeout(400)
        pg.click('#submitBtn'); pg.wait_for_timeout(1200)
        o = pg.evaluate("(()=>{const o=outings.find(x=>x.pid==='P0001');return o&&{st:o.status,hp:o.hasPhoto}})()")
        assert o == {'st': 'out', 'hp': True}, o
        assert pg.evaluate("dbKeys('photos').then(k=>k.length)") == 1
        pg.click('nav button[data-tab=active]'); pg.wait_for_timeout(400)
        pg.locator('#activeList .card', has_text='テスト 太郎').locator('[data-act=return]').click(); pg.wait_for_timeout(300)
        pg.fill('#dlgForm input[name=nurse]', '見本 看護師'); pg.click('#dlgActions button.ok'); pg.wait_for_timeout(1200)
        o = pg.evaluate("(()=>{const o=outings.find(x=>x.pid==='P0001');return {st:o.status,hp:o.hasPhoto,del:!!o.photoDeletedAt}})()")
        assert o == {'st': 'returned', 'hp': False, 'del': True}, o
        assert pg.evaluate("dbKeys('photos').then(k=>k.length)") == 0, '帰院後も写真が残っている'
        assert pg.locator('#activeList .card').count() == 0

        # ---- 再読み込みしても本番用の DB に残る
        pg.reload(); pg.wait_for_timeout(800); pg.click('#startOv'); pg.wait_for_timeout(500)
        assert pg.evaluate('[outings.length,patients.length]') == [1, 1]
        names = pg.evaluate("indexedDB.databases().then(l=>l.map(x=>x.name).sort())")
        assert names == sorted(['gaishutsu_kanri_honban'] + OTHER_DBS), names

        # ---- 旧版・試す用の DB と localStorage は消えも変わりもしない
        after = pg.evaluate(DUMP_DBS, OTHER_DBS)
        assert after == before, ('旧版・試す用の DB が変わった', before, after)
        assert pg.evaluate("localStorage.getItem('gaishutsu_shisaku_theme')") == '{"mode":"dark"}'
        assert pg.evaluate("localStorage.getItem('gaishutsu_theme_mihon')") == 'kyu'
        ctx.close(); b.close()
    srv.shutdown()
    print('errors', errs)
    assert not errs


if __name__ == '__main__':
    main()
