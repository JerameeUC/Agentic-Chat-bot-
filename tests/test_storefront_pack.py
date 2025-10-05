def test_storefront_docs_present():
    import os
    assert os.path.exists('memory/rag/data/storefront/faqs/faq_general.md')
    assert os.path.exists('memory/rag/data/storefront/policies/parking_rules.md')
