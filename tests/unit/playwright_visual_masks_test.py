def test_clerk_hosted_ui_is_masked_in_visual_snapshots(pytestconfig):
    masks = pytestconfig.option.playwright_visual_snapshot_masks

    assert "[data-clerk-component]" in masks
    assert ".cl-rootBox" in masks
    assert 'iframe[src*="clerk"]' in masks
