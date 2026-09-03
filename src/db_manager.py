import os
import sqlite3
import pandas as pd
from typing import Dict, Any, List

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "infrastructure_audit.db")

class DatabaseManager:
    """
    SQLite Database Manager for Data Quality & Infrastructure Analytics.
    Handles table creation, dataframe ingestion, and executing analytical SQL queries.
    """
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Returns an active SQLite database connection."""
        return sqlite3.connect(self.db_path)

    def ingest_audit_data(self, clean_df: pd.DataFrame, quarantine_df: pd.DataFrame, 
                           issues_df: pd.DataFrame, audit_log_df: pd.DataFrame):
        """
        Populates SQLite database with clean records, quarantined records, validation issues, and audit logs.
        """
        conn = self.get_connection()
        try:
            clean_df.to_sql("clean_bridges", conn, if_exists="replace", index=False)
            
            if not quarantine_df.empty:
                quarantine_df.to_sql("quarantined_bridges", conn, if_exists="replace", index=False)
            else:
                pd.DataFrame(columns=clean_df.columns).to_sql("quarantined_bridges", conn, if_exists="replace", index=False)

            if not issues_df.empty:
                issues_df.to_sql("validation_issues", conn, if_exists="replace", index=False)
            else:
                pd.DataFrame(columns=["row_index", "bridge_id", "column", "issue_code", "severity", "description", "invalid_value"]).to_sql("validation_issues", conn, if_exists="replace", index=False)

            if not audit_log_df.empty:
                audit_log_df.to_sql("audit_log", conn, if_exists="replace", index=False)
            else:
                pd.DataFrame(columns=["row_index", "bridge_id", "column", "action_taken", "new_value", "notes"]).to_sql("audit_log", conn, if_exists="replace", index=False)

            conn.commit()
        finally:
            conn.close()

    def run_query(self, query: str) -> pd.DataFrame:
        """
        Executes a SQL query and returns result as a Pandas DataFrame.
        """
        conn = self.get_connection()
        try:
            return pd.read_sql_query(query, conn)
        finally:
            conn.close()
