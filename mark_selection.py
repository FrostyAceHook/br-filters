from pymclevel import alphaMaterials


displayName = "Mark Selection"


inputs = (
    ("Block:", alphaMaterials.Glowstone),
    ("Place at:", ("two selected", "all corners")),
    ("Replaces some corners of the selection with 'block', to mark this "
            "selection so that in the future it can be easily made again by "
            "clicking the corners.", "label"),
)


def perform(level, box, options):
    bid, bdata = options["Block:"].ID, options["Block:"].blockData
    all_corners = (options["Place at:"] == "all corners")

    # Get them corners.
    if all_corners:
        corners = [
            (x, y, z)
            for x in (box.minx, box.maxx - 1)
            for y in (box.miny, box.maxy - 1)
            for z in (box.minz, box.maxz - 1)
        ]
    else:
        try:
            # Try do a little dodgy and access the "leaked" editor object to set
            # the genuine corners of the selection (i.e. the yellow and blue
            # blocks).
            corners = [
                editor.selectionTool.bottomLeftPoint,
                editor.selectionTool.topRightPoint,
            ]
        except UnboundLocalError:
            # Otherwise just take the two extreme corners.
            corners = [
                box.origin,
                # The upper bound is the exclusive maximum, so move it back to
                # the block that's in the selection.
                tuple(c - 1 for c in box.maximum),
            ]

    # Set them corners.
    for x, y, z in corners:
        level.setBlockAt(x, y, z, bid)
        level.setBlockDataAt(x, y, z, bdata)


    print "Finished marking selection."
    print "- block: ({}:{})".format(bid, bdata)
    print "- place at: {}".format(options["Place at:"])
    return
