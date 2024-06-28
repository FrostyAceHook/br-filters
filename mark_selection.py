from pymclevel import alphaMaterials

displayName = "Mark Selection"

inputs = (
    ("Block:", alphaMaterials.Glowstone),
    ("Replaces the most-positive corner and the most-negative corner of the "
            "selection with the block above. Used to mark a selection so that "
            "in the future, this selection can easily be made by clicking these "
            "two blocks.", "label"),
)


def perform(level, box, options):
    bid, bdata = options["Block:"].ID, options["Block:"].blockData

    # Most-negative corner.
    level.setBlockAt(box.minx, box.miny, box.minz, bid)
    level.setBlockDataAt(box.minx, box.miny, box.minz, bdata)

    # Most-positive corner.
    level.setBlockAt(box.maxx - 1, box.maxy - 1, box.maxz - 1, bid)
    level.setBlockDataAt(box.maxx - 1, box.maxy - 1, box.maxz - 1, bdata)

    print "Finished marking selection."
    return
