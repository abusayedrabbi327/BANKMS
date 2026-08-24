"""
BankMS Neo - Application Server Entry Point
"""
import uvicorn
import os

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    
    print("\n" + "="*60)
    print("  [+] BankMS Neo v2.0 - Next-Gen Banking Management System")
    print(f"  [*] Web Dashboard: http://{host}:{port}/")
    print(f"  [*] Swagger API Docs: http://{host}:{port}/docs")
    print(f"  [*] ReDoc: http://{host}:{port}/redoc")
    print("="*60 + "\n")
    
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
