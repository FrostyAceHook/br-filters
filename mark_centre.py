from itertools import product
from pymclevel import alphaMaterials


displayName = "Mark Centre"


inputs = (
    ("Replaces the very centre point of the selection with the block above. "
            "Used to quickly find the centre of something (shocking). If any "
            "dimension is even in length, two blocks are placed along that "
            "direction.", "label"),
    ("Block:", alphaMaterials.Glowstone),
)


def perform(level, box, options):
    bid, bdata = options["Block:"].ID, options["Block:"].blockData

    # Find the floored middle.
    x = box.minx + box.width /2
    z = box.minz + box.length/2
    y = box.miny + box.height/2

    # Find the actual middles.
    X = [x] if (box.width  % 2) else [x - 1, x]
    Z = [z] if (box.length % 2) else [z - 1, z]
    Y = [y] if (box.height % 2) else [y - 1, y]

    # Mark the centre.
    for cx, cz, cy in product(X, Z, Y):
        level.setBlockAt(cx, cy, cz, bid)
        level.setBlockDataAt(cx, cy, cz, bdata)


    print "Finished marking centre."
    print "- block: ({}:{})".format(bid, bdata)
    return
