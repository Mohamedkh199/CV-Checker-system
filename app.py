import streamlit as st
from PyPDF2 import PdfReader
from docx import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import re
from datetime import datetime

# إعداد الصفحة
st.set_page_config(
    page_title="ATS AI Pro | CV Checker",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# إخفاء عناصر Streamlit الافتراضية
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    </style>
""", unsafe_allow_html=True)

# حالة الجلسة
if 'scan_history' not in st.session_state:
    st.session_state.scan_history = []
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False  # الوضع الفاتح هو الافتراضي
if 'missing_kws' not in st.session_state:
    st.session_state.missing_kws = []
if 'show_results' not in st.session_state:
    st.session_state.show_results = False

# ========== تحديد مصفوفة الألوان بناءً على حالة الثيم الحالية ==========
if st.session_state.dark_mode:
    BG = "#020617"
    MAIN_TEXT = "#F8FAFC"
    INPUT_BG = "#1E293B"
    INPUT_TEXT = "#F8FAFC"
    UPLOADER_BG = "#2D2F3F"        # رمادي غامق أنيق
    UPLOADER_BORDER = "#6B7280"     # رمادي متوسط
    HOVER_BORDER = "#9CA3AF"
    TEXTAREA_BG = "#1E293B"
    BADGE_FOUND_BG = "rgba(34,197,94,0.15)"
    BADGE_MISSING_BG = "rgba(239,68,68,0.15)"
    
    # ألوان السايدبار بالوضع الداكن
    SIDEBAR_BG = "linear-gradient(145deg, #0B1120 0%, #0F172A 100%)"
    SIDEBAR_TEXT = "#F1F5F9"
    SIDEBAR_BORDER = "1px solid #1E293B"
    LOGO_COLOR = "#38BDF8"
    LOGO_SUB = "#94A3B8"
    MUTED_TEXT = "#94A3B8"
    TOGGLE_CONTAINER_BG = "rgba(30, 41, 59, 0.4)"
else:
    BG = "#F8FAFC"
    MAIN_TEXT = "#0A0A0A"
    INPUT_BG = "#FFFFFF"
    INPUT_TEXT = "#0A0A0A"
    UPLOADER_BG = "#F3F4F6"        # رمادي فاتح نظيف
    UPLOADER_BORDER = "#D1D5DB"     # رمادي باهت
    HOVER_BORDER = "#9CA3AF"
    TEXTAREA_BG = "#FFFFFF"
    BADGE_FOUND_BG = "rgba(34,197,94,0.1)"
    BADGE_MISSING_BG = "rgba(239,68,68,0.1)"
    
    # ألوان السايدبار بالوضع النهاري
    SIDEBAR_BG = "linear-gradient(145deg, #F1F5F9 0%, #E2E8F0 100%)"
    SIDEBAR_TEXT = "#1E293B"
    SIDEBAR_BORDER = "1px solid #CBD5E1"
    LOGO_COLOR = "#1E40AF"
    LOGO_SUB = "#64748B"
    MUTED_TEXT = "#64748B"
    TOGGLE_CONTAINER_BG = "#FFFFFF"

# ========== بناء السايدبار وعناصر التحكم ==========
with st.sidebar:
    st.markdown("""
        <div class="sidebar-logo">
            <h2>🎯 ATS AI PRO</h2>
            <p>Enterprise Decision Product</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="theme-toggle-container">
            <div class="theme-title">🎨 UI DISPLAY THREAD</div>
        </div>
    """, unsafe_allow_html=True)
    
    # التبديل المباشر بدون callback - Streamlit يعيد التشغيل تلقائياً
    st.toggle(
        "🌙 Dark Mode / الوضع الداكن", 
        value=st.session_state.dark_mode, 
        key="dark_mode"
    )
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    st.markdown("🧭 **Navigation / التنقل**")
    page = st.radio(
        "Navigation",
        ["Dashboard / لوحة التحكم", "Analytics History / سجل الفحص", "Settings / الإعدادات"],
        label_visibility="collapsed"
    )

# ========== حقن الـ CSS ==========
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap');
    
    html, body, .stApp {{
        font-family: 'Cairo', sans-serif !important;
        background-color: {BG} !important;
    }}
    
    [data-testid="stSidebar"] {{
        background: {SIDEBAR_BG} !important;
        border-right: {SIDEBAR_BORDER} !important;
        box-shadow: 4px 0 25px rgba(0,0,0,0.02);
    }}
    [data-testid="stSidebar"] * {{
        color: {SIDEBAR_TEXT} !important;
    }}
    
    .sidebar-logo {{
        text-align: center;
        padding: 1.5rem 1rem;
        margin-bottom: 1rem;
        border-bottom: {SIDEBAR_BORDER};
    }}
    .sidebar-logo h2 {{
        margin: 0;
        font-size: 1.7rem;
        font-weight: 800;
        color: {LOGO_COLOR} !important;
        letter-spacing: -0.5px;
    }}
    .sidebar-logo p {{
        margin: 6px 0 0;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        color: {LOGO_SUB} !important;
    }}
    
    .theme-toggle-container {{
        background-color: {TOGGLE_CONTAINER_BG};
        padding: 10px 14px;
        border-radius: 14px;
        border: {SIDEBAR_BORDER};
        margin-top: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02);
    }}
    .theme-title {{
        font-size: 0.75rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px;
        color: {LOGO_SUB} !important;
    }}
    
    [data-testid="stSidebar"] .stToggle div[data-testid="stWidgetLabel"] p {{
        font-weight: 600 !important;
        font-size: 0.9rem !important;
    }}
    
    .stRadio > div {{
        gap: 6px;
    }}
    .stRadio label {{
        font-weight: 600;
        padding: 10px 14px;
        border-radius: 12px;
        transition: all 0.2s ease;
    }}
    .stRadio label:hover {{
        background: {'rgba(30,41,59,0.06)' if not st.session_state.dark_mode else 'rgba(255,255,255,0.05)'};
    }}
    
    hr {{
        margin: 1.2rem 0;
        border-color: {SIDEBAR_BORDER} !important;
        opacity: 0.5;
    }}
    
    .stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp h4, 
    .stApp label, .stApp span, .stApp div, .stMarkdown {{
        color: {MAIN_TEXT} !important;
    }}
    
    /* ===== صندوق رفع الملفات Drag & Drop - رمادي مرتب ===== */
    [data-testid="stFileUploader"] > div {{
        background-color: {UPLOADER_BG} !important;
        border: 2px dashed {UPLOADER_BORDER} !important;
        border-radius: 20px !important;
        padding: 1.2rem !important;
        transition: all 0.25s ease;
        text-align: center;
    }}
    [data-testid="stFileUploader"] > div:hover {{
        border-color: {HOVER_BORDER} !important;
        background-color: {'#E5E7EB' if not st.session_state.dark_mode else '#374151'} !important;
        transform: scale(1.01);
    }}
    [data-testid="stFileUploader"] [data-testid="stUploadDropzoneInstructions"] span,
    [data-testid="stFileUploader"] small, 
    [data-testid="stFileUploader"] p {{
        color: {MAIN_TEXT} !important;
        font-weight: 600 !important;
    }}
    [data-testid="stFileUploader"] button {{
        background: linear-gradient(95deg, #2563EB, #1E40AF) !important;
        color: white !important;
        border-radius: 40px !important;
        padding: 0.4rem 1.2rem !important;
        font-weight: 600;
        border: none;
    }}
    [data-testid="stFileUploader"] button * {{
        color: white !important;
    }}
    
    .stTextArea textarea {{
        background-color: {TEXTAREA_BG} !important;
        color: {INPUT_TEXT} !important;
        border: 2px solid {UPLOADER_BORDER} !important;
        border-radius: 20px !important;
        font-size: 1rem;
        padding: 1rem;
        height: 180px;
    }}
    .stTextArea textarea::placeholder {{
        color: {MUTED_TEXT} !important;
        opacity: 0.85 !important;
    }}
    .stTextArea textarea:focus {{
        border-color: #10B981 !important;
        box-shadow: 0 0 0 2px rgba(16,185,129,0.2);
    }}
    
    .hero-section {{
        text-align: center;
        background: linear-gradient(115deg, #1E40AF, #0F172A, #020617);
        padding: 2rem;
        border-radius: 28px;
        margin-bottom: 2rem;
    }}
    .hero-section h1, .hero-section p {{
        color: white !important;
    }}
    
    .stButton > button {{
        background: linear-gradient(95deg, #2563EB, #1E40AF);
        color: white !important;
        border: none;
        border-radius: 40px;
        padding: 0.6rem 2rem;
        font-weight: 700;
        font-size: 1.1rem;
        width: auto;
        min-width: 260px;
        margin: 0 auto;
        display: block;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }}
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 12px 22px rgba(37,99,235,0.4);
    }}
    
    .badge-found {{
        background: {BADGE_FOUND_BG};
        border: 1px solid #22c55e;
        color: #22c55e !important;
        padding: 0.3rem 1rem;
        border-radius: 30px;
        font-weight: 600;
        display: inline-block;
        margin: 4px;
    }}
    .badge-missing {{
        background: {BADGE_MISSING_BG};
        border: 1px solid #ef4444;
        color: #ef4444 !important;
        padding: 0.3rem 1rem;
        border-radius: 30px;
        font-weight: 600;
        display: inline-block;
        margin: 4px;
    }}
    
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] > div, [data-testid="stMetricValue"] span {{
        color: {MAIN_TEXT} !important;
    }}
    </style>
""", unsafe_allow_html=True)

# دوال المعالجة
def extract_text_from_pdf(file):
    reader = PdfReader(file)
    return "".join([page.extract_text() or "" for page in reader.pages])

def extract_text_from_docx(file):
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def clean_text(text):
    text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def detect_sections(text):
    sections = {
        "Experience / الخبرات": ["experience", "work", "history", "employment", "الخبرات", "الخبرة", "العمل"],
        "Education / التعليم": ["education", "university", "degree", "جامعة", "التعليم", "الشهادات"],
        "Skills / المهارات": ["skills", "technologies", "languages", "المهارات", "القدرات"],
        "Projects / المشاريع": ["projects", "portfolio", "المشاريع", "مشاريع"]
    }
    detected = {}
    text_lower = text.lower()
    for section, keywords in sections.items():
        detected[section] = any(kw in text_lower for kw in keywords)
    return detected

def analyze_keywords(resume_text, jd_text):
    resume_text = clean_text(resume_text).lower()
    jd_text = clean_text(jd_text).lower()
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1,2))
    try:
        tfidf_matrix = vectorizer.fit_transform([resume_text, jd_text])
        feature_names = vectorizer.get_feature_names_out()
        jd_vector = tfidf_matrix[1].toarray().flatten()
        important_indices = jd_vector.argsort()[-15:][::-1]
        top_keywords = [feature_names[i] for i in important_indices if jd_vector[i] > 0]
    except:
        top_keywords = list(set(jd_text.split()[:12]))
    found = [kw for kw in top_keywords if kw in resume_text]
    missing = [kw for kw in top_keywords if kw not in resume_text]
    return found, missing

# ========== المحتوى حسب الصفحة ==========
if page == "Dashboard / لوحة التحكم":
    st.markdown("""
        <div class="hero-section">
            <h1>🎯 ATS AI ENTERPRISE SYSTEM</h1>
            <p>منصة فحص السير الذاتية بالذكاء الاصطناعي بمعايير الشركات الكبرى</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("### 📄 السيرة الذاتية (CV)")
        uploaded_cv = st.file_uploader(
            "ارفع ملف PDF أو Word",
            type=["pdf", "docx"],
            key="cv",
            help="الحد الأقصى 200 ميجابايت"
        )
    
    with col2:
        st.markdown("### 📋 الوصف الوظيفي (JD)")
        jd_text = st.text_area(
            "أدخل تفاصيل الوظيفة هنا",
            height=180,
            placeholder="مثال: مطلوب مطور بايثون مع خبرة في Streamlit، تحليل بيانات، تعلم آلة..."
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    analyze = st.button("⚡ بدء الفحص والتحليل الذكي", use_container_width=False)
    
    if analyze:
        if uploaded_cv is not None and jd_text.strip() != "":
            with st.spinner("جاري التحليل الذكي..."):
                if uploaded_cv.type == "application/pdf":
                    resume_text = extract_text_from_pdf(uploaded_cv)
                else:
                    resume_text = extract_text_from_docx(uploaded_cv)
                
                if not resume_text.strip() or len(resume_text.strip()) < 50:
                    st.error("⚠️ فشل قراءة النص من السيرة الذاتية. تأكد من أن الملف يحتوي على نص قابل للقراءة.")
                else:
                    vectorizer = TfidfVectorizer(stop_words=None, ngram_range=(1,2))
                    tfidf_matrix = vectorizer.fit_transform([clean_text(resume_text), clean_text(jd_text)])
                    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                    
                    st.session_state.score = round(similarity * 100)
                    st.session_state.found_kws, st.session_state.missing_kws = analyze_keywords(resume_text, jd_text)
                    st.session_state.detected_sections = detect_sections(resume_text)
                    found_sections_count = sum(1 for status in st.session_state.detected_sections.values() if status)
                    st.session_state.integrity_score = round((found_sections_count / len(st.session_state.detected_sections)) * 100)
                    st.session_state.show_results = True
                    
                    st.session_state.scan_history.append({
                        "التاريخ": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "اسم الملف": uploaded_cv.name,
                        "معدل التطابق": f"{st.session_state.score}%",
                        "سلامة البنية": f"{st.session_state.integrity_score}%"
                    })
        else:
            st.warning("⚠️ يرجى رفع السيرة الذاتية وإدخال الوصف الوظيفي أولاً.")
    
    if st.session_state.show_results:
        st.markdown("---")
        st.markdown("### 📊 لوحة تحكم المؤسسة")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("نسبة التوافق مع ATS", f"{st.session_state.score}%")
        c2.metric("الكلمات المفاتيح الموجودة", len(st.session_state.found_kws))
        c3.metric("الكلمات المفقودة", len(st.session_state.missing_kws))
        c4.metric("سلامة الهيكل", f"{st.session_state.integrity_score}%")
        st.progress(st.session_state.score / 100)
        st.markdown("<br>", unsafe_allow_html=True)
        
        res_col1, res_col2 = st.columns(2, gap="large")
        with res_col1:
            st.markdown("### 🔍 فحص الأقسام")
            for sec, found in st.session_state.detected_sections.items():
                if found:
                    st.success(f"✓ {sec}")
                else:
                    st.error(f"✗ {sec}")
        with res_col2:
            st.markdown("### 🔑 تحليل الكلمات المفتاحية")
            st.markdown("**✅ المتطابقة:**")
            if st.session_state.found_kws:
                st.markdown("".join([f'<span class="badge-found">{kw}</span>' for kw in st.session_state.found_kws[:6]]), unsafe_allow_html=True)
            else:
                st.caption("لا توجد مهارات متطابقة")
            st.markdown("**❌ المفقودة والمطلوبة:**")
            if st.session_state.missing_kws:
                st.markdown("".join([f'<span class="badge-missing">{kw}</span>' for kw in st.session_state.missing_kws[:6]]), unsafe_allow_html=True)
            else:
                st.caption("ممتاز! جميع الكلمات موجودة.")
        
        st.markdown("---")
        st.markdown("### ✨ توصيات الذكاء الاصطناعي لتحسين السيرة")
        if st.button("💡 اقتراح جمل احترافية"):
            if st.session_state.missing_kws:
                st.info(f"🔹 أضف في ملخص المهارات: خبرة في {', '.join(st.session_state.missing_kws[:3])} وتطبيقها في مشاريع قابلة للتوسع.")
                st.success(f"🔹 في الخبرات العملية: قم بدمج {st.session_state.missing_kws[0] if st.session_state.missing_kws else 'التقنيات الأساسية'} مما حسن الأداء بنسبة 20%.")
            else:
                st.success("سيرتك الذاتية متوافقة بشكل ممتاز، لا حاجة لتعديلات.")

elif page == "Analytics History / سجل الفحص":
    st.markdown("### 📜 سجل عمليات الفحص")
    if st.session_state.scan_history:
        df_history = pd.DataFrame(st.session_state.scan_history)
        st.dataframe(df_history.iloc[::-1], use_container_width=True)
    else:
        st.info("لا توجد عمليات فحص بعد. قم بتحليل سيرة ذاتية أولاً.")

elif page == "Settings / الإعدادات":
    st.markdown("### ⚙️ إعدادات النظام المتقدمة")
    st.checkbox("تمكين تحليل N-gram (ثنائيات الكلمات)", value=True)
    st.checkbox("تصفية الكلمات الشائعة (Stopwords)", value=True)
    st.slider("الحد الأدنى لنسبة القبول", 0, 100, 75)
    st.info("جميع الإعدادات تعمل بشكل افتراضي على أعلى دقة.")