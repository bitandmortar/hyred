# 🎨 CUSTOM FONTS & TOOLS INTEGRATION

**Status:** ✅ **COMPLETE**  
**Date:** March 21, 2026  
**Fonts Location:** `/Volumes/OMNI_01/10_SOURCE/50_Ops/FONTS/`  
**Tools Integrated:** Reactive Resume, RenderCV

---

## 🎨 CUSTOM FONTS INTEGRATED

### Font Families Available

Located in: `/Volumes/OMNI_01/10_SOURCE/50_Ops/FONTS/`

#### 1. **Barlow** (5 weights)
- Regular (400)
- Medium (500)
- SemiBold (600)
- Bold (700)
- ExtraBold (800)
- Black (900)

**Usage:** Primary UI font, buttons, headings

#### 2. **Inclusive Sans** (9 variants)
- Regular, Light, Medium, SemiBold, Bold
- Italic variants for each
- Variable weight versions

**Usage:** Body text, descriptions, readable content

#### 3. **Korolev** (5 weights)
- Thin (100)
- Light (300)
- Medium (500)
- Bold (700)
- Heavy (900)

**Usage:** Display headings, hero text, branding

#### 4. **Anthropic Sans** (Variable)
- Romans Variable (100-900)
- Italics Variable (100-900)

**Usage:** Professional content, documentation

#### 5. **Anthropic Serif** (Variable)
- Romans Variable (100-900)
- Italics Variable (100-900)

**Usage:** Long-form text, resumes, cover letters

---

## 🛠️ TOOLS INTEGRATION

### 1. Reactive Resume

**Location:** `/Volumes/OMNI_01/70_CLONED_REPOS/reactive-resume`

**What It Is:**
- Open-source resume builder
- 20+ professional templates
- Real-time preview
- Self-hosted (privacy-focused)
- Export to PDF, JSON, PNG

**Integration:**
- New page in Streamlit app: "Resume Tools"
- One-click Docker deployment
- Import AI-tailored content
- Apply professional templates

**How to Use:**
```bash
cd /Volumes/OMNI_01/70_CLONED_REPOS/reactive-resume
docker compose -f compose.dev.yml up -d
```

**Access:** http://localhost:3000

**Best For:**
- Industry resumes
- Visual customization
- Template variety
- Print-ready PDFs

---

### 2. RenderCV

**Location:** `/Volumes/OMNI_01/70_CLONED_REPOS/rendercv`

**What It Is:**
- LaTeX-based resume generator
- YAML/JSON input (version control friendly)
- Academic & industry templates
- Publication/bibliography support
- Command-line interface

**Integration:**
- "Resume Tools" page in Streamlit
- Install via pip
- Convert AI-tailored content to YAML
- Generate LaTeX-quality PDFs

**How to Install:**
```bash
cd /Volumes/OMNI_01/70_CLONED_REPOS/rendercv
pip install -e .
```

**Best For:**
- Academic CVs
- Technical roles
- Publication lists
- Version control workflows

---

## 🔄 INTEGRATED WORKFLOW

### Step 1: AI Tailoring (Local Resume Builder)
```
Input: Job Description + Your CV
Process: RAG retrieval + LLM generation
Output: Tailored resume content (.md)
```

### Step 2: Professional Formatting (Choose One)

#### Option A: Reactive Resume
```
Input: Tailored content (.md)
Process: Import → Choose template → Customize
Output: Professional PDF/PNG
```

#### Option B: RenderCV
```
Input: Tailored content (.md)
Process: Convert to YAML → Render LaTeX
Output: Academic-quality PDF
```

---

## 📊 COMPARISON TABLE

| Feature | AI Tailoring | Reactive Resume | RenderCV |
|---------|-------------|-----------------|----------|
| **Content Generation** | ✅ AI-powered | ❌ Manual | ❌ Manual |
| **Template Variety** | ❌ Basic | ✅ 20+ templates | ✅ 10+ templates |
| **Visual Customization** | ❌ Limited | ✅ Full control | ⚠️ LaTeX only |
| **Academic Support** | ❌ No | ⚠️ Basic | ✅ Full (bibliography) |
| **Version Control** | ❌ Markdown | ⚠️ JSON export | ✅ YAML/JSON |
| **Output Format** | Markdown | PDF, PNG, JSON | PDF (LaTeX) |
| **Best Use Case** | Content tailoring | Industry resumes | Academic CVs |

---

## 🎯 RECOMMENDED USAGE

### For Industry Jobs:
1. **AI Tailoring** → Generate tailored content
2. **Reactive Resume** → Apply professional template
3. **Export PDF** → Submit to employer

### For Academic Positions:
1. **AI Tailoring** → Generate research highlights
2. **RenderCV** → Convert to academic YAML
3. **Add Publications** → Include bibliography
4. **Render LaTeX** → Generate PDF

### For Tech Roles:
1. **AI Tailoring** → Match job requirements
2. **RenderCV** → Use technical template
3. **Version Control** → Track changes in Git
4. **Export PDF** → Submit application

---

## 📁 FILE STRUCTURE

```
/Volumes/OMNI_01/10_SOURCE/10_Front_Gate/public/apps/local-resume-builder/
├── main_ui.py                          # Main app with custom fonts
├── notebooklm_integration.py           # NotebookLM auto-upload
├── assets/
│   └── custom_fonts.css                # Font definitions
├── pages/
│   ├── 01_📄_Resume_Builder.py        # Main page (main_ui.py)
│   └── 02_🛠️_Resume_Tools.py          # NEW: Tools integration page
└── my_documents/
    └── cv_applications/                # Generated resumes
```

```
/Volumes/OMNI_01/10_SOURCE/50_Ops/FONTS/
├── Barlow-*.ttf                        # 6 files
├── InclusiveSans-*.ttf                 # 9 files
├── Korolev-*.otf                       # 5 files
├── AnthropicSans-*.ttf                 # 2 files
└── AnthropicSerif-*.ttf                # 2 files
```

```
/Volumes/OMNI_01/70_CLONED_REPOS/
├── reactive-resume/                    # Docker-based
│   ├── compose.dev.yml
│   ├── Dockerfile
│   └── ...
└── rendercv/                           # Python package
    ├── pyproject.toml
    ├── examples/
    └── docs/
```

---

## 🎨 FONT PREVIEW

### Barlow (Primary UI)
```
ABCDEFGHIJKLMNOPQRSTUVWXYZ
abcdefghijklmnopqrstuvwxyz
0123456789
```
**Use:** Headings, buttons, navigation

### Inclusive Sans (Body Text)
```
ABCDEFGHIJKLMNOPQRSTUVWXYZ
abcdefghijklmnopqrstuvwxyz
0123456789
```
**Use:** Descriptions, paragraphs, readable content

### Korolev (Display)
```
ABCDEFGHIJKLMNOPQRSTUVWXYZ
```
**Use:** Hero text, branding, large headings

### Anthropic Sans (Professional)
```
ABCDEFGHIJKLMNOPQRSTUVWXYZ
abcdefghijklmnopqrstuvwxyz
```
**Use:** Resumes, cover letters, documentation

---

## ⚙️ CONFIGURATION

### Streamlit Theme (`.streamlit/config.toml`)

```toml
[theme]
primaryColor = "#3b82f6"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f3f4f6"
textColor = "#1f2937"
font = "sans serif"

[server]
headless = true
port = 8501
address = "0.0.0.0"
enableCORS = false
enableXsrfProtection = true
```

### Custom Font CSS

Already integrated in `main_ui.py`:
```css
@font-face {
    font-family: 'Barlow';
    src: url('file:///Volumes/OMNI_01/10_SOURCE/50_Ops/FONTS/Barlow-Regular.ttf');
}

.main-header {
    font-family: 'Korolev', 'Barlow', sans-serif;
    font-weight: 900;
}
```

---

## 🚀 DEPLOYMENT

### 1. Restart Streamlit App

```bash
supervisorctl -s unix:///tmp/pastyche_supervisor.sock restart resume-builder
```

### 2. Start Reactive Resume (Optional)

```bash
cd /Volumes/OMNI_01/70_CLONED_REPOS/reactive-resume
docker compose -f compose.dev.yml up -d
```

### 3. Install RenderCV (Optional)

```bash
cd /Volumes/OMNI_01/70_CLONED_REPOS/rendercv
pip install -e .
```

### 4. Verify

Visit: https://docs.bitandmortar.com

- Main page: AI Resume Builder (with custom fonts)
- Sidebar → "Resume Tools": Reactive Resume + RenderCV integration

---

## 📊 BENEFITS

### Custom Fonts:
- ✅ Professional branding
- ✅ Consistent visual identity
- ✅ Better readability
- ✅ Unique appearance

### Tool Integration:
- ✅ Best-of-breed tools in one place
- ✅ Seamless workflow between tools
- ✅ No vendor lock-in
- ✅ Privacy-focused (all local)

---

## 🎯 NEXT STEPS

### Immediate:
1. ✅ Fonts integrated into Streamlit UI
2. ✅ Resume Tools page created
3. ✅ Documentation complete

### Optional Enhancements:
4. Add font picker in UI
5. Export with custom font selection
6. PDF generation with custom fonts
7. Template marketplace integration

---

**Status:** ✅ **COMPLETE**  
**Fonts:** 5 families, 24 variants  
**Tools:** 2 integrated (Reactive Resume, RenderCV)  
**Access:** https://docs.bitandmortar.com → Sidebar → "Resume Tools"

---

**🎉 Your Local Resume Builder now has custom OMNI fonts and professional tool integrations!**
