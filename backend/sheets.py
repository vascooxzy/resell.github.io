"""
Google Sheets integration using the gspread library.

Prerequisites:
  1. Enable Google Sheets API in Google Cloud Console.
  2. Create a Service Account and download credentials JSON.
  3. Share the target spreadsheet with the service account email.
  4. Set GOOGLE_CREDENTIALS_FILE and GOOGLE_SHEET_ID in .env.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

COLUMN_HEADERS = ["Nome", "Preço", "Avaliação", "Vendedor", "Link", "Imagem", "Encomendas"]


def _get_client():
    """Lazy-import gspread and return an authorised client."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError as exc:
        raise ImportError(
            "Install Google Sheets dependencies: pip install gspread google-auth"
        ) from exc

    creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    if not os.path.exists(creds_file):
        raise FileNotFoundError(
            f"Google credentials file not found: '{creds_file}'. "
            "Set GOOGLE_CREDENTIALS_FILE in .env."
        )

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
    return gspread.authorize(creds)


def export_to_sheets(
    products: list[dict],
    sheet_id: Optional[str] = None,
    worksheet_name: str = "DHgate Produtos",
) -> str:
    """
    Export a list of products to a Google Sheets worksheet.

    Args:
        products: List of product dicts from the scraper.
        sheet_id: Google Spreadsheet ID. Falls back to GOOGLE_SHEET_ID env var.
        worksheet_name: Name of the worksheet tab to write to.

    Returns:
        URL of the spreadsheet.
    """
    sheet_id = sheet_id or os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id:
        raise ValueError(
            "Spreadsheet ID is required. "
            "Pass sheet_id or set GOOGLE_SHEET_ID in .env."
        )

    client = _get_client()
    spreadsheet = client.open_by_key(sheet_id)

    # Get or create worksheet
    try:
        ws = spreadsheet.worksheet(worksheet_name)
        ws.clear()
        logger.info(f"Cleared existing worksheet '{worksheet_name}'")
    except Exception:
        ws = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=10)
        logger.info(f"Created new worksheet '{worksheet_name}'")

    rows = [COLUMN_HEADERS]
    for p in products:
        rows.append([
            p.get("name", ""),
            p.get("price", ""),
            p.get("rating", ""),
            p.get("seller", ""),
            p.get("link", ""),
            p.get("image", ""),
            p.get("orders", ""),
        ])

    ws.update(rows, value_input_option="USER_ENTERED")

    # Bold the header row
    ws.format("A1:G1", {"textFormat": {"bold": True}})

    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
    logger.info(f"Exported {len(products)} products to Google Sheets: {url}")
    return url
