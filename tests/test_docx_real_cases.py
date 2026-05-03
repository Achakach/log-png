"""Test real docx parsing cases from test_document_v3.docx."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from putpnginword import parse_paragraphs, expand_abbreviations


class MockParagraph:
    def __init__(self, text):
        self.text = text


def test_v3_single_command():
    """Table 1 Row 0: display device with two devices."""
    paragraphs = [
        MockParagraph('<HUAWEI>display device'),
        MockParagraph('<TUC-TYB91G01HWLEFC303-CPLEF03>'),
        MockParagraph('<TUC-TYB91G01HWLEFC303-CPLEF04>'),
    ]
    blocks = parse_paragraphs(paragraphs)
    assert len(blocks) == 1
    assert blocks[0][0] == ['display device']
    assert blocks[0][1] == ['TUC-TYB91G01HWLEFC303-CPLEF03', 'TUC-TYB91G01HWLEFC303-CPLEF04']


def test_v3_nested_interface_shutdown():
    """Table 2 Row 0: Full nested interface block with shutdown/undo shutdown."""
    paragraphs = [
        MockParagraph('<HUAWEI>system-view'),
        MockParagraph('[~HUAWEI]interface GigabitEthernet0/0/29'),
        MockParagraph('[~HUAWEI-GigabitEthernet0/0/29]display this'),
        MockParagraph('[~HUAWEI-GigabitEthernet0/0/29]shutdown'),
        MockParagraph('[~HUAWEI-GigabitEthernet0/0/29]undo shutdown'),
        MockParagraph('[~HUAWEI-GigabitEthernet0/0/29]display this'),
        MockParagraph('[~HUAWEI-GigabitEthernet0/0/29]quit'),
        MockParagraph('[~HUAWEI]quit'),
        MockParagraph('<TUC-TYB91G01HWLEFC303-CPLEF03>'),
        MockParagraph('<TUC-TYB91G01HWLEFC303-CPLEF04>'),
    ]
    blocks = parse_paragraphs(paragraphs)
    assert len(blocks) == 1
    cmds, nodes = blocks[0]
    assert len(cmds) == 8  # system-view, interface, display this, shutdown, undo shutdown, display this, quit, quit
    assert 'system-view' in cmds
    assert 'shutdown' in cmds
    assert 'undo shutdown' in cmds
    assert nodes == ['TUC-TYB91G01HWLEFC303-CPLEF03', 'TUC-TYB91G01HWLEFC303-CPLEF04']


def test_v3_ospf_with_abbreviations():
    """Table 2 Row 1: OSPF config with sys, dis th, q abbreviations."""
    paragraphs = [
        MockParagraph('<HUAWEI>sys'),
        MockParagraph('[~HUAWEI]ospf 1'),
        MockParagraph('[~HUAWEI-ospf-1]dis th'),
        MockParagraph('[~HUAWEI-ospf-1]network 172.16.0.0 0.0.255.255 area 0'),
        MockParagraph('[~HUAWEI-ospf-1]silent-interface all'),
        MockParagraph('[~HUAWEI-ospf-1]undo silent-interface all'),
        MockParagraph('[~HUAWEI-ospf-1]q'),
        MockParagraph('[~HUAWEI]q'),
        MockParagraph('<TUC-TYB91G01HWLEFC303-CPLEF03>'),
    ]
    blocks = parse_paragraphs(paragraphs)
    assert len(blocks) == 1
    cmds, nodes = blocks[0]
    assert nodes == ['TUC-TYB91G01HWLEFC303-CPLEF03']

    # Test abbreviation expansion
    expanded = expand_abbreviations(cmds)
    assert expanded[0] == 'system-view'
    assert expanded[2] == 'display this'
    assert expanded[6] == 'quit'
    assert expanded[7] == 'quit'


def test_v3_multiple_display_in_system_view():
    """Table 2 Row 2: Multiple display commands in system view without interface."""
    paragraphs = [
        MockParagraph('<HUAWEI>system-view'),
        MockParagraph('[~HUAWEI]display current-configuration'),
        MockParagraph('[~HUAWEI]display ip routing-table'),
        MockParagraph('[~HUAWEI]display vlan'),
        MockParagraph('[~HUAWEI]display interface brief'),
        MockParagraph('[~HUAWEI]quit'),
        MockParagraph('<TUC-TYB91G01HWLEFC303-CPLEF03>'),
    ]
    blocks = parse_paragraphs(paragraphs)
    assert len(blocks) == 1
    cmds, nodes = blocks[0]
    assert len(cmds) == 6
    assert cmds[0] == 'system-view'
    assert cmds[-2] == 'display interface brief'
    assert cmds[-1] == 'quit'
    assert nodes == ['TUC-TYB91G01HWLEFC303-CPLEF03']


def test_v3_multiple_blocks_in_one_cell():
    """Table 3 Row 0: Multiple standalone commands after nested block."""
    paragraphs = [
        MockParagraph('<HUAWEI>system-view'),
        MockParagraph('[~HUAWEI]interface GigabitEthernet0/0/1'),
        MockParagraph('[~HUAWEI-GigabitEthernet0/0/1]display this'),
        MockParagraph('[~HUAWEI-GigabitEthernet0/0/1]quit'),
        MockParagraph('[~HUAWEI]quit'),
        MockParagraph('<TUC-TYB91G01HWLEFC303-CPLEF03>'),
        MockParagraph('<TUC-TYB91G01HWLEFC303-CPLEF04>'),
        MockParagraph('<HUAWEI>display device'),
        MockParagraph('<TUC-TYB91G01HWLEFC303-CPLEF03>'),
        MockParagraph('<TUC-TYB91G01HWLEFC303-CPLEF04>'),
        MockParagraph('<HUAWEI>display clock'),
        MockParagraph('<TUC-TYB91G01HWLEFC303-CPLEF03>'),
        MockParagraph('<TUC-TYB91G01HWLEFC303-CPLEF04>'),
    ]
    blocks = parse_paragraphs(paragraphs)
    assert len(blocks) == 3

    # Block 0: nested interface
    assert blocks[0][0][0] == 'system-view'
    assert blocks[0][0][-1] == 'quit'
    assert blocks[0][1] == ['TUC-TYB91G01HWLEFC303-CPLEF03', 'TUC-TYB91G01HWLEFC303-CPLEF04']

    # Block 1: display device
    assert blocks[1][0] == ['display device']
    assert blocks[1][1] == ['TUC-TYB91G01HWLEFC303-CPLEF03', 'TUC-TYB91G01HWLEFC303-CPLEF04']

    # Block 2: display clock
    assert blocks[2][0] == ['display clock']
    assert blocks[2][1] == ['TUC-TYB91G01HWLEFC303-CPLEF03', 'TUC-TYB91G01HWLEFC303-CPLEF04']


def test_v3_set_cpu_and_version():
    """Table 3 Row 1: Nested set-cpu then standalone display version."""
    paragraphs = [
        MockParagraph('<HUAWEI>system-view'),
        MockParagraph('[HUAWEI]set cpu threshold 4'),
        MockParagraph('[HUAWEI]quit'),
        MockParagraph('<TUC-TYB91G01HWLEFC303-CPLEF03>'),
        MockParagraph('<TUC-TYB91G01HWLEFC303-CPLEF04>'),
        MockParagraph('<HUAWEI>display version'),
        MockParagraph('<TUC-TYB91G01HWLEFC303-CPLEF03>'),
    ]
    blocks = parse_paragraphs(paragraphs)
    assert len(blocks) == 2

    # Block 0: set-cpu nested
    assert blocks[0][0] == ['system-view', 'set cpu threshold 4', 'quit']
    assert blocks[0][1] == ['TUC-TYB91G01HWLEFC303-CPLEF03', 'TUC-TYB91G01HWLEFC303-CPLEF04']

    # Block 1: display version
    assert blocks[1][0] == ['display version']
    assert blocks[1][1] == ['TUC-TYB91G01HWLEFC303-CPLEF03']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
