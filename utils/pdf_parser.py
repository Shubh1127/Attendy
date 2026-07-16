import pdfplumber
import pandas as pd


def read_student_pdf(file) -> pd.DataFrame:

    rows = []

    with pdfplumber.open(file) as pdf:

        for page in pdf.pages:

            tables = page.extract_tables()

            for table in tables:

                if not table:
                    continue

                headers = table[0]

                for row in table[1:]:

                    if row:

                        rows.append(row)

    df = pd.DataFrame(
        rows,
        columns=headers
    )

    return df

def extract_students(df):

    students = []

    required = [
        "Enrollment Number",
        "Name"
    ]

    for col in required:

        if col not in df.columns:

            raise ValueError(
                f"Missing column: {col}"
            )

    for _, row in df.iterrows():

        students.append({

            "enrollment_number":
                str(row["Enrollment Number"]).strip(),

            "name":
                str(row["Name"]).strip()

        })

    return students