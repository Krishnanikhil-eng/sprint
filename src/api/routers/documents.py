"""
Documents API Router Module (Day 40).
Implements REST endpoint for retrieving annual reports and filing document metadata per company.
"""

import sqlite3
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException

from src.api.database import get_db

router = APIRouter(tags=["Documents"])


@router.get("/companies/{ticker}/documents")
def get_company_documents(
    ticker: str,
    db: sqlite3.Connection = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns filing documents, annual report URLs, and link validation status for a given company ticker.
    """
    ticker_upper = ticker.strip().upper()
    cursor = db.cursor()

    # Verify company exists
    cursor.execute("SELECT company_id, company_name FROM companies WHERE UPPER(company_id) = ?", (ticker_upper,))
    company = cursor.fetchone()
    if not company:
        raise HTTPException(
            status_code=404,
            detail=f"Company ticker '{ticker}' not found"
        )

    # Fetch documents
    query = """
    SELECT 
        id,
        year,
        annual_report as document_url
    FROM documents
    WHERE UPPER(company_id) = ?
    ORDER BY year DESC;
    """
    cursor.execute(query, (ticker_upper,))
    rows = cursor.fetchall()

    documents: List[Dict[str, Any]] = []
    for r in rows:
        url = r["document_url"]
        is_valid = bool(url and isinstance(url, str) and (url.startswith("http://") or url.startswith("https://")))
        documents.append({
            "id": r["id"],
            "year": r["year"],
            "document_type": "Annual Report",
            "document_url": url,
            "is_valid_url": is_valid
        })

    return {
        "ticker": company["company_id"],
        "company_name": company["company_name"],
        "document_count": len(documents),
        "documents": documents
    }
