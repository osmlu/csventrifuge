import csventrifuge


def test_load_rules_single_file():
    rules = csventrifuge.load_rules("luxembourg_addresses", ["rue"])
    assert "rue" in rules
    assert rules["rue"]["A la Croix Saint Pierre"].value == "À la Croix Saint-Pierre"
    assert rules["rue"]["A la Croix Saint Pierre"].count == 0


def test_load_enhancements_multiple_targets():
    keys = ["id_caclr_bat"]
    book, enhanced = csventrifuge.load_enhancements("luxembourg_addresses", keys)
    assert "id_caclr_bat" in book
    assert "rue" in book["id_caclr_bat"]
    assert book["id_caclr_bat"]["rue"]["79281"].value == "Rue des Jardins"
    assert book["id_caclr_bat"]["rue"]["79281"].count == 0
    assert "rue" in enhanced and "id_caclr_rue" in enhanced


def test_load_filters_simple():
    filters = csventrifuge.load_filters("luxembourg_addresses", ["id_geoportail"])
    assert "id_geoportail" in filters
    value = "005C00508003461_5126_15-17"
    assert filters["id_geoportail"][value].value == value
    assert filters["id_geoportail"][value].count == 0
