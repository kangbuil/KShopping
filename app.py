import html
import json
from pathlib import Path

import streamlit as st

DATA_FILE = Path(__file__).parent / "items.json"
KEY = "shopping_items"  # 주의: 'items'는 session_state의 메서드명과 충돌


# ---------- 저장 / 불러오기 (F7) ----------
def load_items():
    """items.json 읽기. 파일이 없거나 손상되면 빈 목록."""
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return [
            {"id": int(d["id"]), "name": str(d["name"]), "checked": bool(d["checked"])}
            for d in data
        ]
    except (OSError, ValueError, KeyError, TypeError):
        return []


def save_items():
    DATA_FILE.write_text(
        json.dumps(st.session_state[KEY], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def refresh():
    """파일을 단일 기준으로 삼아 최신 목록을 다시 읽는다 (다른 탭의 변경 반영)."""
    st.session_state[KEY] = load_items()


def init_state():
    refresh()
    if "editing_id" not in st.session_state:
        st.session_state.editing_id = None
    if "flash" not in st.session_state:
        st.session_state.flash = None


# ---------- 콜백 ----------
def add_item():
    refresh()
    name = st.session_state.get("new_item", "").strip()
    if not name:
        st.session_state.flash = "아이템 이름을 입력해주세요."
        return
    items = st.session_state[KEY]
    new_id = max((i["id"] for i in items), default=0) + 1
    items.append({"id": new_id, "name": name, "checked": False})
    save_items()


def toggle_item(item_id):
    refresh()
    for item in st.session_state[KEY]:
        if item["id"] == item_id:
            item["checked"] = st.session_state[f"chk_{item_id}"]
    save_items()


def toggle_all():
    """전체 선택/해제: 체크되면 모두 완료, 해제되면 모두 미완료."""
    refresh()
    value = st.session_state["select_all"]
    for item in st.session_state[KEY]:
        item["checked"] = value
    save_items()


def start_edit(item_id):
    st.session_state.editing_id = item_id


def cancel_edit():
    st.session_state.editing_id = None


def save_edit(item_id):
    name = st.session_state.get(f"edit_{item_id}", "").strip()
    if not name:
        st.session_state.flash = "수정할 이름을 입력해주세요."
        return
    refresh()
    for item in st.session_state[KEY]:
        if item["id"] == item_id:
            item["name"] = name
    st.session_state.editing_id = None
    save_items()


def delete_item(item_id):
    refresh()
    st.session_state[KEY] = [i for i in st.session_state[KEY] if i["id"] != item_id]
    if st.session_state.editing_id == item_id:
        st.session_state.editing_id = None
    save_items()


def clear_checked():
    refresh()
    st.session_state[KEY] = [i for i in st.session_state[KEY] if not i["checked"]]
    save_items()


CSS = """
<style>
.block-container { max-width: 600px; padding-top: 2.5rem; margin: 0 auto; }
h1 { text-align: center; margin-bottom: .5rem; }
/* 모바일에서도 한 행(체크|이름|버튼)이 세로로 쌓이지 않게 */
[data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; align-items: center; gap: .4rem; }
[data-testid="stColumn"] { min-width: 0 !important; }
[data-testid="stForm"] { padding: .6rem; border-radius: 12px; }
.stButton > button, [data-testid="stFormSubmitButton"] > button {
    width: 100%; min-height: 2.5rem; padding: 0 .4rem; border-radius: 10px;
}
.stButton > button, [data-testid="stFormSubmitButton"] > button { white-space: nowrap; }
[data-testid="stColumn"]:has(button) [data-testid="stElementContainer"],
[data-testid="stColumn"]:has(button) .stButton { width: 100% !important; }
[data-testid="stColumn"]:has(button) { min-width: 2.8rem !important; flex: 0 0 auto !important; width: auto !important; }
[data-testid="stColumn"]:has(input[type="text"]) { flex: 1 1 0 !important; }
[data-testid="stColumn"]:has(.item-name) { flex: 1 1 0 !important; }
[data-testid="stColumn"]:has([data-testid="stCheckbox"]) { flex: 0 0 auto !important; width: auto !important; min-width: 2rem !important; }
[data-testid="InputInstructions"] { display: none; }
.item-name { font-size: 1.05rem; word-break: break-word; }
.item-name.done { text-decoration: line-through; opacity: .45; }
.empty-box { text-align: center; padding: 2rem 1rem; border-radius: 12px;
    border: 1px dashed rgba(128,128,128,.5); opacity: .8; }
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


# ---------- 화면 ----------
def render_header():
    st.title("🛒 쇼핑리스트")


def render_add_form():
    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        col1.text_input("새 아이템", key="new_item", label_visibility="collapsed",
                        placeholder="예: 우유 2개")
        col2.form_submit_button("➕ 추가", on_click=add_item, use_container_width=True)


def render_summary():
    items = st.session_state[KEY]
    remain = sum(1 for i in items if not i["checked"])
    total = len(items)
    st.progress((total - remain) / total if total else 0.0)
    st.caption(f"남은 항목 {remain} / 전체 {total}")


def render_row(item):
    iid = item["id"]
    if st.session_state.editing_id == iid:
        with st.form(f"edit_form_{iid}"):
            c1, c2, c3 = st.columns([5, 1, 1])
            c1.text_input("이름 수정", value=item["name"], key=f"edit_{iid}",
                          label_visibility="collapsed")
            c2.form_submit_button("💾", on_click=save_edit, args=(iid,))
            c3.form_submit_button("✖️", on_click=cancel_edit)
        return
    c1, c2, c3, c4 = st.columns([1, 6, 1, 1])
    st.session_state[f"chk_{iid}"] = item["checked"]
    c1.checkbox("완료", key=f"chk_{iid}",
                on_change=toggle_item, args=(iid,), label_visibility="collapsed")
    cls = "item-name done" if item["checked"] else "item-name"
    c2.markdown(f'<div class="{cls}">{html.escape(item["name"])}</div>', unsafe_allow_html=True)
    c3.button("✏️", key=f"edit_btn_{iid}", on_click=start_edit, args=(iid,))
    c4.button("🗑️", key=f"del_btn_{iid}", on_click=delete_item, args=(iid,))


def render_list():
    items = st.session_state[KEY]
    if not items:
        st.markdown('<div class="empty-box">목록이 비었어요.<br>첫 아이템을 추가해보세요 🛍️</div>',
                    unsafe_allow_html=True)
        return
    st.session_state["select_all"] = all(i["checked"] for i in items)
    st.checkbox("전체 선택", key="select_all", on_change=toggle_all)
    for item in items:
        render_row(item)
    st.button("🧹 완료 항목 삭제", on_click=clear_checked,
              disabled=not any(i["checked"] for i in items))


def main():
    st.set_page_config(page_title="쇼핑리스트", page_icon="🛒")
    init_state()
    inject_css()
    render_header()
    render_add_form()
    if st.session_state.flash:
        st.warning(st.session_state.flash)
        st.session_state.flash = None
    render_summary()
    render_list()


if __name__ == "__main__":
    main()
