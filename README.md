# Global Exam Automation Script

<p align="center">
  <img src="./screenshot.png" alt="Global Exam Automation" width="600"/>
</p>

This script automates login and TOEIC exam training exercises on **Global Exam**.

## Features

- 🔐 **Automated Login** - Logs in with your credentials from `.env`
- 🍪 **Cookie Handling** - Automatically accepts cookie banners
- 🏫 **Organization Selection** - Selects the IPSSI organization if prompted
- 📝 **Exam Training** - Automatically solves "Entraînement 201" questions using a built-in Q&A mapping
- 🔄 **Continuous Loop** - Repeats the activity indefinitely

## Anti-Detection Measures

The script includes several stealth techniques to avoid bot detection:
- Human-like mouse movements using Bezier curves with occasional overshoot
- Randomized typing delays
- Realistic viewport and user agent configuration
- WebGL and navigator spoofing
- Persistent browser session

## Requirements

1. **Python 3.9+** installed
2. Install dependencies from `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   playwright install
   ```
3. Create a `.env` file with your credentials:
   ```env
   EMAIL=your_email
   PASSWORD=your_password
   ```

## Running the Script

Execute:
```bash
python script_resolve_exam.py
```

## Workflow

The script will:

1. **Login** - Navigate to Global Exam and log in with your credentials
2. **Accept Cookies** - Handle any cookie consent banners
3. **Select IPSSI** - Select the IPSSI organization if the selection page appears
4. **Navigate to Activity** - Go to the exam training exercises library
5. **Start Activity** - Click "Entraînement 201" and start the activity
6. **Solve Questions** - Answer each question using the built-in Q&A mapping
7. **Complete Pages** - Click "Valider" to move between pages, or "Terminer" to finish
8. **Loop** - Return to home and repeat the activity continuously

## Q&A Mapping

The script uses a predefined mapping (`EXAM_QA_MAP`) to match question snippets to correct answers. Questions are matched by checking if a key phrase appears in the question text.

## Notes

- The browser session is persisted in `./browser_session/` to maintain login state
- The script uses French locale (`fr-FR`) and Paris timezone
- Press `Ctrl+C` to stop the script manually
