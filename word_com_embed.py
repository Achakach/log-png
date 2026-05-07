"""
Embed .txt files as OLE objects inside a .docx using Microsoft Word COM automation.

Replaces marker paragraphs (previously inserted by putpnginword.py) with true
Word embedded objects.  Double-clicking the icon in Word opens the full .txt.

Requires:
    - Microsoft Word installed (MS365 / Office 2016+)
    - pywin32 (pip install pywin32)
    - Windows OS
"""
import os
import sys


def embed_txt_via_word(docx_path, marker_txt_pairs):
    """
    Post-process a .docx by opening it in Word and replacing each marker
    paragraph with an embedded OLE object pointing to the corresponding .txt.

    Parameters
    ----------
    docx_path : str
        Absolute path to the .docx file.
    marker_txt_pairs : list of (str, str)
        Each tuple: (marker_text, txt_file_path).  marker_text is the
        UUID placeholder string that putpnginword.py inserted.

    Returns
    -------
    str
        docx_path (modified in-place).
    """
    if not marker_txt_pairs:
        return docx_path

    try:
        import win32com.client as win32
    except ImportError:
        print("ERROR: pywin32 not installed.  Run: pip install pywin32")
        sys.exit(1)

    word = win32.Dispatch("Word.Application")
    word.Visible = False          # headless
    word.DisplayAlerts = 0        # suppress all dialogs

    try:
        doc = word.Documents.Open(os.path.abspath(docx_path))

        for marker, txt_path in marker_txt_pairs:
            if not os.path.exists(txt_path):
                print(f"  Warning: .txt not found, skipping: {txt_path}")
                continue

            # Use a document Content range for searching
            rng = doc.Content
            find = rng.Find
            find.Text = marker
            find.Forward = True
            find.Wrap = 0               # 0 = wdFindStop
            find.Format = False
            find.MatchCase = False
            find.MatchWholeWord = False
            found = find.Execute()

            if not found:
                print(f"  Warning: marker '{marker}' not found in Word document")
                continue

            # rng is now redefined to the found marker text
            # Delete the marker text (leaves an empty range at that position)
            rng.Delete()

            # Collapse to start of the now-empty range
            rng.Collapse(Direction=1)  # 1 = wdCollapseStart

            # Insert OLE object at this exact position
            ole = doc.InlineShapes.AddOLEObject(
                ClassType="Package",
                FileName=os.path.abspath(txt_path),
                LinkToFile=False,
                DisplayAsIcon=True,
                IconFileName="",
                IconIndex=0,
                IconLabel=os.path.basename(txt_path),
                Range=rng,
            )

            print(f"  Embedded via Word COM: {os.path.basename(txt_path)}")

        doc.Save()
        doc.Close()
        return docx_path

    finally:
        word.Quit()


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 4:
        docx = sys.argv[1]
        marker = sys.argv[2]
        txt = sys.argv[3]
        embed_txt_via_word(docx, [(marker, txt)])
    else:
        print("Usage: python word_com_embed.py <docx_path> <marker> <txt_path>")
