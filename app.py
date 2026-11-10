import streamlit as st
import database as db
import config
import os
from datetime import datetime

# ========== 页面配置 ==========
st.set_page_config(
    page_title="校园二手教材流转平台",
    page_icon="📚",
    layout="wide"
)

# ========== 初始化 ==========
db.init_db()
_app_config = config.load_config()

# 优先级：Streamlit Cloud 的 secrets > 本地 config.json > 侧边栏手动输入
_secret_key = ""
try:
    _secret_key = st.secrets.get("DEEPSEEK_API_KEY", "")
except Exception:
    _secret_key = ""

if _secret_key:
    st.session_state["api_key"] = _secret_key
elif "api_key" not in st.session_state and _app_config.get("api_key"):
    st.session_state["api_key"] = _app_config["api_key"]

# ========== AI 调用模块 ==========
def call_ai(messages):
    """通用AI调用函数"""
    try:
        from openai import OpenAI
    except ImportError:
        return "⚠️ 请先安装 openai 库：pip install openai"

    api_key = st.session_state.get("api_key", "")
    if not api_key:
        return None, "⚠️ 请在左侧侧边栏填写你的 DeepSeek API Key。"

    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=False
        )
        return response.choices[0].message.content, None
    except Exception as e:
        return None, f"AI调用失败：{str(e)}"


def ai_recommend(user_need, textbook_list):
    """根据用户需求推荐教材"""
    if not textbook_list:
        return "目前没有在售教材，无法推荐。"

    book_info = ""
    for i, book in enumerate(textbook_list, 1):
        book_info += f"{i}. 《{book['title']}》 作者:{book['author']} 课程:{book['course']} 价格:{book['price']}元\n"

    prompt = f"""用户需求：{user_need}

当前在售教材列表：
{book_info}

请扮演校园二手教材推荐助手，从上面的在售教材中，选出最匹配用户需求的1-3本，并给出推荐理由。
要求：
1. 先说明最推荐哪本，为什么匹配
2. 如果有其他备选，也列出来
3. 语言简洁口语化
4. 如果列表中没有匹配的，就说没有合适的，并建议用户发布求购信息
"""

    result, err = call_ai([
        {"role": "system", "content": "你是一个热心的校园二手教材推荐助手。"},
        {"role": "user", "content": prompt}
    ])
    return result if result else f"⚠️ {err}"


def ai_price_suggest(book_title, condition):
    """AI建议二手书合理价格"""
    prompt = f"""书名：《{book_title}》
成色：{condition}

请你根据这本书的市场价和二手教材行情，给出一个合理的二手售价建议。
只返回一个数字（元），不要其他文字。比如：15"""

    result, err = call_ai([
        {"role": "system", "content": "你是一个校园二手教材定价助手，根据书名和成色给出合理二手价格建议。"},
        {"role": "user", "content": prompt}
    ])
    if result:
        try:
            # 提取数字
            import re
            nums = re.findall(r'\d+\.?\d*', result)
            if nums:
                return float(nums[0])
        except:
            pass
    return None


def ai_recommend_for_want(want_book_title, want_course, available_books):
    """AI根据求购需求推荐匹配的在售教材"""
    if not available_books:
        return ""

    book_list = ""
    for i, b in enumerate(available_books, 1):
        book_list += f"{i}. 《{b['title']}》 课程:{b['course']} 价格:{b['price']}元 成色:{b['condition']}\n"

    prompt = f"""求购需求：想要《{want_book_title}》，对应课程：{want_course}

当前在售教材：
{book_list}

请从上面的在售教材中，找出最匹配这个求购需求的1-3本，给出推荐理由。
语言简洁口语化，像同学之间推荐一样。如果没有匹配的，就说没有合适的。"""

    result, err = call_ai([
        {"role": "system", "content": "你是一个校园二手教材推荐助手。"},
        {"role": "user", "content": prompt}
    ])
    return result if result else ""


# ========== 辅助函数 ==========
def save_uploaded_file(uploaded_file, prefix="cover"):
    """保存上传的文件到uploads目录，返回文件路径"""
    if uploaded_file is None:
        return ""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    ext = os.path.splitext(uploaded_file.name)[1]
    filename = f"{prefix}_{timestamp}{ext}"
    filepath = os.path.join(db.UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return filepath


def render_rating_stars(avg, count):
    """渲染评分星级"""
    if count == 0:
        return "暂无评价"
    stars = "⭐" * int(round(avg))
    return f"{stars} {avg}分 ({count}条评价)"


# ========== 页面函数 ==========

def page_home():
    st.title("📚 校园二手教材流转平台")
    st.markdown("### 让每一本教材，在校园里继续旅行")
    st.write("")

    stats = db.get_stats()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📦 在售教材", stats["available"])
    with col2:
        st.metric("🔍 求购信息", stats["open_wants"])
    with col3:
        st.metric("✅ 已成交", stats["sold"])
    with col4:
        st.metric("💰 均价", f"¥{stats['avg_price']}")

    st.write("")
    st.subheader("平台能做什么？")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.info("**卖家发布**\n\n毕业或学完的专业教材，拍照上传封面，AI自动补全信息，一键发布。")
    with col_b:
        st.info("**买家求购**\n\n找不到想要的书？发布求购需求，让有书的同学主动来找你。")
    with col_c:
        st.info("**AI智能匹配**\n\n说你需要什么课的书，AI帮你从在售列表里挑最匹配的那一本。")

    st.write("")
    st.markdown("> 💡 **使用提示**：在左侧侧边栏选择功能页面开始使用。")


def page_publish():
    st.title("📝 发布闲置教材")
    st.write("把你不再需要的教材发布出来，帮助学弟学妹省钱，也给自己回点血。")
    st.write("")

    # 封面上传放最上面
    cover_file = st.file_uploader("📷 上传教材封面照片（可选）", type=["jpg", "jpeg", "png"])
    st.write("")

    # AI价格建议（在form外面）
    ai_price_col1, ai_price_col2 = st.columns([3, 1])
    with ai_price_col1:
        ai_price_title = st.text_input("输入书名，AI帮你建议价格", key="ai_price_title")
    with ai_price_col2:
        st.write("")
        if st.button("🤖 AI建议价格", use_container_width=True):
            if ai_price_title.strip():
                with st.spinner("AI正在分析合理价格..."):
                    suggested = ai_price_suggest(ai_price_title.strip(), "九成新")
                    if suggested:
                        st.info(f"💡 AI建议价格：约 ¥{suggested}")
                    else:
                        st.warning("⚠️ AI暂时无法建议价格")
            else:
                st.warning("请先输入书名")

    st.write("")

    with st.form("publish_form", clear_on_submit=True):
        title = st.text_input("教材名称 *", placeholder="例如：高等数学（第七版上册）")
        course = st.text_input("对应课程", placeholder="例如：高等数学A")

        col1, col2 = st.columns(2)
        with col1:
            price = st.number_input("售价（元）*", min_value=0.0, value=10.0, step=1.0)
            condition = st.selectbox("成色 *", ["全新", "九成新", "八成新", "七成新", "有笔记/划线"])
        with col2:
            campus = st.selectbox("所在校区", ["麦庐园", "蛟桥园", "枫林园", "其他"])
            student_id = st.text_input("学号（可选）", placeholder="填写学号增加信任度")

        contact = st.text_input("联系方式 *", placeholder="微信号或手机号")
        seller_note = st.text_input("备注（可选）", placeholder="例如：有笔记、附赠资料等")

        submitted = st.form_submit_button("🚀 发布教材", use_container_width=True)

        if submitted:
            if not title.strip():
                st.error("⚠️ 请填写教材名称")
            elif price <= 0:
                st.error("⚠️ 请填写合理的售价")
            elif not contact.strip():
                st.error("⚠️ 请填写联系方式")
            else:
                cover_path = save_uploaded_file(cover_file, "cover") if cover_file else ""
                new_id = db.add_textbook(
                    title=title.strip(),
                    course=course.strip(),
                    price=price,
                    condition=condition,
                    contact=contact.strip(),
                    student_id=student_id.strip(),
                    campus=campus,
                    description=seller_note.strip(),
                    cover_path=cover_path
                )
                st.success(f"✅ 发布成功！教材编号 #{new_id}")
                st.balloons()


def page_publish_want():
    st.title("🔍 发布求购信息")
    st.write("找不到你需要的教材？发布一条求购信息，让有书的同学主动来找你。")
    st.write("")

    with st.form("want_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            book_title = st.text_input("想要的教材名称 *", placeholder="例如：高等数学（第七版下册）")
            course = st.text_input("对应课程", placeholder="例如：高等数学A")
            author_required = st.text_input("要求作者/版本", placeholder="例如：同济大学第七版")
        with col2:
            max_price = st.number_input("心理价位（元）", min_value=0.0, value=15.0, step=1.0)
            condition_required = st.selectbox("成色要求", ["不限", "全新", "九成新", "八成新", "有笔记也可以"])
            student_id = st.text_input("学号（校园认证）", placeholder="填写学号增加信任度")
            campus = st.selectbox("所在校区", ["麦庐园", "蛟桥园", "枫林园", "其他"])

        note = st.text_area("补充说明", placeholder="比如：上下册一起要、只要课后习题解答等等")
        contact = st.text_input("联系方式 *", placeholder="微信号或手机号")

        submitted = st.form_submit_button("📢 发布求购", use_container_width=True)

        if submitted:
            if not book_title.strip():
                st.error("⚠️ 请填写你想要的教材名称")
            elif not contact.strip():
                st.error("⚠️ 请填写联系方式")
            else:
                new_id = db.add_want(
                    book_title=book_title.strip(),
                    course=course.strip(),
                    author_required=author_required.strip(),
                    max_price=max_price,
                    condition_required=condition_required,
                    contact=contact.strip(),
                    student_id=student_id.strip(),
                    campus=campus,
                    note=note.strip()
                )
                st.success(f"✅ 求购信息发布成功！编号 #{new_id}")
                st.info("有这本书的同学会在「浏览教材 → 求购信息」里看到你的需求，主动联系你。")
                st.balloons()

                # 直接列出匹配的在售教材卡片
                available = db.get_all_textbooks(status="available")
                if available:
                    # 按关键词筛选相关的书
                    matched = []
                    keywords = book_title.strip()
                    if course:
                        keywords += " " + course
                    for b in available:
                        # 简单关键词匹配
                        if (keywords and (keywords in b.get('title','') or keywords in b.get('course',''))) or \
                           (any(kw in b.get('title','') or kw in b.get('course','') for kw in keywords.split() if len(kw) > 1)):
                            matched.append(b)

                    # 如果没匹配到，就取前5本
                    if not matched:
                        matched = available[:5]
                    else:
                        matched = matched[:5]

                    if matched:
                        st.write("")
                        st.markdown(f"### 📚 你可能在找的 {len(matched)} 本教材")
                        st.caption("以下是在售列表中与你需求相关的教材，直接联系卖家就行～")

                        for book in matched:
                            with st.container(border=True):
                                c1, c2, c3 = st.columns([1, 3, 1])
                                with c1:
                                    if book.get('cover_path') and os.path.exists(book['cover_path']):
                                        st.image(book['cover_path'], use_container_width=True)
                                    else:
                                        st.image("https://via.placeholder.com/120x160?text=Book", use_container_width=True)
                                with c2:
                                    st.markdown(f"**《{book['title']}》**")
                                    if book.get('course'):
                                        st.caption(f"课程：{book['course']}")
                                    if book.get('campus'):
                                        st.caption(f"📍 {book['campus']}")
                                    if book.get('description'):
                                        st.caption(book['description'])
                                with c3:
                                    st.markdown(f"**¥{book['price']}**")
                                    st.caption(f"成色：{book['condition']}")
                                    st.caption(f"📞 {book['contact']}")
                            st.write("")

                        # AI推荐理由
                        with st.spinner("AI正在生成推荐理由..."):
                            rec = ai_recommend_for_want(book_title, course, matched)
                            if rec:
                                st.write("")
                                st.markdown("### 🤖 AI推荐说明")
                                st.info(rec)


def page_browse():
    st.title("🔍 浏览教材市场")
    st.write("看看大家都在卖什么、买什么，找到适合你的那本书。")
    st.write("")

    tab_sell, tab_buy = st.tabs(["📦 在售教材（卖家）", "🔍 求购信息（买家）"])

    with tab_sell:
        st.subheader("在售教材列表")
        with st.expander("⚙️ 筛选条件", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                keyword = st.text_input("关键词", placeholder="书名/作者/课程", key="sell_kw")
            with col2:
                all_courses = db.get_all_courses()
                course_options = ["全部"] + all_courses
                course = st.selectbox("课程", course_options, key="sell_course")
            with col3:
                price_range = st.select_slider("价格区间",
                    options=["不限", "0-10元", "10-20元", "20-30元", "30元以上"],
                    value="不限", key="sell_price")
            with col4:
                cond = st.selectbox("成色",
                    ["不限", "全新", "九成新", "八成新", "七成新", "有笔记/划线"],
                    key="sell_cond")
                campus_filter = st.selectbox("校区", ["全部", "麦庐园", "蛟桥园", "枫林园", "其他"], key="sell_campus")

        min_p, max_p = None, None
        if price_range == "0-10元":
            min_p, max_p = 0, 10
        elif price_range == "10-20元":
            min_p, max_p = 10, 20
        elif price_range == "20-30元":
            min_p, max_p = 20, 30
        elif price_range == "30元以上":
            min_p = 30

        course_param = None if course == "全部" else course
        cond_param = None if cond == "不限" else cond
        keyword_param = keyword.strip() if keyword.strip() else None

        campus_param = None if campus_filter == "全部" else campus_filter
        results = db.search_textbooks(
            keyword=keyword_param, course=course_param,
            min_price=min_p, max_price=max_p, condition=cond_param,
            campus=campus_param
        )

        st.write(f"共找到 **{len(results)}** 本在售教材")
        st.write("")

        if not results:
            st.info("没有找到符合条件的教材，试试放宽筛选条件吧～")
        else:
            for book in results:
                rating = db.get_user_rating(book['contact'])
                with st.container(border=True):
                    c1, c2, c3 = st.columns([1, 3, 1])
                    with c1:
                        if book.get('cover_path') and os.path.exists(book['cover_path']):
                            st.image(book['cover_path'], use_container_width=True)
                        else:
                            st.image("https://via.placeholder.com/120x160?text=No+Cover",
                                     use_container_width=True)
                    with c2:
                        st.markdown(f"### 《{book['title']}》")
                        meta_parts = []
                        if book['author']:
                            meta_parts.append(f"👤 {book['author']}")
                        if book['publisher']:
                            meta_parts.append(f"🏛️ {book['publisher']}")
                        if book['edition']:
                            meta_parts.append(f"📖 {book['edition']}")
                        if book['course']:
                            meta_parts.append(f"📚 {book['course']}")
                        st.markdown(" ｜ ".join(meta_parts))
                        if book['description']:
                            st.write(f"📝 {book['description']}")
                        if book['seller_note']:
                            st.caption(f"卖家备注：{book['seller_note']}")
                    with c3:
                        st.markdown(f"## ¥{book['price']}")
                        st.caption(f"成色：{book['condition']}")
                        st.caption(f"发布：{book['created_at'][:10]}")
                        st.caption(f"📞 {book['contact']}")
                        if book.get('campus'):
                            st.caption(f"📍 {book['campus']}")
                        if book.get('student_id'):
                            st.caption(f"🎓 学号认证：{book['student_id']}")
                        st.caption(render_rating_stars(rating['avg'], rating['count']))
                st.write("")

    with tab_buy:
        st.subheader("求购信息列表")
        st.caption("如果你有这些书想卖，可以直接联系求购的同学～")
        st.write("")

        want_keyword = st.text_input("搜索求购", placeholder="输入书名或课程关键词", key="want_kw")
        want_kw = want_keyword.strip() if want_keyword.strip() else None
        wants = db.search_wants(keyword=want_kw)

        st.write(f"共 **{len(wants)}** 条求购信息")
        st.write("")

        if not wants:
            st.info("目前没有求购信息，你可以去「发布求购」页面发布一条～")
        else:
            for w in wants:
                rating = db.get_user_rating(w['contact'])
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"### 🔍 求购：《{w['book_title']}》")
                        meta_parts = []
                        if w['course']:
                            meta_parts.append(f"📚 {w['course']}")
                        if w['author_required']:
                            meta_parts.append(f"👤 {w['author_required']}")
                        if w['condition_required']:
                            meta_parts.append(f"📖 {w['condition_required']}")
                        st.markdown(" ｜ ".join(meta_parts))
                        if w['note']:
                            st.write(f"📝 {w['note']}")
                    with c2:
                        if w['max_price']:
                            st.markdown(f"## 预算≤¥{w['max_price']}")
                        else:
                            st.markdown(f"## 价格可议")
                        st.caption(f"发布：{w['created_at'][:10]}")
                        st.caption(f"📞 {w['contact']}")
                        if w.get('student_id'):
                            st.caption(f"🎓 学号认证：{w['student_id']}")
                        st.caption(render_rating_stars(rating['avg'], rating['count']))
                st.write("")


def page_ai():
    st.title("🤖 AI 智能教材匹配")
    st.write("不知道哪本教材适合你？把你的需求告诉AI，它帮你从在售列表里挑。")
    st.write("")

    user_need = st.text_area(
        "描述你的需求",
        placeholder="例如：我下学期要学概率论与数理统计，想要一本同济大学版的，不要太贵，有笔记也没关系",
        height=100
    )

    if st.button("✨ 让AI帮我找教材", type="primary", use_container_width=True):
        if not user_need.strip():
            st.warning("请先描述一下你需要什么教材～")
            return

        with st.spinner("AI正在分析在售教材并为你匹配..."):
            available = db.get_all_textbooks(status="available")
            if not available:
                st.info("目前没有在售教材")
            else:
                # 先按关键词筛选相关的书
                matched = []
                for b in available:
                    title = b.get('title', '')
                    course = b.get('course', '')
                    desc = b.get('description', '')
                    # 简单关键词匹配：用户需求里的词出现在书名/课程/描述里
                    need_words = [w for w in user_need.split() if len(w) > 1]
                    if any(w in title or w in course or w in desc for w in need_words):
                        matched.append(b)

                # 如果没匹配到，就取前6本
                if not matched:
                    matched = available[:6]
                else:
                    matched = matched[:6]

                # 显示匹配的教材卡片
                st.write("")
                st.markdown(f"### 📚 为你找到的 {len(matched)} 本相关教材")
                st.caption("直接联系卖家就行～")

                for book in matched:
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([1, 3, 1])
                        with c1:
                            if book.get('cover_path') and os.path.exists(book['cover_path']):
                                st.image(book['cover_path'], use_container_width=True)
                            else:
                                st.image("https://via.placeholder.com/120x160?text=Book", use_container_width=True)
                        with c2:
                            st.markdown(f"**《{book['title']}》**")
                            meta = []
                            if book.get('course'):
                                meta.append(f"课程：{book['course']}")
                            if book.get('campus'):
                                meta.append(f"📍 {book['campus']}")
                            st.caption(" ｜ ".join(meta))
                            if book.get('description'):
                                st.caption(book['description'])
                        with c3:
                            st.markdown(f"**¥{book['price']}**")
                            st.caption(f"成色：{book['condition']}")
                            st.caption(f"📞 {book['contact']}")
                    st.write("")

                # AI推荐理由
                st.write("")
                st.markdown("### 🤖 AI推荐说明")
                result = ai_recommend(user_need, matched)
                if result:
                    st.info(result)

    st.write("")
    st.markdown("---")
    st.caption("💡 AI基于DeepSeek大模型生成，推荐结果仅供参考，请自行确认教材版本和课程要求。")


def page_manage():
    st.title("📦 我的发布与评价")
    st.write("输入你的联系方式，查看和管理你发布的信息，以及收到的评价。")
    st.write("")

    my_contact = st.text_input("你的联系方式", placeholder="输入你发布时填写的微信号/手机号")

    if not my_contact:
        return

    contact_clean = my_contact.strip()
    rating = db.get_user_rating(contact_clean)

    # 显示我的信誉
    st.info(f"📊 我的信誉：{render_rating_stars(rating['avg'], rating['count'])}")
    st.write("")

    tab_sell, tab_buy, tab_review = st.tabs(["📦 我卖的书", "🔍 我求的书", "⭐ 我的评价"])

    with tab_sell:
        my_books = db.get_textbooks_by_contact(contact_clean)
        st.write(f"共 **{len(my_books)}** 条卖书信息")
        st.write("")

        if not my_books:
            st.info("没有找到你发布的卖书记录")
        else:
            for book in my_books:
                status_badge = "🟢 在售中" if book['status'] == 'available' else "🔴 已售出"
                with st.container(border=True):
                    st.markdown(f"**#{book['id']} 《{book['title']}》** — {status_badge}")
                    st.caption(f"售价：¥{book['price']} ｜ 成色：{book['condition']} ｜ 发布：{book['created_at'][:10]}")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if book['status'] == 'available':
                            if st.button(f"标记已售出", key=f"sell_{book['id']}"):
                                db.update_status(book['id'], 'sold')
                                st.rerun()
                        else:
                            if st.button(f"重新上架", key=f"relist_{book['id']}"):
                                db.update_status(book['id'], 'available')
                                st.rerun()
                    with col2:
                        if st.button(f"🗑️ 删除", key=f"del_{book['id']}"):
                            db.delete_textbook(book['id'])
                            st.rerun()
                    with col3:
                        if book['status'] == 'sold':
                            if st.button(f"⭐ 去评价买家", key=f"review_{book['id']}"):
                                st.session_state['review_target'] = {
                                    'reviewee': book['contact'],
                                    'book': book['title']
                                }
                                st.rerun()
                st.write("")

    with tab_buy:
        all_wants = db.get_all_wants()
        my_wants = [w for w in all_wants if w['contact'] == contact_clean]

        st.write(f"共 **{len(my_wants)}** 条求购信息")
        st.write("")

        if not my_wants:
            st.info("没有找到你发布的求购记录")
        else:
            for w in my_wants:
                status_badge = "🟢 求购中" if w['status'] == 'open' else "✅ 已找到"
                with st.container(border=True):
                    st.markdown(f"**#{w['id']} 求购《{w['book_title']}》** — {status_badge}")
                    price_str = f"预算≤¥{w['max_price']}" if w['max_price'] else "价格可议"
                    st.caption(f"{price_str} ｜ 发布：{w['created_at'][:10]}")

                    col1, col2 = st.columns(2)
                    with col1:
                        if w['status'] == 'open':
                            if st.button(f"标记已找到", key=f"want_done_{w['id']}"):
                                db.update_want_status(w['id'], 'closed')
                                st.rerun()
                        else:
                            if st.button(f"重新求购", key=f"want_open_{w['id']}"):
                                db.update_want_status(w['id'], 'open')
                                st.rerun()
                    with col2:
                        if st.button(f"🗑️ 删除", key=f"want_del_{w['id']}"):
                            db.delete_want(w['id'])
                            st.rerun()
                st.write("")

    with tab_review:
        st.subheader("收到的评价")
        my_reviews = db.get_reviews_for_user(contact_clean)

        if not my_reviews:
            st.info("还没有收到评价，交易完成后对方可以给你打分评价～")
        else:
            for r in my_reviews:
                with st.container(border=True):
                    stars = "⭐" * r['rating']
                    st.markdown(f"**{stars} {r['rating']}分** — 来自 {r['reviewer_name'] or r['reviewer_contact']}")
                    if r['related_book']:
                        st.caption(f"关于《{r['related_book']}》")
                    if r['comment']:
                        st.write(r['comment'])
                    st.caption(f"{r['created_at'][:10]}")
                st.write("")

    # 评价弹窗（如果有目标评价人）
    if 'review_target' in st.session_state:
        target = st.session_state['review_target']
        st.write("")
        st.markdown("---")
        st.subheader(f"⭐ 评价交易对象：{target['reviewee']}")

        with st.form("review_form"):
            reviewer_name = st.text_input("你的昵称（可选）", placeholder="怎么称呼你")
            rating_val = st.slider("评分", 1, 5, 5)
            comment = st.text_area("评价内容", placeholder="对方的书怎么样？交易顺利吗？")
            reviewee_name = st.text_input("对方昵称（可选）", placeholder="怎么称呼对方")

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("✅ 提交评价", use_container_width=True):
                    db.add_review(
                        reviewer_contact=contact_clean,
                        reviewer_name=reviewer_name.strip(),
                        reviewee_contact=target['reviewee'],
                        reviewee_name=reviewee_name.strip(),
                        rating=rating_val,
                        comment=comment.strip(),
                        related_book=target['book']
                    )
                    del st.session_state['review_target']
                    st.success("✅ 评价提交成功！")
                    st.rerun()
            with col2:
                if st.form_submit_button("❌ 取消", use_container_width=True):
                    del st.session_state['review_target']
                    st.rerun()


# ========== 侧边栏导航 ==========
st.sidebar.title("📚 教材流转平台")
st.sidebar.write("")

page = st.sidebar.radio(
    "功能导航",
    ["🏠 首页", "📝 发布卖书", "🔍 发布求购", "🔍 浏览教材市场",
     "🤖 AI智能匹配", "📦 我的发布"],
    index=0
)

st.sidebar.write("")
st.sidebar.write("---")
st.sidebar.subheader("⚙️ AI 设置")
api_key_input = st.sidebar.text_input(
    "DeepSeek API Key",
    type="password",
    placeholder="sk-...",
    help="在 https://platform.deepseek.com/ 获取"
)
if api_key_input:
    st.session_state["api_key"] = api_key_input
    # 保存到配置文件（云端只读时静默失败）
    _app_config["api_key"] = api_key_input
    config.save_config(_app_config)
    st.sidebar.success("API Key 已保存")

if st.session_state.get("api_key"):
    st.sidebar.caption("✅ 已配置 API Key，AI 功能可用")

st.sidebar.write("")
st.sidebar.caption("© 2026 校园二手教材流转平台\nAI应用开发课程期中项目")

# ========== 路由 ==========
if page == "🏠 首页":
    page_home()
elif page == "📝 发布卖书":
    page_publish()
elif page == "🔍 发布求购":
    page_publish_want()
elif page == "🔍 浏览教材市场":
    page_browse()
elif page == "🤖 AI智能匹配":
    page_ai()
elif page == "📦 我的发布":
    page_manage()
