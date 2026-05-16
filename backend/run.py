#!/usr/bin/env python3
"""Запуск API из корня backend: python3 run.py"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
