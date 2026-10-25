import os
import pandas as pd
from typing import Optional, Dict, Any

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data"))

class MockRegistryService:
    def __init__(self):
        self._registry_df: Optional[pd.DataFrame] = None
        self._counselling_df: Optional[pd.DataFrame] = None
        self._exams_df: Optional[pd.DataFrame] = None
        self._fees_df: Optional[pd.DataFrame] = None

    def _ensure_loaded(self):
        reg_file = os.path.join(DATA_DIR, "registry.csv")
        counselling_file = os.path.join(DATA_DIR, "counselling.csv")
        exams_file = os.path.join(DATA_DIR, "exams.csv")
        fees_file = os.path.join(DATA_DIR, "fees.csv")

        if self._registry_df is None and os.path.exists(reg_file):
            try:
                self._registry_df = pd.read_csv(reg_file, dtype=str)
            except Exception:
                self._registry_df = pd.DataFrame()

        if self._counselling_df is None and os.path.exists(counselling_file):
            try:
                self._counselling_df = pd.read_csv(counselling_file, dtype=str)
            except Exception:
                self._counselling_df = pd.DataFrame()

        if self._exams_df is None and os.path.exists(exams_file):
            try:
                self._exams_df = pd.read_csv(exams_file, dtype=str)
            except Exception:
                self._exams_df = pd.DataFrame()

        if self._fees_df is None and os.path.exists(fees_file):
            try:
                self._fees_df = pd.read_csv(fees_file, dtype=str)
            except Exception:
                self._fees_df = pd.DataFrame()

    def lookup_apaar_registry(self, apaar_id: str) -> Optional[Dict[str, Any]]:
        self._ensure_loaded()
        if self._registry_df is None or self._registry_df.empty or not apaar_id:
            return None
        match = self._registry_df[self._registry_df["apaar_id"] == str(apaar_id).strip()]
        if not match.empty:
            return match.iloc[0].to_dict()
        return None

    def lookup_counselling_record(self, apaar_id: str) -> Optional[Dict[str, Any]]:
        self._ensure_loaded()
        if self._counselling_df is None or self._counselling_df.empty or not apaar_id:
            return None
        match = self._counselling_df[self._counselling_df["apaar_id"] == str(apaar_id).strip()]
        if not match.empty:
            return match.iloc[0].to_dict()
        return None

    def lookup_exam_record(self, apaar_id: str) -> Optional[Dict[str, Any]]:
        self._ensure_loaded()
        if self._exams_df is None or self._exams_df.empty or not apaar_id:
            return None
        match = self._exams_df[self._exams_df["apaar_id"] == str(apaar_id).strip()]
        if not match.empty:
            return match.iloc[0].to_dict()
        return None

    def lookup_fee_record(self, apaar_id: str) -> Optional[Dict[str, Any]]:
        self._ensure_loaded()
        if self._fees_df is None or self._fees_df.empty or not apaar_id:
            return None
        match = self._fees_df[self._fees_df["apaar_id"] == str(apaar_id).strip()]
        if not match.empty:
            return match.iloc[0].to_dict()
        return None


registry_service = MockRegistryService()
