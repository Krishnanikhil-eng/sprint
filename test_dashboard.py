import os
import glob
from streamlit.testing.v1 import AppTest

def test_pages():
    pages = glob.glob("src/dashboard/pages/*.py")
    pages.append("src/dashboard/app.py")
    for page in sorted(pages):
        print(f"Testing {page}...")
        try:
            at = AppTest.from_file(page)
            at.run()
            
            if at.exception:
                print(f"[FAIL] Error in {page}:")
                for e in at.exception:
                    print(e)
            else:
                print(f"[PASS] {page} loaded successfully.")
        except Exception as e:
            print(f"[FAIL] Failed to run {page}: {e}")

if __name__ == "__main__":
    test_pages()
