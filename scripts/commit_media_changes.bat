@echo off
REM Commit media panel and .gitattributes (Windows CMD)
git add backoffice\ui\media_upload_panel.py streamlit_app.py .gitattributes
git commit -m "feat(media): add media upload panel and menu entry"
git push origin main
