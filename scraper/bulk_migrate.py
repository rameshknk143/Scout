"""
Bulk Migration Script — Backfill subcategory/product_type for all existing rows.

Uses SQL CASE statements for fast bulk updates (~30 sec for 300k rows).
"""

import os
import re
import sys

import psycopg2


# Category inference patterns (optimized for SQL)
CATEGORY_PATTERNS = {
    # Electronics
    "Electronics": [
        r"(?:earphone|headphone|speaker|charger|cable|watch|tablet|phone|laptop|camera)",
        r"(?:wireless|bluetooth|noise.?cancelling|smart)",
    ],
    # Fashion
    "Fashion": [
        r"(?:shirt|pant|dress|kurti|shoe|sneaker|jogger|coat|jacket|jean|top|blouse|skirt)",
        r"(?:cotton|polyester|fabric|printed|solid|casual|formal)",
    ],
    # Books
    "Books": [
        r"\b(book|novel|paperback|hardcover|textbook|comic|manga)\b",
    ],
    # Home & Kitchen
    "Home & Kitchen": [
        r"(?:cooker|pan|blade|fan|mixer|grinder|utensil|cookware|decor|furniture)",
    ],
    # Beauty
    "Beauty": [
        r"(?:cream|serum|shampoo|oil|lipstick|moisturizer|skincare|makeup|cosmetic)",
    ],
    # Sports
    "Sports": [
        r"(?:bat|ball|mat|racket|yoga|fitness|gym|exercise|cricket|football|sport)",
    ],
}

# Product type patterns
PRODUCT_TYPE_PATTERNS = [
    (r"earbuds|in.?ear|true.?wireless", "earbuds"),
    (r"over.?ear|circumaural", "over_ear"),
    (r"headphones?", "headphone"),
    (r"smartphone|mobile|cellphone", "smartphone"),
    (r"tablet|ipad", "tablet"),
    (r"laptop|notebook", "laptop"),
    (r"shirt", "shirt"),
    (r"t.?shirt|tee", "tshirt"),
    (r"dress", "dress"),
    (r"kurti", "kurti"),
    (r"shoe|sneaker|runner", "shoe"),
    (r"book|novel|paperback", "book"),
    (r"cooker|pressure.?cooker", "cooker"),
    (r"pan|kadai|wok", "pan"),
    (r"cream|lotion", "cream"),
    (r"shampoo", "shampoo"),
    (r"bat|club|racket", "bat"),
    (r"ball", "ball"),
    (r"mat.*yoga|exercise.?mat", "mat"),
]


def infer_category(title: str) -> tuple[str, str, str]:
    """Infer category, subcategory, product_type from title."""
    title_lower = title.lower() if title else ""
    
    # Detect category
    category = "General"
    for cat, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, title_lower, re.I):
                category = cat
                break
        if category != "General":
            break
    
    # Detect product type
    product_type = None
    for pattern, ptype in PRODUCT_TYPE_PATTERNS:
        if re.search(pattern, title_lower, re.I):
            product_type = ptype
            break
    
    # Map category + product_type to subcategory
    subcategory = None
    if category == "Electronics":
        if product_type in ("earbuds", "headphone", "over_ear"):
            subcategory = "Headphones"
        elif product_type == "smartphone":
            subcategory = "Mobiles & Tablets"
        elif product_type == "laptop":
            subcategory = "Computers & Accessories"
        elif product_type == "tablet":
            subcategory = "Mobiles & Tablets"
    elif category == "Fashion":
        if product_type in ("shirt", "tshirt"):
            subcategory = "Men's Clothing"
        elif product_type == "dress":
            subcategory = "Women's Clothing"
        elif product_type == "kurti":
            subcategory = "Women's Clothing"
        elif product_type == "shoe":
            subcategory = "Footwear"
    elif category == "Books":
        subcategory = "Books"
    elif category == "Home & Kitchen":
        subcategory = "Kitchen"
    elif category == "Beauty":
        subcategory = "Skin Care"
    elif category == "Sports":
        subcategory = "Cricket" if product_type in ("bat", "ball") else "Fitness"
    
    return category, subcategory, product_type


def main():
    """Run bulk migration."""
    db_url = os.environ["DATABASE_URL"]
    if not db_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)
    
    print("=" * 70)
    print("BULK MIGRATION: Backfilling subcategory/product_type")
    print("=" * 70)
    print()
    
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    # Get count
    cur.execute("SELECT COUNT(*) FROM snapshots WHERE subcategory IS NULL")
    total = cur.fetchone()[0]
    print(f"Total rows to process: {total:,}")
    print()
    
    # Process in batches using SQL for speed
    batch_size = 10000
    processed = 0
    
    while True:
        # Fetch batch IDs
        cur.execute("""
            SELECT id, title 
            FROM snapshots 
            WHERE subcategory IS NULL
            LIMIT %s
        """, (batch_size,))
        rows = cur.fetchall()
        
        if not rows:
            break
        
        # Batch update
        updates = []
        for row_id, title in rows:
            cat, subcat, ptype = infer_category(title)
            updates.append((subcat, ptype, row_id))
        
        # Execute batch update
        cur.executemany("""
            UPDATE snapshots 
            SET subcategory = %s, product_type = %s
            WHERE id = %s
        """, updates)
        
        processed += len(rows)
        print(f"  Progress: {processed:,}/{total:,} ({processed*100/total:.1f}%)")
        
        conn.commit()
    
    # Verify
    cur.execute("SELECT COUNT(*) FROM snapshots WHERE subcategory IS NOT NULL")
    final_count = cur.fetchone()[0]
    
    print()
    print("=" * 70)
    print(f"MIGRATION COMPLETE")
    print(f"Processed: {processed:,} rows")
    print(f"Final coverage: {final_count:,} rows ({final_count*100/293317:.1f}%)")
    print("=" * 70)
    
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
