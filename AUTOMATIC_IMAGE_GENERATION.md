# Automatic Image Generation & Selection

This enhanced AI Manga Storyboard Generator now includes powerful automatic features that can process all your panels with minimal manual intervention.

## 🚀 New Features

### 1. **Auto-Process All Panels** 
- **Location**: Image Generator app sidebar
- **What it does**: 
  - Generates multiple variants for each panel in your project
  - Automatically evaluates each variant against the panel description
  - Selects the best matching image based on AI evaluation
  - Processes all panels in sequence

### 2. **Auto-Select Best Variant** (Individual Panel)
- **Location**: Image Generator app, in the variants section
- **What it does**:
  - Evaluates existing variants for the current panel
  - Scores each image from 0-10 based on prompt matching
  - Automatically selects the highest scoring variant

### 3. **AI Image Evaluation**
- Uses advanced multimodal AI to analyze images
- Evaluates based on:
  - Visual accuracy to description
  - Composition and framing
  - Character positioning and appearance
  - Background accuracy
  - Mood and atmosphere
  - Technical quality

## 📖 How to Use

### Quick Start - Process Everything Automatically:

1. **Set up your project** in the Project Setup app
2. **Load the project** in the Image Generator app
3. **Configure automatic settings** in the sidebar:
   - **Variants per panel**: 2-5 (3 recommended)
   - **Image creativity**: 0.0-1.0 (0.7 recommended)
4. **Click "🎯 Auto-Process All Panels"**
5. **Wait for completion** - this may take several minutes depending on the number of panels
6. **Review results** - see processing summary with scores

### Manual Panel Processing with Auto-Selection:

1. **Navigate to a panel** using the panel navigation
2. **Generate variants** manually with custom prompts
3. **Click "🎯 Auto-Select Best Variant"** to automatically choose the best one
4. **Review the AI's reasoning** for the selection

## 🎯 Evaluation Criteria

The AI evaluates images based on:

- **Accuracy (25%)**: How well visual elements match the description
- **Composition (20%)**: Proper framing and camera angles
- **Characters (20%)**: Accurate character appearance and positioning  
- **Background (15%)**: Setting and environment accuracy
- **Mood (10%)**: Atmosphere and emotional tone
- **Quality (10%)**: Technical clarity and artistic quality

## 💡 Tips for Best Results

1. **Clear Descriptions**: Write detailed, specific panel descriptions
2. **Character References**: Define characters with reference images in Project Setup
3. **Background Context**: Add background references for consistent environments
4. **Optimal Settings**: 
   - Use 3-4 variants per panel for good selection variety
   - Set creativity to 0.7 for balanced results
   - Higher creativity (0.8-1.0) for more artistic variation
   - Lower creativity (0.4-0.6) for more literal interpretations

## 🔧 Troubleshooting

**No variants generated?**
- Check your Google Cloud setup and API permissions
- Ensure Vertex AI is enabled in your project
- Verify your panel descriptions aren't too vague

**Low evaluation scores?**
- Make panel descriptions more specific and visual
- Add character and background references
- Try regenerating with different creativity settings

**Processing fails?**
- Check your internet connection
- Verify Google Cloud quota and billing
- Ensure all required APIs are enabled

## 🎨 Example Workflow

1. Create project with characters and backgrounds
2. Import or create panel descriptions
3. Run "Auto-Process All Panels" 
4. Review automatically selected images
5. Manually adjust any panels if needed
6. Export final comic in Comic Preview app

The automatic features save significant time while maintaining high quality results through AI-powered evaluation and selection! 