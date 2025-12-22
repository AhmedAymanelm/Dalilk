#!/bin/bash

# سكريبت لتشغيل السيرفر

cd "$(dirname "$0")"
source ../venv/bin/activate

echo "🚀 بدء تشغيل السيرفر..."
echo "📍 العنوان: http://localhost:8000"
echo "📚 Swagger UI: http://localhost:8000/docs"
echo ""
echo "للإيقاف: اضغط Ctrl+C"
echo ""

python -c "import uvicorn; from main import app; uvicorn.run(app, host='0.0.0.0', port=8000, reload=True)"

