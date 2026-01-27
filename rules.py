JE_RULES = [
#SOD Conflict
  {
       "rule_id": "SOD_Conflict_001",
       "rule_description": "Journal Entries where preparer and reviewer is the same",
       "sql": """ 
       SELECT *
       FROM JE_Table
       WHERE Preparer_ID IS NOT NULL
       AND Approver_ID IS NOT NULL
       AND Preparer_ID = Approver_ID;
    """
 },

#Double Posting Error
  {
      "rule_id": "Duplicate_Entries_002",
      "rule_description":"Same Journal Entries posted twice",
      "sql": """
       WITH JE_Rewrite AS(
       SELECT 
           JE_ID,
           GROUP_CONCAT(
              CASE
                 WHEN ROUND(Debit,2) <> 0 
                 THEN GL_Account || ':' || printf('%.2f', ROUND(Debit,2))
               END,
               '|'
        ) AS GL_DR_WITH_AMT,
        GROUP_CONCAT(
           CASE 
               WHEN ROUND(Credit, 2) <> 0
               THEN GL_Account || ':' || printf('%.2f', ROUND(Credit, 2))
           END, 
           '|'
        ) AS GL_CR_WITH_AMT
    FROM (
          SELECT JE_ID, GL_Account, Debit, Credit
          FROM JE_Table 
          ORDER BY JE_ID, GL_Account
       )
       GROUP BY JE_ID
    ),
    Duplicate_JEs AS (
        SELECT a.JE_ID AS JE_ID
        FROM JE_Rewrite a
        JOIN JE_Rewrite b
         ON a.JE_ID < b.JE_ID
        AND a.GL_DR_WITH_AMT = b.GL_DR_WITH_AMT
        AND a.GL_CR_WITH_AMT = b.GL_CR_WITH_AMT

    UNION
    
       SELECT b.JE_ID AS JE_ID
       FROM JE_Rewrite a
       JOIN JE_Rewrite b
        ON a.JE_ID < b.JE_ID
       AND a.GL_DR_WITH_AMT = b.GL_DR_WITH_AMT
      AND a.GL_CR_WITH_AMT = b.GL_CR_WITH_AMT
)
SELECT jt.*
FROM JE_Table jt
JOIN Duplicate_JEs d
ON jt.JE_ID = d.JE_ID
ORDER BY jt.JE_ID;
"""
},

#Entries Posted on Weekends
{
    "rule_id":"Postings_on_Weekend_003",
    "rule_description": "Jornal Entries posted on weekends",
    "sql": """
    WITH date_range AS (
    SELECT 
    MIN(Posting_Date) AS earliest_date,
    MAX(Posting_Date) AS latest_date
    FROM JE_Table 
),
dates(d) AS (
    SELECT earliest_date
    FROM date_range 
    UNION ALL
    SELECT date(d, '+1 day')
    FROM date_range, dates
    WHERE d <= date_range.latest_date
)
SELECT * FROM JE_Table WHERE Posting_Date IN (
    SELECT d FROM dates
    WHERE strftime('%w', d) IN ('0', '6'))
    ORDER BY Posting_Date;
"""
}

,

{
    "rule_id": "Large_JE_Amount_001",
    "rule_description": "Identifies journal entries with either a debit or credit amount exceeding 10,000.",
    "sql": "SELECT * FROM JE_Table WHERE Debit > 10000 OR Credit > 10000"
}
]
