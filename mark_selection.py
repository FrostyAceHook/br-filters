from pymclevel import alphaMaterials

displayName = "Mark Selection"

inputs = (
    ("Block:", alphaMaterials.Glowstone),
    ("Replaces the two corners of the selection with 'block'. Used to mark a "
            "selection so that in the future, this selection can easily be made "
            "by clicking these two blocks.", "label"),
)


def perform(level, box, options):
    bid, bdata = options["Block:"].ID, options["Block:"].blockData

    try:
        # Try do a little dodgy and access the "leaked" editor object to set the
        # genuine corners of the selection (i.e. the yellow and blue blocks).
        x1, y1, z1 = editor.selectionTool.bottomLeftPoint
        x2, y2, z2 = editor.selectionTool.topRightPoint
    except Exception:
        # Otherwise just take the two extreme corners.
        x1, y1, z1 = box.origin
        x2, y2, z2 = box.maximum
        # The upper bound isn't included but we wanna place blocks in the
        # selection.
        x2, y2, z2 = x2 - 1, y2 - 1, z2 - 1

    # Set the two corners.
    level.setBlockAt(x1, y1, z1, bid)
    level.setBlockAt(x2, y2, z2, bid)
    level.setBlockDataAt(x1, y1, z1, bdata)
    level.setBlockDataAt(x2, y2, z2, bdata)

    print "Finished marking selection."
    return
