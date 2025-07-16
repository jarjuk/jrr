import pytest
import os

from src import screen
from src.constants import COROS, APP_CONTEXT


def test_framework():
    assert 1 == 1

# ------------------------------------------------------------------
# Build screen


def test_screen_init():
    s = screen.Screen(size=(480, 320))
    assert len(s.screen_entries) == 0


def test_screen_text1():
    s = screen.Screen(size=(480, 320))
    txt1 = "text1"
    update_needed = s.add_or_update_entry(
        name=COROS.Screen.ENTRY_B1,
        entry_props={"text": txt1},
    )
    assert update_needed
    assert len(s.screen_entries) == 1
    update_needed = s.add_or_update_entry(
        name=COROS.Screen.ENTRY_B1,
        entry_props={"text": txt1},
    )
    assert not update_needed
    assert len(s.screen_entries) == 1


def test_screen_text1_changes():
    s = screen.Screen(size=(480, 320))
    txt1 = "text1"
    txt2 = "text2"
    update_needed = s.add_or_update_entry(
        name=COROS.Screen.ENTRY_B1,
        entry_props={"text": txt1},
    )
    assert update_needed
    assert len(s.screen_entries) == 1
    update_needed = s.add_or_update_entry(
        name=COROS.Screen.ENTRY_B1,
        entry_props={"text": txt2},
    )
    assert update_needed
    assert len(s.screen_entries) == 1


def test_screen_two_text1():
    s = screen.Screen(size=(480, 320))
    txt1 = "text1"
    txt2 = "text2"
    update_needed = s.add_or_update_entry(
        name=COROS.Screen.ENTRY_B1,
        entry_props={"text": txt1},
    )
    assert update_needed
    assert len(s.screen_entries) == 1
    update_needed = s.add_or_update_entry(
        name=COROS.Screen.ENTRY_B2,
        entry_props={"text": txt2},
    )
    assert update_needed
    assert len(s.screen_entries) == 2

# ------------------------------------------------------------------
# Build create image


def test_screen_txtlines_update_full():
    txt1 = "text1"
    txt2 = "text2"
    entries = [
        {"name": COROS.Screen.ENTRY_B1, "entry_props": {"text": txt1}},
        {"name": COROS.Screen.ENTRY_B2, "entry_props": {"text": txt2}},
    ]
    s = screen.Screen(size=(480, 320))
    for entry in entries:
        s.add_or_update_entry(**entry)
    assert len(s.screen_entries) == len(entries)
    img_file = os.path.join(os.path.dirname(__file__),
                            "../tmp/test_screen_full.png")
    s.img.save(img_file)


def test_screen_txtlines_icons_update_full():
    txt1 = "text1"
    txt2 = "text2"
    entries = [
        {"name": COROS.Screen.ENTRY_B1, "entry_props": {"text": txt1}},
        {"name": COROS.Screen.ENTRY_B2, "entry_props": {"text": txt2}},
        {"name": COROS.Screen.ENTRY_SPRITE_ICONS,
         "entry_props": {
             "imagepath": os.path.join(os.path.dirname(__file__), "../src/resources/icon-sprite.png"),
             "network": False,
             "streaming": True,
         }
         },
    ]
    s = screen.Screen(size=(480, 320))
    for entry in entries:
        s.add_or_update_entry(**entry)
    assert len(s.screen_entries) == len(entries)
    img_file = os.path.join(os.path.dirname(__file__),
                            "../tmp/test_screen_txtlines_icons_update_full.png")
    s.img.save(img_file)


def test_screen_update_all():
    txt1 = "text1"
    txt2 = "text2"
    txt3 = "text3"
    txt4 = "text4"
    entries = [
        {"name": COROS.Screen.ENTRY_B1, "entry_props": {"text": txt1}},
        {"name": COROS.Screen.ENTRY_B2, "entry_props": {"text": txt2}},
        {"name": COROS.Screen.ENTRY_B3, "entry_props": {"text": txt3}},
        {"name": COROS.Screen.ENTRY_B4, "entry_props": {"text": txt4}},
        {"name": COROS.Screen.ENTRY_MSG_L1, "entry_props": {"text": "line1"}},
        # {"name": COROS.Screen.ENTRY_MSG_L2, "entry_props": {"text": "line2"}},
        {"name": COROS.Screen.ENTRY_CLOCK, "entry_props": {"text": "12:01:15"}},
        {"name": COROS.Screen.ENTRY_SPRITE_ICONS,
         "entry_props": {
             "imagepath": os.path.join(os.path.dirname(__file__), "../src/resources/icon-sprite.png"),
             "network": False,
             "streaming": True,
         }},
        {"name": COROS.Screen.ENTRY_STREAM_ICON,
         "entry_props": {
             "imagepath": os.path.join(os.path.dirname(__file__), "../.icons/v2/classic.png"),
         }},
    ]
    s = screen.Screen(size=(480, 320))
    for entry in entries:
        s.add_or_update_entry(**entry)
    assert len(s.screen_entries) == len(entries)
    img_file = os.path.join(os.path.dirname(__file__),
                            "../tmp/test_screen_update_all.png")
    s.img.save(img_file)


def test_screen_update_partial():
    txt1 = "text1"
    txt2 = "text2"
    txt3 = "text3"
    txt4 = "text4"
    txt1_1 = {"name": COROS.Screen.ENTRY_B1,
              "entry_props": {"text": txt1 + "xxx"}}
    txt1_2 = {"name": COROS.Screen.ENTRY_B1,
              "entry_props": {"text": txt1 + "--"}}
    entry_clock1 = {"name": COROS.Screen.ENTRY_CLOCK,
                    "entry_props": {"text": "13:01:15"}}
    entry_clock2 = {"name": COROS.Screen.ENTRY_CLOCK,
                    "entry_props": {"text": "13:01:16"}}
    entry_sprite1 = {"name": COROS.Screen.ENTRY_SPRITE_ICONS,
                     "entry_props": {
                         "imagepath": os.path.join(os.path.dirname(__file__), "../src/resources/icon-sprite.png"),
                         "network": False,
                         "streaming": True,
                     }}
    entry_sprite2 = {"name": COROS.Screen.ENTRY_SPRITE_ICONS,
                     "entry_props": {
                         "imagepath": os.path.join(os.path.dirname(__file__), "../src/resources/icon-sprite.png"),
                         "network": True,
                         "streaming": False,
                     }}
    entry_stream_classic = {"name": COROS.Screen.ENTRY_STREAM_ICON,
                            "entry_props": {
                                "imagepath": os.path.join(os.path.dirname(__file__), "../.icons/v2/classic.png"),
                            }}
    entry_stream_jr = {"name": COROS.Screen.ENTRY_STREAM_ICON,
                       "entry_props": {
                           "imagepath": os.path.join(os.path.dirname(__file__), "../.icons/v2/järviradio.png"),
                       }}
    entries = [
        txt1_1,
        {"name": COROS.Screen.ENTRY_B2, "entry_props": {"text": txt2}},
        {"name": COROS.Screen.ENTRY_B3, "entry_props": {"text": txt3}},
        {"name": COROS.Screen.ENTRY_B4, "entry_props": {"text": txt4}},
        {"name": COROS.Screen.ENTRY_MSG_L1, "entry_props": {"text": "line1"}},
        # {"name": COROS.Screen.ENTRY_MSG_L2, "entry_props": {"text": "line2"}},
        entry_clock1,
        entry_sprite1,
        entry_stream_classic,
    ]
    s = screen.Screen(size=(480, 320))
    for entry in entries:
        s.add_or_update_entry(**entry)
    assert len(s.screen_entries) == len(entries)
    img_file = os.path.join(os.path.dirname(__file__),
                            "../tmp/test_screen_update_partial-1.png")
    s.img.save(img_file)

    update_needed = s.add_or_update_entry(**entry_clock1)
    assert not update_needed
    update_needed = s.add_or_update_entry(**entry_clock2)
    assert update_needed

    update_needed = s.add_or_update_entry(**entry_sprite1)
    assert not update_needed
    update_needed = s.add_or_update_entry(**entry_sprite2)
    assert update_needed

    update_needed = s.add_or_update_entry(**entry_stream_classic)
    assert not update_needed
    update_needed = s.add_or_update_entry(**entry_stream_jr)
    assert update_needed

    update_needed = s.add_or_update_entry(**txt1_1)
    assert not update_needed
    update_needed = s.add_or_update_entry(**txt1_2)
    assert update_needed

    img_file = os.path.join(os.path.dirname(__file__),
                            "../tmp/test_screen_update_partial-2.png")
    s.update_partial(name=entry_clock2["name"])
    s.update_partial(name=entry_sprite2["name"])
    s.update_partial(name=entry_stream_jr["name"])
    s.update_partial(name=txt1_1["name"])
    s.img.save(img_file)

# ------------------------------------------------------------------
# Create screen entry container


def test_screen_entry_container():
    test_case = "entry_container"
    img_nro = 1

    # Base screeen
    txt1 = "TEXT1"
    txt2 = "text2"
    txt1_1 = {"name": COROS.Screen.ENTRY_B1,
              "entry_props": {"text": txt1 + "xxx"}}
    txt1_2 = {"name": COROS.Screen.ENTRY_B2,
              "entry_props": {"text": txt2}}

    entries = [
        txt1_1,
        txt1_2,
    ]
    s = screen.Screen(size=(480, 320))

    for entry in entries:
        s.add_or_update_entry(**entry)
    assert len(s.screen_entries) == 2

    s.img.save(os.path.join(os.path.dirname(__file__),
                            f"../tmp/{test_case}_ {img_nro}.png"))
    img_nro += 1

    # One container screen entry
    config_entry_name = COROS.Screen.ENTRY_CONFIG
    s.add_or_update_entry(name=config_entry_name, entry_props={})
    assert len(s.screen_entries) == 3

    config_entry = s.named_screen_entry(name=config_entry_name)
    assert config_entry.screen.size == screen.OVERLAY_SIZE
    assert isinstance(config_entry, screen.ScreenEntryContainer)
    # By default inits empty screen_entries
    assert len(config_entry.screen.screen_entries) == 2

    # Add directry to
    line1_txt = "Line 1 here"
    container_entry1 = {
        "name": config_entry_name,
        "entry_props": {
            "line1.text": line1_txt,
        }
    }
    print(f"before add: {config_entry=}")
    updated = s.add_or_update_entry(**container_entry1)
    print(f"after add: {config_entry=}")
    assert len(config_entry.screen.screen_entries) == 2
    assert updated

    # Second updte no change
    updated = s.add_or_update_entry(**container_entry1)
    assert len(config_entry.screen.screen_entries) == 2
    assert not updated

    # Create new entry
    container_entry2 = {
        "name": config_entry_name,
        "entry_props": {
            "line2.text": "text in line2.text"
        }
    }
    updated = s.add_or_update_entry(**container_entry2)
    assert len(config_entry.screen.screen_entries) == 2
    assert updated
    s.update_full()

    s.img.save(os.path.join(os.path.dirname(__file__),
                            f"../tmp/{test_case}_ {img_nro}.png"))
    img_nro += 1

    entry = s.named_screen_entry(name=f"{config_entry_name}")
    assert entry is not None

    entry = s.named_screen_entry(name=f"{config_entry_name}.xx")
    assert entry is None
    entry = s.named_screen_entry(name=f"{config_entry_name}.line1")
    assert entry is not None
    assert entry.text == line1_txt

    # Add data to container

    print(f"before image {img_nro}")
    s.update_full()
    s.img.save(os.path.join(os.path.dirname(__file__),
                            f"../tmp/{test_case}_ {img_nro}.png"))
    print(f"after image {img_nro}")
    img_nro += 1


def default_screen_6():
    txt1 = "text1"
    txt2 = "text2"
    txt3 = "text3"
    txt4 = "text4"
    entries = [
        {"name": COROS.Screen.ENTRY_B1, "entry_props": {"text": txt1}},
        {"name": COROS.Screen.ENTRY_B2, "entry_props": {"text": txt2}},
        {"name": COROS.Screen.ENTRY_MSG_L1, "entry_props": {"text": "line1"}},
        {"name": COROS.Screen.ENTRY_CLOCK, "entry_props": {"text": "12:01:15"}},
        {"name": COROS.Screen.ENTRY_SPRITE_ICONS,
         "entry_props": {
             "imagepath": os.path.join(os.path.dirname(__file__), "../src/resources/icon-sprite.png"),
             "network": False,
             "streaming": True,
         }},
        {"name": COROS.Screen.ENTRY_STREAM_ICON,
         "entry_props": {
             "imagepath": os.path.join(os.path.dirname(__file__), "../.icons/v2/classic.png"),
         }},
    ]
    s = screen.Screen(size=(480, 320))
    for entry in entries:
        s.add_or_update_entry(**entry)
    return s


def to_image_path(icon):
    icon_dir = os.path.join(os.path.dirname(__file__))
    return f"{icon_dir}/../.icons/v2/{icon}.png"


def test_screen_attribute_error():
    test_case = "attribute_error"
    test_nro = 1
    s = screen.Screen(size=(480, 320))
    with pytest.raises(AttributeError) as err:
        s.add_or_update_entry(COROS.Screen.ENTRY_B1, {"textxxx": test_case})
    assert "no attribute 'textxxx'" in str(err)
    with pytest.raises(AttributeError) as err:
        s.add_or_update_entry(COROS.Screen.ENTRY_CONFIG,
                              {"line1.xxx": test_case})
    assert "no attribute 'xxx'" in str(err)


def test_screen_update_streming():
    test_case = "update_streaming"
    test_nro = 1
    s = screen.Screen(size=(480, 320))
    s.add_or_update_entry(COROS.Screen.ENTRY_B1, {"text": test_case})
    s.add_or_update_entry(name=COROS.Screen.ENTRY_STREAM_ICON,
                          entry_props={"imagepath": to_image_path("classic")})
    updated = s.update_full()
    assert updated
    updated = s.add_or_update_entry(name=COROS.Screen.ENTRY_STREAM_ICON,
                                    entry_props={"imagepath": to_image_path("classic")})
    assert not updated


def test_screen_update_collection():
    test_case = "update_collection"
    test_nro = 1
    s = screen.Screen(size=(480, 320))
    s.add_or_update_entry(COROS.Screen.ENTRY_B1, {"text": test_case})
    updated = s.add_or_update_entry(COROS.Screen.ENTRY_CONFIG,
                                    {
                                        "line1.text": "initvalue",
                                        # "active": False
                                    })
    assert updated
    # s.activate_entry(COROS.Screen.ENTRY_CONFIG, True)
    container = s.named_screen_entry(COROS.Screen.ENTRY_CONFIG)
    assert isinstance(container, screen.ScreenEntryContainer)
    assert container.active

    # No change in container
    updated = s.add_or_update_entry(COROS.Screen.ENTRY_CONFIG,
                                    {
                                        "line1.text": "initvalue",
                                        # "active": False
                                    })
    assert not updated

    updated = s.add_or_update_entry(COROS.Screen.ENTRY_CONFIG,
                                    {
                                        "line1.text": "changed-value",
                                        # "active": False
                                    })
    assert updated

    s.img.save(os.path.join(os.path.dirname(__file__),
                            f"../tmp/{test_case}-{test_nro}.png"))
    test_nro += 1


def test_screen_altenatives():
    test_case = "screen_alternatives"
    test_nro = 1

    s = screen.Screen(size=(480, 320))

    # Image 1 expect
    # - b1: screen_alternatives.1
    # - radio classing
    s.add_or_update_entry(COROS.Screen.ENTRY_B1, {
                          "text": f"{test_case}.{test_nro}"})
    s.add_or_update_entry(name=COROS.Screen.ENTRY_STREAM_ICON,
                          entry_props={"imagepath": to_image_path("classic")})

    # expect to see radio classing
    assert len(s.screen_entries) == 2
    s.img.save(os.path.join(os.path.dirname(__file__),
                            f"../tmp/{test_case}-{test_nro}.png"))
    test_nro += 1

    # Image 2 expect
    # - b1: screen_alternatives.2
    # - init line2.text
    s.add_or_update_entry(COROS.Screen.ENTRY_B1, {
                          "text": f"{test_case}.{test_nro}"})
    updated = s.add_or_update_entry(
        COROS.Screen.ENTRY_CONFIG,
        {
            "line2.text": f"init-line2.text= {test_nro}"
        })
    assert updated

    s.update_full()
    s.img.save(os.path.join(os.path.dirname(__file__),
                            f"../tmp/{test_case}-{test_nro}.png"))
    test_nro += 1

    # Image 3 expect
    # - b1: screen_alternatives.2
    # - init line1.text
    # - init line2.text

    s.add_or_update_entry(COROS.Screen.ENTRY_B1, {
                          "text": f"{test_case}.{test_nro}"})
    updated = s.add_or_update_entry(
        COROS.Screen.ENTRY_CONFIG,
        {
            "line1.text": f"add-line1.text {test_nro}",
            "line2.text": f"upd-line2.text {test_nro}"
        })
    assert updated

    # Error config not updated
    container = s.named_screen_entry(COROS.Screen.ENTRY_CONFIG)
    container.cache_invalidate()
    s.invalidate_image_cache()

    s.update_full()
    s.img.save(os.path.join(os.path.dirname(__file__),
                            f"../tmp/{test_case}-{test_nro}.png"))
    test_nro += 1
    print(f"{s.screen_entries=}")
