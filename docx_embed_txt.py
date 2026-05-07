"""
Helper to embed .txt files as OLE objects inside a .docx package.

Since python-docx doesn't support arbitrary file embedding natively,
this module post-processes a saved .docx ZIP to:
1. Insert placeholder paragraphs (during python-docx generation)
2. After save, replace placeholders with w:object OLE references
3. Copy .txt files into word/embeddings/
4. Update [Content_Types].xml and document.xml.rels
"""
import os
import shutil
import zipfile
import tempfile
import uuid
from lxml import etree


_NSMAP = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
    'o': 'urn:schemas-microsoft-com:office:office',
    'v': 'urn:schemas-microsoft-com:vml',
    've': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
    'o14': 'http://schemas.microsoft.com/office/word/2010/wordml',
    'r14': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}


def _ns(tag):
    prefix, name = tag.split(':', 1)
    return '{%s}%s' % (_NSMAP[prefix], name)


def _make_generic_icon(txt_path, icon_path):
    """Create a simple 64x64 PNG icon with the filename text."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        # Fallback: create a minimal 1x1 transparent PNG
        import struct
        # Minimal PNG: 1x1 transparent
        png_data = (
            b'\x89PNG\r\n\x1a\n'
            + b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
            + b'\x00\x00\x00\nIDATx\x9cc\xfc\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N'
            + b'\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        with open(icon_path, 'wb') as f:
            f.write(png_data)
        return

    img = Image.new('RGBA', (64, 64), (240, 240, 240, 255))
    draw = ImageDraw.Draw(img)
    # Try to use a font, fallback to default
    try:
        font = ImageFont.truetype("arial.ttf", 10)
    except OSError:
        font = ImageFont.load_default()
    
    basename = os.path.basename(txt_path)
    # Draw filename (truncated if too long)
    text = basename[:20] + "..." if len(basename) > 20 else basename
    draw.text((4, 4), text, fill=(0, 0, 0, 255), font=font)
    draw.rectangle([2, 2, 62, 62], outline=(100, 100, 100, 255), width=2)
    img.save(icon_path)


def embed_txt_in_docx(docx_path, marker_txt_pairs):
    """
    Post-process a .docx to replace marker paragraphs with embedded .txt OLE objects.

    Parameters
    ----------
    docx_path : str
        Path to the .docx file produced by python-docx.
    marker_txt_pairs : list of (str, str)
        Each tuple is (marker_text, txt_file_path).
        The marker_text is a unique string previously inserted in a paragraph.
        The txt_file_path is the .txt to embed as an OLE object.

    Returns
    -------
    str
        The docx_path (modified in-place).
    """
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"DOCX not found: {docx_path}")
    if not marker_txt_pairs:
        return docx_path

    tmpdir = tempfile.mkdtemp(prefix='docx_embed_')
    try:
        # Extract
        with zipfile.ZipFile(docx_path, 'r') as zin:
            zin.extractall(tmpdir)

        word_dir = os.path.join(tmpdir, 'word')
        embed_dir = os.path.join(word_dir, 'embeddings')
        media_dir = os.path.join(word_dir, 'media')
        rels_dir = os.path.join(word_dir, '_rels')
        os.makedirs(embed_dir, exist_ok=True)
        os.makedirs(media_dir, exist_ok=True)
        os.makedirs(rels_dir, exist_ok=True)

        # ---- Update [Content_Types].xml ----
        ct_path = os.path.join(tmpdir, '[Content_Types].xml')
        ct_tree = etree.parse(ct_path)
        ct_root = ct_tree.getroot()
        ct_ns = 'http://schemas.openxmlformats.org/package/2006/content-types'

        # Ensure .txt default exists
        if not ct_root.findall(f'{{{ct_ns}}}Default[@Extension="txt"]'):
            etree.SubElement(
                ct_root, f'{{{ct_ns}}}Default',
                Extension='txt', ContentType='text/plain',
            )
        # Ensure .bin for OLE object
        if not ct_root.findall(f'{{{ct_ns}}}Default[@Extension="bin"]'):
            etree.SubElement(
                ct_root, f'{{{ct_ns}}}Default',
                Extension='bin',
                ContentType='application/vnd.openxmlformats-officedocument.oleObject',
            )
        ct_tree.write(ct_path, xml_declaration=True, encoding='UTF-8', standalone=True)

        # ---- Read / create document.xml.rels ----
        rels_path = os.path.join(rels_dir, 'document.xml.rels')
        if os.path.exists(rels_path):
            rels_tree = etree.parse(rels_path)
            rels_root = rels_tree.getroot()
        else:
            rels_root = etree.Element(
                'Relationships',
                nsmap={'': 'http://schemas.openxmlformats.org/package/2006/relationships'},
            )
            rels_tree = etree.ElementTree(rels_root)
        rels_ns = 'http://schemas.openxmlformats.org/package/2006/relationships'

        # Find next rId
        max_id = 0
        for rel in rels_root.findall(f'{{{rels_ns}}}Relationship'):
            rid = rel.get('Id', '')
            if rid.startswith('rId') and rid[3:].isdigit():
                max_id = max(max_id, int(rid[3:]))

        # ---- Process each marker ----
        doc_xml_path = os.path.join(word_dir, 'document.xml')
        doc_tree = etree.parse(doc_xml_path)
        doc_root = doc_tree.getroot()
        body = doc_root.find('.//{%s}body' % _NSMAP['w'])

        # Body namespace
        w_ns = _NSMAP['w']
        body_ns = '{%s}' % w_ns

        # Collect all paragraphs recursively (including inside tables)
        paragraphs = body.findall(f'.//{body_ns}p')

        for marker_text, txt_path in marker_txt_pairs:
            if not os.path.exists(txt_path):
                print(f"  Warning: .txt not found, skipping: {txt_path}")
                continue

            # Find paragraph containing marker
            target_para = None
            for para in paragraphs:
                para_text = ''.join(
                    t.text or '' for t in para.iter(f'{body_ns}t')
                )
                if marker_text in para_text:
                    target_para = para
                    break

            if target_para is None:
                print(f"  Warning: marker '{marker_text}' not found in document.xml")
                continue

            # Copy .txt to embeddings/
            safe_txt_name = os.path.basename(txt_path).replace(' ', '_')
            embed_txt_dst = os.path.join(embed_dir, safe_txt_name)
            shutil.copy2(txt_path, embed_txt_dst)

            # Generate a tiny icon
            safe_icon_name = f"icon_{uuid.uuid4().hex[:8]}.png"
            icon_path = os.path.join(media_dir, safe_icon_name)
            _make_generic_icon(txt_path, icon_path)

            # Add relationships
            max_id += 1
            rId_embed = f'rId{max_id}'
            etree.SubElement(
                rels_root, f'{{{rels_ns}}}Relationship',
                Id=rId_embed,
                Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/package',
                Target=f'embeddings/{safe_txt_name}',
            )

            max_id += 1
            rId_icon = f'rId{max_id}'
            etree.SubElement(
                rels_root, f'{{{rels_ns}}}Relationship',
                Id=rId_icon,
                Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/image',
                Target=f'media/{safe_icon_name}',
            )

            # Build minimal OLE object XML
            # We replace the ENTIRE marker paragraph with a new one containing w:object
            new_para = etree.Element(f'{{{w_ns}}}p')
            new_para.set(f'{{{_NSMAP["ve"]}}}Ignorable', 'w14 wp14')

            pPr = etree.SubElement(new_para, f'{{{w_ns}}}pPr')
            jc = etree.SubElement(pPr, f'{{{w_ns}}}jc')
            jc.set(f'{{{w_ns}}}val', 'left')

            # w:object with VML shape + OLE reference
            w_obj = etree.SubElement(new_para, f'{{{w_ns}}}object')

            # shapetype
            st_id = f'_x0000_t{uuid.uuid4().hex[:6]}'
            shapetype = etree.SubElement(
                w_obj, f'{{{_NSMAP["v"]}}}shapetype',
                {
                    'id': st_id,
                    'coordsize': '21600,21600',
                    f'{{{_NSMAP["o"]}}}spt': '75',
                    f'{{{_NSMAP["o"]}}}preferrelative': 't',
                    'path': 'm@7,l@8,m@5,21600l@6,21600e',
                },
                nsmap={'o': _NSMAP['o'], 'v': _NSMAP['v']},
            )
            stroke = etree.SubElement(shapetype, f'{{{_NSMAP["v"]}}}stroke')
            stroke.set('joinstyle', 'miter')
            formulas = etree.SubElement(shapetype, f'{{{_NSMAP["v"]}}}formulas')
            for eqn in ['sum #0 360 0', 'prod #0 2 1', 'sum 21600 0 #1',
                        'prod #0 2 1', 'sum 21600 0 #3',
                        'if #0 #4 0', 'if #0 0 #5',
                        'if #0 21600 0', 'if #0 0 21600',
                        'sum 0 0 @6', 'sum 21600 0 @7',
                        'if @8 21600 @9', 'if @8 0 @10',
                        'prod @11 2 1', 'prod @12 2 1',
                        'sum @13 0 21600', 'sum @14 0 21600',
                        'if @15 @16 0', 'if @15 0 @17']:
                f_elem = etree.SubElement(formulas, f'{{{_NSMAP["v"]}}}f')
                f_elem.set('eqn', eqn)
            handles = etree.SubElement(shapetype, f'{{{_NSMAP["v"]}}}handles')
            h = etree.SubElement(handles, f'{{{_NSMAP["v"]}}}h')
            h.set('position', '#0,bottomRight')
            h.set('xrange', '6629,14971')
            locks = etree.SubElement(shapetype, f'{{{_NSMAP["v"]}}}handles')
            locks.set('position', 'text')

            # shape (the icon visual)
            shape_id = f'_x0000_s{uuid.uuid4().hex[:8]}'
            shape = etree.SubElement(
                w_obj, f'{{{_NSMAP["v"]}}}shape',
                {
                    'id': shape_id,
                    'type': f'#{st_id}',
                    'style': 'position:absolute;margin-left:0;margin-top:0;width:32pt;height:32pt;z-index:1',
                    f'{{{_NSMAP["o"]}}}ole': '',
                },
                nsmap={'o': _NSMAP['o'], 'v': _NSMAP['v']},
            )
            fill = etree.SubElement(shape, f'{{{_NSMAP["v"]}}}fill')
            fill.set('type', 'frame')
            fill.set(f'{{{_NSMAP["r"]}}}id', rId_icon)

            # OLEObject
            ole = etree.SubElement(
                w_obj, f'{{{_NSMAP["o"]}}}OLEObject',
                {
                    'Type': 'Package',
                    'ProgID': 'Package',
                    'DrawAspect': 'Icon',
                    f'{{{_NSMAP["r"]}}}id': rId_embed,
                    'ShapeID': shape_id,
                },
                nsmap={'o': _NSMAP['o'], 'r': _NSMAP['r']},
            )

            # Replace target_para in the body with new_para
            target_para.getparent().replace(target_para, new_para)
            print(f"  Embedded OLE object for: {safe_txt_name}")

        # Write updated rels
        rels_tree.write(rels_path, xml_declaration=True, encoding='UTF-8', standalone=True)

        # Write updated document.xml
        doc_tree.write(doc_xml_path, xml_declaration=True, encoding='UTF-8', standalone=True)

        # Repackage ZIP
        os.remove(docx_path)
        with zipfile.ZipFile(docx_path, 'w', zipfile.ZIP_DEFLATED) as zout:
            for root, dirs, files in os.walk(tmpdir):
                for f in files:
                    full = os.path.join(root, f)
                    arc = os.path.relpath(full, tmpdir)
                    zout.write(full, arc)

        print(f"  Post-processed: {docx_path}")
        return docx_path

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 4:
        docx = sys.argv[1]
        marker = sys.argv[2]
        txt = sys.argv[3]
        embed_txt_in_docx(docx, [(marker, txt)])
    else:
        print("Usage: python docx_embed_txt.py <docx_path> <marker> <txt_path>")
