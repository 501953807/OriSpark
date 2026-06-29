"""Data migration: products → design_listings (P2).

Migrates existing flat Product records to the new DesignListing model,
preserving all data and establishing proper FK relationships.

Run: python -m app.migrations.migrate_products_to_listings
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import text
from app.database import SessionLocal
from app.models.publish import Product, RevenueRecord, ProductPublishing
from app.models.monetization import Campaign, License
from app.models.supply import Order
from app.models.listings import DesignListing, DesignTemplateCompatibility


def migrate_products_to_listings():
    """Migrate all existing products to design_listings."""
    db = SessionLocal()

    try:
        # 1. Count existing products
        product_count = db.query(Product).count()
        print(f"Found {product_count} existing products to migrate.")

        if product_count == 0:
            print("No products to migrate. Skipping.")
            return

        migrated = 0
        skipped = 0

        for product in db.query(Product).all():
            try:
                # Map material_category from product.category
                material_map = {
                    't_shirt': 'textile', 'hoodie': 'textile', 'tote_bag': 'textile',
                    'mug': 'hard_goods', 'phone_case': 'plastic_3c', 'sticker': 'paper',
                    'poster': 'paper', 'pin': 'toys', 'plush_toy': 'toys',
                }
                material = material_map.get(product.category, '')

                listing = DesignListing(
                    id=product.id,  # Preserve original ID for FK compatibility
                    work_id=product.work_id,
                    product_template_id='',  # Will be set after template resolution
                    title=product.title or '未命名商品',
                    description=product.description,
                    price=product.price or 0,
                    cost=product.cost or 0,
                    currency=product.currency or 'CNY',
                    monetization_path=product.monetization_path,
                    variant_sku='',
                    variant_name='',
                    spec_validation=product.specifications,
                    spec_validated_at=product.created_at,
                    mockup_image_path=product.mockup_image_path,
                    design_file_path=product.design_variant_path,
                    status=product.status or 'draft',
                    created_at=product.created_at,
                    updated_at=product.updated_at,
                )

                # Try to find matching template from specifications
                if product.specifications and isinstance(product.specifications, dict):
                    template_id = product.specifications.get('category_id', '')
                    if template_id:
                        listing.product_template_id = template_id

                db.add(listing)
                migrated += 1

            except Exception as e:
                print(f"  SKIP product {product.id}: {e}")
                skipped += 1

        db.commit()
        print(f"\nMigration complete:")
        print(f"  Migrated: {migrated}")
        print(f"  Skipped: {skipped}")
        print(f"  Total: {product_count}")

        # 2. Migrate RevenueRecord FKs
        print("\nMigrating RevenueRecord listing_id FKs...")
        rev_count = db.query(RevenueRecord).filter(
            RevenueRecord.listing_id.is_(None),
            RevenueRecord.product_id.isnot(None)
        ).count()
        print(f"  Found {rev_count} revenue records to update.")

        for rev in db.query(RevenueRecord).filter(
            RevenueRecord.listing_id.is_(None),
            RevenueRecord.product_id.isnot(None)
        ).all():
            rev.listing_id = rev.product_id  # Same ID preserved
        db.commit()

        # 3. Migrate ProductPublishing FKs
        print("\nMigrating ProductPublishing listing_id FKs...")
        pub_count = db.query(ProductPublishing).filter(
            ProductPublishing.listing_id.is_(None),
            ProductPublishing.product_id.isnot(None)
        ).count()
        print(f"  Found {pub_count} publishing records to update.")

        for pub in db.query(ProductPublishing).filter(
            ProductPublishing.listing_id.is_(None),
            ProductPublishing.product_id.isnot(None)
        ).all():
            pub.listing_id = pub.product_id
        db.commit()

        # 4. Migrate Campaign listing_id
        print("\nMigrating Campaign listing_id FKs...")
        camp_count = db.query(Campaign).filter(
            Campaign.listing_id.is_(None),
            Campaign.related_product_ids.isnot(None)
        ).count()
        print(f"  Found {camp_count} campaigns with related_product_ids.")

        for camp in db.query(Campaign).filter(
            Campaign.listing_id.is_(None),
            Campaign.related_product_ids.isnot(None)
        ).all():
            related = camp.related_product_ids
            if isinstance(related, list) and related:
                camp.listing_id = related[0]  # Use first product as primary
        db.commit()

        # 5. Migrate License listing_id
        print("\nMigrating License listing_id FKs...")
        lic_count = db.query(License).filter(
            License.listing_id.is_(None),
            License.work_id.isnot(None)
        ).count()
        print(f"  Found {lic_count} licenses to potentially update.")
        # Licenses link to work_id already; listing_id can be set later manually

        # 6. Migrate Order listing_id
        print("\nMigrating Order listing_id FKs...")
        ord_count = db.query(Order).filter(
            Order.listing_id.is_(None),
            Order.product_id.isnot(None)
        ).count()
        print(f"  Found {ord_count} orders to update.")

        for order in db.query(Order).filter(
            Order.listing_id.is_(None),
            Order.product_id.isnot(None)
        ).all():
            order.listing_id = order.product_id
        db.commit()

        print("\n✅ All migrations complete.")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        db.close()


if __name__ == '__main__':
    migrate_products_to_listings()
