# 📊 PowerPoint Presentation Setup Guide

**Complete guide to creating your Socializer presentation with videos and ER diagrams**

---

## ✅ WHAT'S ALREADY DONE

✅ **PowerPoint Created:** `Socializer_Presentation.pptx`  
- 12 professional slides
- Modern design
- Compatible with PowerPoint for Mac
- Ready for videos and images

---

## 📋 STEP-BY-STEP INSTRUCTIONS

### **STEP 1: Install Graphviz (for ER Diagrams)** ⏱️ 2 minutes

Graphviz is needed to create database relationship diagrams with arrows.

```bash
# Install Graphviz using Homebrew
brew install graphviz

# Install Python package
.venv/bin/pip install graphviz
```

**Check installation:**
```bash
which dot
# Should output: /opt/homebrew/bin/dot (or similar)
```

---

### **STEP 2: Create ER Diagram** ⏱️ 1 minute

```bash
cd /Users/leeroystevenson/PycharmProjects/Socializer
.venv/bin/python create_er_diagram.py
```

**Output:** `socializer_er_diagram.png`  
- High-resolution PNG
- All tables with relationships
- Proper crow's foot notation arrows
- Color-coded by function

---

### **STEP 3: Record Backend Video (Swagger)** ⏱️ 3-5 minutes

#### **What to show:**
1. Open Swagger UI: http://localhost:8000/docs
2. Show list of endpoints
3. Demonstrate login:
   - Click POST /api/auth/login
   - Enter credentials: `human2` / `FuckShit123.`
   - Show token in response
4. Show authorization:
   - Click "Authorize" button
   - Paste token
5. Test a few endpoints:
   - GET /users/me/
   - GET /api/rooms/
   - POST /api/ai/chat (send a message)
6. Show 200 status codes

#### **How to record on Mac:**

**Option 1: QuickTime Player (Recommended)**
```
1. Press Cmd + Shift + 5
2. Select "Record Selected Portion"
3. Select browser window with Swagger
4. Click "Record"
5. Perform demo
6. Click Stop button in menu bar
7. Save as: swagger_demo.mp4
```

**Option 2: QuickTime Player App**
```
1. Open QuickTime Player
2. File > New Screen Recording
3. Select area
4. Record
5. Stop and save
```

**Tips:**
- Keep it 2-3 minutes max
- Speak clearly (optional)
- Show key features
- End with successful API calls

---

### **STEP 4: Record Frontend Video** ⏱️ 3-5 minutes

#### **What to show:**
1. Home page
2. Login page (login with human2)
3. Main chat interface
4. Create/join a room
5. Send messages in room
6. Show AI interaction
7. Show room list
8. Demonstrate logout

#### **How to record:**
Same as backend video (Cmd + Shift + 5)

**Save as:** `frontend_demo.mp4`

**Tips:**
- Show smooth navigation
- Demonstrate key features
- Keep it concise (2-3 minutes)
- Show responsiveness

---

### **STEP 5: Add Materials to PowerPoint** ⏱️ 10 minutes

#### **5.1: Add ER Diagram**

1. Open `Socializer_Presentation.pptx`
2. Go to slide: "🗄️ Database Schema Overview"
3. Click: Insert > Pictures > Picture from File
4. Select: `socializer_er_diagram.png`
5. Resize to fit slide (keep aspect ratio)
6. Position below the text
7. Optional: Add border (Format > Picture Border)

#### **5.2: Add Backend Video**

1. Go to slide: "🔧 Backend API Demo (Swagger UI)"
2. Click the placeholder box
3. Delete placeholder
4. Click: Insert > Video > Video from File
5. Select: `swagger_demo.mp4`
6. Resize video to fit the space
7. Set to play automatically:
   - Select video
   - Playback tab > Start: Automatically
8. Optional: Add play button overlay

#### **5.3: Add Frontend Video**

1. Go to slide: "🎨 Frontend Demo"
2. Follow same steps as backend video
3. Select: `frontend_demo.mp4`
4. Set playback options

---

## 🎨 OPTIONAL: Customize Presentation

### **Add Screenshots:**
You can add more screenshots to any slide:
- Take screenshots with Cmd + Shift + 4
- Insert > Pictures
- Resize and position

### **Modify Slides:**
- Edit text: Click and type
- Change colors: Format > Shape Fill
- Add shapes: Insert > Shapes
- Add transitions: Transitions tab

### **Add Your Logo:**
If you have a logo:
1. Insert > Pictures
2. Add to title slide
3. Resize to corner position

---

## 📊 PRESENTATION STRUCTURE

Your presentation includes:

1. **Title Slide** - Professional opener
2. **Agenda** - Overview of topics
3. **Project Overview** - What is Socializer
4. **System Architecture** - Technical layers
5. **Database Schema** - ER diagram placeholder
6. **Users Table Detail** - Core table structure
7. **Chat Rooms Table Detail** - Room management
8. **Key Features** - AI, Chat, Security
9. **Backend Video** - Swagger demo placeholder
10. **Frontend Video** - UI demo placeholder
11. **Security & Encryption** - Security features
12. **Performance & Quality** - Metrics
13. **Future Enhancements** - Roadmap
14. **Closing** - Thank you slide

---

## 🎥 VIDEO RECORDING CHECKLIST

### **Before Recording:**
- [ ] Start the Socializer server
- [ ] Close unnecessary apps/windows
- [ ] Turn off notifications (Do Not Disturb)
- [ ] Test microphone (if narrating)
- [ ] Prepare browser windows
- [ ] Clear browser cache/cookies

### **Backend Video Recording:**
- [ ] Open Swagger UI
- [ ] Have credentials ready
- [ ] Test one endpoint beforehand
- [ ] Keep mouse movements smooth
- [ ] Record 2-3 minutes max

### **Frontend Video Recording:**
- [ ] Open application in browser
- [ ] Have test account logged out
- [ ] Plan your clicks
- [ ] Show key features
- [ ] Record 2-3 minutes max

### **After Recording:**
- [ ] Review video quality
- [ ] Check audio (if applicable)
- [ ] Trim if needed (QuickTime: Edit > Trim)
- [ ] Save in presentation folder

---

## ⚡ QUICK COMMANDS REFERENCE

```bash
# 1. Install Graphviz
brew install graphviz
.venv/bin/pip install graphviz

# 2. Create ER Diagram
.venv/bin/python create_er_diagram.py

# 3. Start Server (for recording)
uvicorn app.main:app --reload

# 4. Open Swagger
open http://localhost:8000/docs

# 5. Open Frontend
open http://localhost:8000
```

---

## 🎯 EXPECTED TIMELINE

| Task | Time | Status |
|------|------|--------|
| Install Graphviz | 2 min | ⏳ |
| Create ER Diagram | 1 min | ⏳ |
| Record Backend Video | 5 min | ⏳ |
| Record Frontend Video | 5 min | ⏳ |
| Add Materials to PPT | 10 min | ⏳ |
| Review & Finalize | 5 min | ⏳ |
| **TOTAL** | **~30 min** | |

---

## 📝 NOTES

### **PowerPoint Compatibility:**
✅ Created with python-pptx (fully compatible with Mac)  
✅ Standard .pptx format  
✅ Opens in PowerPoint for Mac, Keynote, or LibreOffice  
✅ No special fonts required (uses Arial)  
✅ Videos embed properly in PowerPoint for Mac

### **File Locations:**
```
Socializer/
├── Socializer_Presentation.pptx    ← PowerPoint file
├── socializer_er_diagram.png       ← ER diagram (after step 2)
├── swagger_demo.mp4                ← Backend video (you record)
├── frontend_demo.mp4               ← Frontend video (you record)
├── create_presentation.py          ← Script (already run)
└── create_er_diagram.py            ← Script (run in step 2)
```

### **Video Format:**
- Format: .mp4 (H.264 codec)
- Resolution: 1920x1080 recommended
- Frame rate: 30fps
- Audio: Optional but recommended

---

## ❓ TROUBLESHOOTING

### **"Graphviz not found"**
```bash
# Install with Homebrew
brew install graphviz

# Verify
which dot
```

### **"Video won't play in PowerPoint"**
- Make sure video is .mp4 format
- Try re-inserting the video
- Update PowerPoint for Mac
- Use QuickTime to convert if needed

### **"Presentation looks different on another Mac"**
- Embed fonts: File > Options > Save > Embed Fonts
- Keep videos in same folder as presentation
- Share entire folder, not just .pptx file

### **"Screen recording shortcut doesn't work"**
- System Preferences > Keyboard > Shortcuts
- Enable Screen Recording shortcuts
- Or use QuickTime Player app instead

---

## ✅ FINAL CHECKLIST

Before presenting:

- [ ] ER diagram added to slide 5
- [ ] Backend video embedded and plays
- [ ] Frontend video embedded and plays
- [ ] All videos in same folder as presentation
- [ ] Reviewed all slides for typos
- [ ] Tested presentation in slideshow mode
- [ ] Checked transitions work
- [ ] Videos set to autoplay or manual
- [ ] Presentation saved and backed up

---

## 🎉 YOU'RE READY!

Once you complete these steps, you'll have:
- ✅ Professional PowerPoint presentation
- ✅ Database ER diagram with relationships
- ✅ Backend API demonstration video
- ✅ Frontend walkthrough video
- ✅ Fully functional presentation ready to share

---

## 📧 NEXT STEPS

1. **Follow steps 1-5 above**
2. **Review the presentation**
3. **Practice your delivery**
4. **Share or present!**

**Good luck with your presentation!** 🚀

