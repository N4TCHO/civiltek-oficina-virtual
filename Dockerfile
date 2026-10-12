FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python -m compileall -q backend && python -c "from backend.main import app; assert app.title == 'Civiltek API'"
RUN mkdir -p /app/data
ENV CIVILTEK_DB_PATH=/app/data/civiltek.db
EXPOSE 8000
CMD ["uvicorn","backend.main:app","--host","0.0.0.0","--port","8000"]
